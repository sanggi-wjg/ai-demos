import os

from dotenv import load_dotenv
from langchain.embeddings import CacheBackedEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain.storage import LocalFileStore
from langchain_community.document_loaders import DirectoryLoader, ConfluenceLoader
from langchain_community.document_loaders.confluence import ContentFormat
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.globals import set_debug
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_demos.utils.dev import cyan, blue, green

load_dotenv()
# set_verbose(True)
set_debug(False)

JIRA_SPACE_PO = os.getenv("JIRA_SPACE_PO")
JIRA_SPACE_DEV = os.getenv("JIRA_SPACE_DEV")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_URL = os.getenv("JIRA_API_URL")
JIRA_API_KEY = os.getenv("JIRA_API_KEY")
JIRA_CONFLUENCE_API_URL = f"{JIRA_API_URL}/wiki"


def load_documents():
    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=30,
        length_function=len,
        is_separator_regex=False,
        separators=["\n\n"],
    )

    directory_loader = DirectoryLoader(
        path="./data",
        glob=["**/*.txt", "**/*.md"],
    )
    directory_extracts = directory_loader.load()
    directory_docs: list[Document] = recursive_splitter.split_documents(directory_extracts)

    # po_confluence_loader = ConfluenceLoader(
    #     url=JIRA_CONFLUENCE_API_URL,
    #     api_key=JIRA_API_KEY,
    #     username=JIRA_USERNAME,
    #     space_key=JIRA_SPACE_PO,
    #     content_format=ContentFormat.STORAGE,
    #     limit=10,
    #     max_pages=1000,
    #     keep_markdown_format=False,
    #     keep_newlines=False,
    # )
    # po_confluence_extracts = po_confluence_loader.lazy_load()
    # po_confluence_docs = recursive_splitter.split_documents(po_confluence_extracts)

    # dev_confluence_loader = ConfluenceLoader(
    #     url=JIRA_CONFLUENCE_API_URL,
    #     api_key=JIRA_API_KEY,
    #     username=JIRA_USERNAME,
    #     space_key=JIRA_SPACE_DEV,
    #     content_format=ContentFormat.STORAGE,
    #     limit=50,
    #     max_pages=1000,
    #     keep_markdown_format=False,
    #     keep_newlines=False,
    # )
    # dev_confluence_extracts = dev_confluence_loader.load()
    # dev_confluence_docs = recursive_splitter.split_documents(dev_confluence_extracts)

    # notion_db_loader = NotionDBLoader()
    return directory_docs


documents = load_documents()

embeddings = OllamaEmbeddings(model="mxbai-embed-large")
cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings=embeddings,
    document_embedding_cache=LocalFileStore(".store"),
    namespace=embeddings.model,
)

vector_db = Chroma.from_documents(
    documents=documents,
    embedding=cached_embeddings,
    persist_directory=".vector",
)
# a = db.search("브레이즈 PUSH 기준", search_type="mmr")
# b = db.similarity_search("브레이즈 PUSH 기준")

bm25_retriever = BM25Retriever.from_documents(documents, search_kwargs={"k": 4})
chroma_retriever = vector_db.as_retriever(search_type="mmr", search_kwargs={"k": 4})
ensemble_retriever = EnsembleRetriever(retrievers=[bm25_retriever, chroma_retriever], weights=[0.6, 0.4])
# a = ensemble_retriever.invoke("브레이즈 PUSH 기준")

llm = ChatOllama(model="llama3.1", temparature=0)
# llm = ChatOllama(model="phi3:medium", temperature=0)


template = """
당신은 핏펫몰 설계 및 정책에 대한 전문가 입니다. 
당신의 임무는 참고 정보를 기반으로 자세하면서 친절한 답변을 해주는 것입니다.
만약 주어진 정보로 답변이 어렵다면 `정보가 부족하여 답변이 어렵습니다.`로 답변 해주세요.

# 참고 정보:
{docs_context}

# 유저 질문:
{question}

# 답변:"""
prompt = PromptTemplate.from_template(template)
chain = {"docs_context": ensemble_retriever, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()

while True:
    user_input = input("\n유저 입력: ")

    bm25_search_docs = bm25_retriever.invoke(user_input)
    chroma_search_docs = chroma_retriever.invoke(user_input)
    ensemble_search_docs = ensemble_retriever.invoke(user_input)

    for doc in bm25_search_docs:
        cyan(f"BM25: {doc}")
    for doc in chroma_search_docs:
        blue(f"Chroma: {doc}")
    for doc in ensemble_search_docs:
        green(f"Ensemble: {doc}")

    for token in chain.stream(user_input):
        print(token, end="", flush=True)
