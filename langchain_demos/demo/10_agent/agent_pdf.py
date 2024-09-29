from langchain.agents import (
    create_react_agent,
    AgentExecutor,
)
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import create_retriever_tool
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def get_pdf_tool():
    loader = PyPDFLoader("../../data/SK_ESG_2023.pdf")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = loader.load_and_split(text_splitter)

    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    vector_db = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=".vector.agent_pdf",
    )
    retriever = vector_db.as_retriever()

    return create_retriever_tool(
        retriever,
        name="pdf_search",
        description="SK의 ESG 경영에 대한 정보는 PDF 문서에서 검색합니다. **'SK ESG'와 관련된 질문은 이 도구를 사용해야 합니다!**",
    )


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

tools = [
    # get_search_tool(),
    get_pdf_tool(),
]
llm = ChatOllama(model="llama3.1", temparature=0)

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

while True:
    user_input = input("유저 입력:")  # SK에서 ESG 경영을 위해서 어떤 것들을 하겠다는 건지? 목록으로 정리해줘.
    res = agent_executor.invoke({"input": user_input})
    print(res)
