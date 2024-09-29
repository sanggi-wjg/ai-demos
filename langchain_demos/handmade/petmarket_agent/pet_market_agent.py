import os

from dotenv import load_dotenv
from langchain.agents import (
    create_react_agent,
    AgentExecutor,
)
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import PDFMinerLoader
from langchain_community.tools import TavilySearchResults
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.tools import create_retriever_tool, Tool
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

embeddings = OllamaEmbeddings(model="mxbai-embed-large")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=50,
    length_function=len,
    is_separator_regex=False,
    separators=["\n\n"],
)


def get_web_search_tool():
    search = TavilySearchResults(k=5)
    return Tool(
        name="demo",
        func=search.invoke,
        description="실시간 웹 정보를 검색합니다. 실시간 반려동물 시장 분석에 대한 정보가 필요하다면 이 도구를 사용해주세요.",
    )


def get_pet_market_pdf_tool():
    docs = PDFMinerLoader("data/pet_market_2023.pdf").load_and_split(text_splitter)
    docs2 = PDFMinerLoader("data/pet_market_2024_2.pdf").load_and_split(text_splitter)

    vector_db = Chroma.from_documents(
        documents=docs + docs2,
        embedding=embeddings,
        persist_directory=".vector.pet_market_pdf",
    )
    retriever = vector_db.as_retriever()

    return create_retriever_tool(
        retriever,
        name="pdf_search",
        description="반려동물 시장에 대한 분석 리포트 입니다. 반려동물 시장 분석에 대한 전문가 의견이 필요하다면 이 도구를 사용해주세요.",
    )


def get_agent_executor():
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

    tools = [get_web_search_tool(), get_pet_market_pdf_tool()]
    llm = ChatOllama(model="llama3.1", temparature=0)

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
    )
    return agent_executor


message_history = ChatMessageHistory()
agent_with_chat_history = RunnableWithMessageHistory(
    get_agent_executor(),
    lambda session_id: message_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)


while True:
    user_input = input("유저 입력:")  # 미래의 펫 병원 시장에 대해서 분석해줘
    for token in agent_with_chat_history.stream(
        {"input": user_input},
        config={"configurable": {"session_id": "MyTestSessionID"}},
    ):
        print(token, end="", flush=True)
