import os
from typing import List

import bs4
from dotenv import load_dotenv
from langchain.embeddings import CacheBackedEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain.storage import LocalFileStore
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_demos.utils.cache_loader import LocalCacheLoader
from langchain_demos.utils.decorators import cacheable
from langchain_demos.utils.dev import green

DOCUMENT_CACHE_PATH = "coupdeta"
CHROMA_PATH = ".vector.coupdeta"
STORE_PATH = ".store.coupdeta"

load_dotenv()


@cacheable(DOCUMENT_CACHE_PATH, loader=LocalCacheLoader)
def load_documents() -> List[Document]:
    recursive_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=30,
        length_function=len,
        is_separator_regex=False,
        separators=["\n\n"],
    )
    loader = WebBaseLoader(
        web_paths=(
            "https://n.news.naver.com/mnews/article/050/0000082996",
            "https://n.news.naver.com/mnews/article/050/0000082989",
            "https://n.news.naver.com/mnews/article/014/0005277179",
            "https://n.news.naver.com/mnews/article/050/0000082998",
            "https://n.news.naver.com/mnews/article/050/0000082873",
            "https://n.news.naver.com/mnews/article/014/0005277164",
            "https://n.news.naver.com/mnews/article/014/0005277881",
        ),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer("article", attrs={"id": ["dic_area"]}),
        ),
    )
    return loader.load_and_split(recursive_text_splitter)


def get_vector_db() -> Chroma:
    embeddings = OllamaEmbeddings(
        # model="mxbai-embed-large"
        model="bge-m3",
    )
    cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings=embeddings,
        document_embedding_cache=LocalFileStore(STORE_PATH),
        namespace=embeddings.model,
    )

    if os.path.exists(DOCUMENT_CACHE_PATH):
        return Chroma(
            embedding_function=cached_embeddings,
            persist_directory=CHROMA_PATH,
        )
    return Chroma.from_documents(
        documents=load_documents(),
        embedding=cached_embeddings,
        persist_directory=CHROMA_PATH,
    )


def get_retriever() -> EnsembleRetriever:
    vector_db = get_vector_db()

    bm25_retriever = BM25Retriever.from_documents(
        load_documents(),
        search_kwargs={
            "k": 5,
        },
    )
    vector_retriever = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 5,
            # "fetch_k": 5,  # MMR 초기 후보군 크기
            # "lambda_mult": 0.8,  # 다양성, 관련성 사이의 균형 조정 (0.5-0.8 범위 추천)
            # "score_threshold": 0.8,  # 유사도 점수가 0.8 이상인 문서만 반환
            # "filter": {"metadata_field": "desired_value"},  # 메타 데이터 기반 필터링
        },
    )
    return EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.6, 0.4],
    )


def app_main():
    # llm = ChatOllama(
    #     # model="llama3.1",
    #     model="benedict/linkbricks-llama3.1-korean:8b",
    #     temparature=0,
    # )
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        # model="llama3-groq-70b-8192-tool-use-preview",
        temperature=0,
        max_tokens=None,
        max_retries=2,
        timeout=None,
    )
    retriever = get_retriever()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
# Instruction:
다음은 뉴스 데이터에서 추출한 텍스트입니다. 아래의 지침을 따라 요약하세요.
1. 텍스트에서만 제공된 정보를 기반으로 요약하세요. 외부의 추가 정보나 상식을 포함하지 마세요.
2. 내용은 객관적이고 중립적인 시각에서 작성하세요.
3. 뉴스에 언급된 숫자, 통계, 인용문 등 중요한 세부 정보를 반드시 포함하세요.
4. 주제와 관련 없는 세부 사항이나 부차적인 정보를 제거하고 핵심적인 내용을 간결하게 전달하세요.
5. 뉴스의 출처가 명확하지 않은 정보나 추측성 내용은 요약에 포함하지 마세요.

# News Article: 
{articles}

# Response Format:
"전체 내용 요약 (50단어 이내)"
- "핵심 내용 1 (20단어 이내)"
- "핵심 내용 2 (20단어 이내)"
- "핵심 내용 3 (20단어 이내)"
- ...
    """.strip(),
            ),
            ("human", "# Question: {question}"),
        ]
    )
    chain = {"articles": retriever, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()

    while True:
        user_input = input("\n유저 입력: ")

        for found in retriever.invoke(user_input):
            green(found.page_content)

        for token in chain.stream(user_input):
            print(token, end="", flush=True)


if __name__ == '__main__':
    app_main()
