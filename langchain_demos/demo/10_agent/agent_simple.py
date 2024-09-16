import os

from dotenv import load_dotenv
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_community.tools import TavilySearchResults
from langchain_ollama import ChatOllama

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


search = TavilySearchResults(k=5)

tavily_tool = Tool(
    name="demo",
    func=search.invoke,
    description="Tavily Search",
)


llm = ChatOllama(model="llama3.1", temparature=0)
tools = [tavily_tool]

agent_executor = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

resp = agent_executor.invoke({"input": "Fitpet의 회사 주소 정보 알려줘"})
print(resp)
