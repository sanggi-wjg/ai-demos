import os
import uuid

from dotenv import load_dotenv
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools import TavilySearchResults
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.tools import create_retriever_tool, Tool
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=20,
)
loader = WebBaseLoader(
    "https://docs.smith.langchain.com/overview",
    raise_for_status=True,
)
docs = loader.load_and_split(text_splitter)

embeddings = OllamaEmbeddings(model="mxbai-embed-large")
vector_db = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory=".vector.langsmith",
)
retriever = vector_db.as_retriever()

langsmith_docs_tool = create_retriever_tool(
    retriever,
    name="langsmith docs",
    description="Langsmith 문서입니다. Langsmith 관련 질문이라면 이 도구를 사용해주세요.",
)

search = TavilySearchResults(k=5)
search_tool = Tool(
    name="demo",
    func=search.invoke,
    description="정보가 더 필요하다면 이 웹 검색 도구를 사용해주세요.",
)

tools = [langsmith_docs_tool, search_tool]

template = """Answer the following questions as best you can. You have access to the following tools.
**답변은 꼭 한글로 해주세요!**

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
message_history = ChatMessageHistory()

llm = ChatOllama(model="llama3.1", temparature=0)

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)
agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor,
    lambda session_id: message_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)


user_input = input("\n유저 입력: ")

for token in agent_with_chat_history.stream(
    {"input": user_input},
    config={"configurable": {"session_id": f"{uuid.uuid4()}"}},
):
    print(token, end="", flush=True)
