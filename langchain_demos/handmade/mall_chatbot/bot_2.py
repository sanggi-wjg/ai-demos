import os
from typing import List

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

SUFFIX_PATH = "bot2"
DOCUMENTS_CACHE_PATH = f"./docs_{SUFFIX_PATH}.pkl"


def get_one_pager_documents_ids_in_confluence() -> List[str]:
    return [
        "107151658",
        "107282434",
        "158728193",
        "158662658",
        "158662720",
        "149127169",
        "158728317",
        "151519233",
        "145850369",
        "194871297",
        "204408489",
        "203915521",
        "203915433",
        "227409922",
        "193101949",
        "234291201",
        "204408559",
        "211550209",
        "166166529",
        "203915265",
        "203915349",
        "241172481",
        "239894529",
        "241795073",
        "241860609",
        "240123906",
        "210370561",
        "253067265",
        "253034730",
        "253034497",
        "235208705",
        "235143253",
        "253034630",
        "255262721",
    ]


@caching(DOCUMENTS_CACHE_PATH)
def load_documents() -> List[Document]:
    recursive_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
        separators=["\n\n"],
    )
    # space_key, page_ids 는 둘중에 하나만 작동함
    confluence_loader = ConfluenceLoader(
        url=JIRA_CONFLUENCE_API_URL,
        api_key=JIRA_API_KEY,
        username=JIRA_USERNAME,
        content_format=ContentFormat.STORAGE,
        limit=10,
        max_pages=1000,
        keep_markdown_format=False,
        keep_newlines=False,
        # space_key=JIRA_SPACE_PO,
        page_ids=get_one_pager_documents_ids_in_confluence(),
    )
    confluence_docs = recursive_text_splitter.split_documents(
        [doc for doc in confluence_loader.load() if doc.page_content != ""]
    )
    return confluence_docs


def get_vector_db() -> Chroma:
    chroma_path = f".vector.{SUFFIX_PATH}"
    store_path = LocalFileStore(f".store.{SUFFIX_PATH}")

    # embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    embeddings = OllamaEmbeddings(model="bge-m3")
    cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings=embeddings,
        document_embedding_cache=store_path,
        namespace=embeddings.model,
    )

    if not os.path.exists(DOCUMENTS_CACHE_PATH):
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
            "k": 3,
        },
    )
    vector_retriever = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 3,
            # "fetch_k": 5,  # MMR 초기 후보군 크기
            # "lambda_mult": 0.8,  # 다양성, 관련성 사이의 균형 조정 (0.5-0.8 범위 추천)
            # "score_threshold": 0.8,  # 유사도 점수가 0.8 이상인 문서만 반환
            # "filter": {"metadata_field": "desired_value"},  # 메타 데이터 기반 필터링
        },
    )
    return EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.5, 0.5],
    )


def main():
    llm = ChatOllama(
        # model="llama3.1",
        model="benedict/linkbricks-llama3.1-korean:8b",
        temparature=0,
    )
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
    당신은 핏펫 회사 직원들을 위한 내부 문서와 정책 정보에 대해서 주어진 질문에 정확하고 상세한 답변을 해주세요. 다음 지침을 따라 답변해주세요:
    - **반드시 Documents들을 기반으로 질문에 대해서 답변을 해야합니다.**
    - **모르는 정보라면 `모르는 정보 입니다.`라고 답변 해주세요.** 
    - 전체 내용을 50단어 이내로 요약한 '요약' 필드를 작성해 주세요.
    - 핵심 내용들을 간결하게 정리해서 '키 포인트' 필드에 작성해 주세요.
    - 정보를 확인한 출처를 `출처` 필드를 작성해 주세요.
    - 모든 답변은 한글이어야 합니다.
    - 요약은 객관적이고 중립성을 유지해주세요.
    
    응답은 반드시 아래 형식을 따라 주세요:
    요약: "전체 내용 요약 (50단어 이내)"
    키 포인트:
      - "핵심 포인트 1" 
      - "핵심 포인트 2"
      - "핵심 포인트 3"
      ...
    출처:
      - "출처 1"
      - "출처 2"
      - ...
     
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


if __name__ == "__main__":
    main()
