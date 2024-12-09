import os
from typing import List

import logging

import bs4
from dotenv import load_dotenv
from langchain.embeddings import CacheBackedEmbeddings
from langchain.globals import set_debug
from langchain.retrievers import EnsembleRetriever
from langchain.storage import LocalFileStore
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.vectorstores import VectorStore
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_demos.cookbook.naver_openapi_client import NaverOpenAPIClient
from langchain_demos.utils.cache_loader import RedisCacheLoader
from langchain_demos.utils.decorators import cacheable

load_dotenv()
set_debug(True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


@cacheable(cache_loader=RedisCacheLoader)
def get_news_urls_by_keyword(
    keyword: str,
    display: int = 10,
    start: int = 1,
    sort: str = "date",
) -> List[str]:
    logger.debug("get_news_urls_by_keyword...")
    client = NaverOpenAPIClient(
        client_id=os.getenv("NAVER_OPEN_API_CLIENT_ID"),
        client_secret=os.getenv("NAVER_OPEN_API_CLIENT_SECRET"),
    )
    urls = client.get_news_urls(
        query=keyword,
        display=display,
        start=start,
        sort=sort,
    )
    urls = list(filter(lambda x: "https://n.news.naver.com" in x, urls))
    logger.debug(urls)
    return urls


def load_documents(urls: List[str]) -> List[Document]:
    logger.debug("load_documents...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=0,
        add_start_index=True,
        length_function=len,
        is_separator_regex=False,
        separators=["\n", "\n\n"],
    )
    loader = WebBaseLoader(
        web_paths=urls,
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer("div", attrs={"id": ["newsct_article"]}),
        ),
    )

    # def escape_content(text: str) -> str:
    #     return text.strip().replace("\t", "")

    # documents = []
    # for doc in loader.load():
    #     doc.page_content = escape_content(doc.page_content)
    #     documents.append(doc)

    # return text_splitter.split_documents(documents)
    return loader.load_and_split(text_splitter)


def create_vector_db(documents: List[Document]) -> Chroma:
    logger.debug("create_vector_db...")
    chroma_path = ".vector.summary"
    store_path = ".store.summary"

    embeddings = OllamaEmbeddings(model="bge-m3")
    cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings=embeddings,
        document_embedding_cache=LocalFileStore(store_path),
        namespace=embeddings.model,
    )
    return Chroma.from_documents(
        documents=documents,
        embedding=cached_embeddings,
        persist_directory=chroma_path,
    )


def create_retriever(vector_db: VectorStore, documents: List[Document]) -> EnsembleRetriever:
    logger.debug("create_retriever...")
    bm25_retriever = BM25Retriever.from_documents(
        documents=documents,
        search_kwargs={
            "k": 10,
        },
    )
    vector_retriever = vector_db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": 10,
            # "fetch_k": 20,  # MMR 초기 후보군 크기
            # "lambda_mult": 0.8,  # 다양성, 관련성 사이의 균형 조정 (0.5-0.8 범위 추천)
            "score_threshold": 0.8,  # 유사도 점수가 0.8 이상인 문서만 반환
            # "filter": {"metadata_field": "desired_value"},  # 메타 데이터 기반 필터링
        },
    )
    return EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.5, 0.5],
    )


def flatten_documents(documents: List[Document]):
    return "\n\n".join(doc.page_content for doc in documents)


def create_prompt_for_news() -> ChatPromptTemplate:
    template = """
나는 당신이 **뉴스 요약 전문가**로서 행동하기를 바랍니다. 나는 당신에게 뉴스 내용들을 제공할 것 입니다.   
당신은 아래 지침을 따라 요약 내용을 제공 하세요.
1. News에서만 제공된 정보를 기반으로 요약하세요. 외부의 추가 정보, 본인의 생각, 상식 등을 포함하지 마세요.
2. 내용은 객관적이고 중립적인 시각에서 작성하세요.
3. 뉴스에 언급된 숫자, 통계, 인용문 등 중요한 세부 정보를 반드시 포함하세요.
4. 주제와 관련 없는 세부 사항이나 부차적인 정보를 제거하고 핵심적인 내용을 간결하게 전달하세요.
5. 뉴스의 출처가 명확하지 않은 정보나 추측성 내용은 요약에 포함하지 마세요.

# 뉴스: 
{articles}

# 응답은 반드시 아래 형식을 따라 주세요:
요약: 전체 내용 요약 (50단어 이내)
내용: 전체 내용 요약 (200단어 이내) 
핵심 내용:
- 핵심 내용 1 (30단어 이내) (source)
- 핵심 내용 2 (30단어 이내) (source)
- 핵심 내용 3 (30단어 이내) (source)
- ...

# 질문:
{question}
    """.strip()
    return ChatPromptTemplate.from_template(template)


def app_main():
    keyword = input("찾고 싶은 뉴스 키워드:")

    new_urls = get_news_urls_by_keyword(keyword, display=20)
    documents = load_documents(new_urls)
    # documents_context = flatten_documents(documents)

    vector_db = create_vector_db(documents)
    retriever = create_retriever(vector_db, documents)

    llm = ChatOllama(
        model="llama3.1",
        # model="benedict/linkbricks-llama3.1-korean:8b",
        temparature=0,
    )
    prompt = create_prompt_for_news()
    # chain = (
    #     {"articles": retriever | flatten_documents, "question": RunnablePassthrough()}
    #     | prompt
    #     | llm
    #     | StrOutputParser()
    # )
    chain = {"articles": retriever, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()

    while True:
        user_input = input("\n뉴스 질문: ")
        for token in chain.stream(user_input):
            print(token, end="", flush=True)


if __name__ == '__main__':
    app_main()
