import os

from dotenv import load_dotenv
from langchain.embeddings import CacheBackedEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain.storage import LocalFileStore
from langchain_chroma.vectorstores import Chroma
from langchain_community.document_loaders import ConfluenceLoader
from langchain_community.document_loaders.confluence import ContentFormat
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_groq import ChatGroq
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_demos.utils.decorators import caching
from langchain_demos.utils.dev import green

load_dotenv()
# set_verbose(True)
# set_debug(False)

JIRA_SPACE_PO = os.getenv("JIRA_SPACE_PO")
JIRA_SPACE_DEV = os.getenv("JIRA_SPACE_DEV")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_URL = os.getenv("JIRA_API_URL")
JIRA_API_KEY = os.getenv("JIRA_API_KEY")
JIRA_CONFLUENCE_API_URL = f"{JIRA_API_URL}/wiki"


@caching("./docs.bot.pkl")
def load_documents() -> list[Document]:
    recursive_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
        separators=["\n\n"],
    )

    confluence_loader = ConfluenceLoader(
        url=JIRA_CONFLUENCE_API_URL,
        api_key=JIRA_API_KEY,
        username=JIRA_USERNAME,
        space_key=JIRA_SPACE_PO,
        content_format=ContentFormat.STORAGE,
        limit=10,
        max_pages=1000,
        keep_markdown_format=False,
        keep_newlines=False,
    )
    confluence_docs = recursive_text_splitter.split_documents(
        [doc for doc in confluence_loader.load() if doc.page_content != ""]
    )
    return confluence_docs


def get_vector_db() -> Chroma:
    chroma_path = ".vector.bot"
    store_path = LocalFileStore(".store.bot")

    # embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    embeddings = OllamaEmbeddings(model="bge-m3:latest")
    cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings=embeddings,
        document_embedding_cache=store_path,
        namespace=embeddings.model,
    )

    if not os.path.exists(chroma_path):
        db = Chroma.from_documents(
            documents=load_documents(),
            embedding=cached_embeddings,
            persist_directory=chroma_path,
        )
    else:
        db = Chroma(
            embedding_function=cached_embeddings,
            persist_directory=chroma_path,
        )
    return db


def get_retriever() -> EnsembleRetriever:
    vector_db = get_vector_db()

    bm25_retriever = BM25Retriever.from_documents(
        load_documents(),
        search_kwargs={
            "k": 10,
        },
    )
    vector_retriever = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 10,
            "fetch_k": 20,  # MMR 초기 후보군 크기
            "lambda_mult": 0.7,  # 다양성, 관련성 사이의 균형 조정 (0.5-0.8 범위 추천)
            "score_threshold": 0.8,  # 유사도 점수가 0.8 이상인 문서만 반환
            # "filter": {"metadata_field": "desired_value"},  # 메타 데이터 기반 필터링
        },
    )
    return EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.5, 0.5],
    )


llm = ChatOllama(model="llama3.1", temparature=0)
# llm = ChatGroq(
#     model="llama-3.1-70b-versatile",
#     temperature=0,
#     max_tokens=None,
#     max_retries=2,
#     timeout=None,
# )
retriever = get_retriever()

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
# Instruction:
당신은 핏펫 회사 직원들을 위한 내부 문서와 정책을 잘 이해하고 있는 도우미 입니다.
Documents들을 기반으로 주어진 질문에 대해 정확하고 상세한 답변과 정보에 대한 출처도 같이 알려주세요. 
만약 모르는 정보라면 `모르는 정보 입니다.`라고 답변해주세요.
PLEASE ENSURE THAT ALL ANSWERS ARE KOREAN!

# Documents: 
{documents_context}""".strip(),
        ),
        ("human", "# Question: {question}"),
    ]
)
chain = {"documents_context": retriever, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()

while True:
    user_input = input("\n유저 입력: ")

    for found in retriever.invoke(user_input):
        green(found.page_content)

    for token in chain.stream(user_input):
        print(token, end="", flush=True)
