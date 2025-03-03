from dotenv import load_dotenv
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.tools import TavilySearchResults
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_experimental.utilities import PythonREPL
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

load_dotenv()

repl = PythonREPL()
repl_tool = Tool(
    name="python_repl",
    description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
    func=repl.run,
)

search = TavilySearchResults(k=5)
search_tool = Tool(
    name="search_web",
    func=search.invoke,
    description="Use this to search web. You can get additional information.",
)
tools = [repl_tool, search_tool]

template = """Answer the following questions as best you can. You have access to the following tools.
    
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
    
    질문: {input}
    생각: {agent_scratchpad}"""
prompt = PromptTemplate.from_template(template)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite")

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)

chat_response = agent_executor.invoke({"input": input("유저 입력: ")})
print(chat_response)
