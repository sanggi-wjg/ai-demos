from typing import Literal

from dotenv import load_dotenv
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.tools import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_experimental.utilities import PythonREPL
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.constants import END, START
from langgraph.graph import MessagesState, StateGraph
from langgraph.types import Command
from pydantic import BaseModel, Field

load_dotenv()

search_tool = TavilySearchResults(max_results=3)
repl = PythonREPL()  # pip install -U matplotlib


# @tool
# def python_repl_tool(
#     code: Annotated[str, "The python code to execute to generate your chart."],
# ):
#     """Use this to execute python code. If you want to see the output of a value,
#     you should print it out with `print(...)`. This is visible to the user."""
#     try:
#         result = repl.run(code)
#     except BaseException as e:
#         return f"Failed to execute. Error: {repr(e)}"
#     result_str = f"Successfully executed: {code}\nStdout: {result}"
#     return result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER."

python_repl_tool = Tool(
    name="python_repl",
    description=(
        "A Python shell. Use this to execute python commands. Input should be a valid python command. "
        "If you want to see the output of a value, you should print it out with `print(...)`."
    ),
    func=repl.run,
)


def make_system_prompt(suffix: str) -> str:
    return (
        "You are a helpful AI assistant, collaborating with other assistants."
        " Use the provided tools to progress towards answering the question."
        " If you are unable to fully answer, that's OK, another assistant with different tools "
        " will help where you left off. Execute what you can to make progress."
        " If you or any of the other assistants have the final answer or deliverable,"
        " prefix your response with FINAL ANSWER so the team knows to stop."
        f"\n{suffix}"
    )


def make_prompt() -> str:
    return """
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
Thought:{agent_scratchpad}""".strip()


# llm = ChatOllama(model="qwen2.5:32b-instruct-q4_0")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

research_prompt = PromptTemplate.from_template(
    make_system_prompt("You can only do research. You are working with a chart generator colleague.") + make_prompt()
)
chart_prompt = PromptTemplate.from_template(
    make_system_prompt("You can only generate charts. You are working with a researcher colleague.") + make_prompt()
)

research_agent = AgentExecutor(
    agent=create_react_agent(llm, [search_tool, python_repl_tool], research_prompt),
    tools=[search_tool],
    verbose=True,
    handle_parsing_errors=True,
)
chart_agent = AgentExecutor(
    agent=create_react_agent(llm, [python_repl_tool], chart_prompt),
    tools=[python_repl_tool],
    verbose=True,
    handle_parsing_errors=True,
)


# def router(last_message: str, goto: str):
#     if "Final Answer" in last_message:
#         return END
#     return goto


def research_node(state: MessagesState) -> Command[Literal["chart"]]:
    chat_response = research_agent.invoke({"input": state["messages"][-1].content})
    breakpoint()
    output = chat_response["output"]
    return Command(
        goto="chart",
        update={"messages": state["messages"] + [HumanMessage(content=output, name="research")]},
    )


def chart_node(state: MessagesState) -> Command[Literal[END]]:
    breakpoint()
    chat_response = chart_agent.invoke({"input": state})
    breakpoint()
    output = chat_response["output"]

    return Command(
        goto=END,
        update={"messages": state["messages"] + [HumanMessage(content=output, name="chart")]},
    )


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
    {"recursion_limit": 5},
)
for event in events:
    for name, e in event.items():
        e["messages"][-1].pretty_print()
