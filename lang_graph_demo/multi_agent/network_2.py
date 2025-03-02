from typing import Annotated, Literal

from dotenv import load_dotenv
from langchain.agents import create_react_agent
from langchain_community.tools import TavilySearchResults
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langchain_ollama import ChatOllama
from langgraph.constants import END, START
from langgraph.graph import MessagesState, StateGraph
from langgraph.types import Command

load_dotenv()


repl = PythonREPL()

"""
pip install -U langchain_community langchain_anthropic langchain_experimental matplotlib langgraph
"""


@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    result_str = f"Successfully executed: {code}\nStdout: {result}"
    return result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER."


def make_prompt(suffix: str) -> str:
    return (
        "You are a helpful AI assistant, collaborating with other assistants."
        " Use the provided tools to progress towards answering the question."
        " If you are unable to fully answer, that's OK, another assistant with different tools "
        " will help where you left off. Execute what you can to make progress."
        " If you or any of the other assistants have the final answer or deliverable,"
        " prefix your response with FINAL ANSWER so the team knows to stop."
        f"\n{suffix}"
    )


def make_prompt_2(role: str) -> str:
    return (
        role
        + """
You have access to the following tools: 

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}
    """.strip()
    )


def router(last_message: BaseMessage, goto: str):
    if "FINAL ANSWER" in last_message.content:
        # Any agent decided the work is done
        return END
    return goto


search_tool = TavilySearchResults(max_results=3)

llm = ChatOllama(model="qwen2.5:14b-instruct-q8_0")
research_agent = create_react_agent(
    llm,
    tools=[search_tool],
    prompt=PromptTemplate.from_template(
        make_prompt_2("You can only do research. You are working with a chart generator colleague.")
    ),
)

chart_agent = create_react_agent(
    llm,
    tools=[python_repl_tool],
    prompt=PromptTemplate.from_template(
        make_prompt_2("You can only generate charts. You are working with a researcher colleague.")
    ),
)


def research_node(state: MessagesState) -> Command[Literal["chart", END]]:
    chat_response = research_agent.invoke(state)
    goto = router(chat_response, "chart")

    chat_response["messages"][-1] = HumanMessage(content=chat_response.content, name="research")
    return Command(update={"messages": chat_response["messages"]}, goto=goto)


def chart_node(state: MessagesState) -> Command[Literal["research", END]]:
    chat_response = chart_agent.invoke(state)
    goto = router(chat_response, "research")

    chat_response["messages"][-1] = HumanMessage(content=chat_response.content, name="chart")
    return Command(update={"messages": chat_response["messages"]}, goto=goto)


workflow = StateGraph(MessagesState)
workflow.add_node("research", research_node)
workflow.add_node("chart", chart_node)

workflow.add_edge(START, "research")
graph = workflow.compile()

with open(f"network_02.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())

events = graph.stream(
    {
        "messages": [
            (
                "user",
                "First, get the UK's GDP over the past 5 years, then make a line chart of it. Once you make the chart, finish.",
            )
        ],
    },
    {"recursion_limit": 10},
)
for s in events:
    print(s)
    print("----")
