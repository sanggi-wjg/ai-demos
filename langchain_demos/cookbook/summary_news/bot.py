import os
from typing import Dict
from typing import List
from urllib.parse import urlencode

import bs4
import requests
import streamlit as st
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
from langchain_core.vectorstores import VectorStore
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter


class NaverOpenAPIClient:
    """
    https://developers.naver.com/docs/serviceapi/search/news/news.md#%EB%89%B4%EC%8A%A4

    client = NaverOpenAPIClient(
        client_id=os.getenv("NAVER_OPEN_API_CLIENT_ID"),
        client_secret=os.getenv("NAVER_OPEN_API_CLIENT_SECRET"),
    )
    news_urls = client.get_news_urls(
        query="계엄령",
        display=10,
    )
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        api_url: str = "https://openapi.naver.com",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = api_url

    @property
    def header(self) -> Dict[str, str]:
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

    def http_get(self, url: str) -> Dict:
        response = requests.get(url, headers=self.header)
        response.raise_for_status()
        return response.json()

    def request_news(
        self,
        query: str,
        display: int,
        start: int,
        sort: str,
    ) -> Dict:
        assert query != ""
        assert 10 <= display <= 100
        assert 1 <= start <= 100
        assert sort in ["sim", "date"]

        params = urlencode({"query": query, "display": display, "start": start, "sort": sort})
        url = f"{self.api_url}/v1/search/news.json?{params}"
        return self.http_get(url)

    def get_news_urls(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "date",
    ) -> List[str]:
        news_items = self.request_news(query, display, start, sort)
        return [item["link"] for item in news_items["items"]]


load_dotenv()
# set_debug(True)
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())


# @cacheable(cache_loader=RedisCacheLoader)
def get_news_urls_by_keyword(
    keyword: str,
    display: int = 10,
    start: int = 1,
    sort: str = "date",
) -> List[str]:
    # logger.debug("get_news_urls_by_keyword...")
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
    # logger.debug(urls)
    return urls


def load_documents(urls: List[str]) -> List[Document]:
    # logger.debug("load_documents...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=0,
        add_start_index=True,
        length_function=len,
        is_separator_regex=False,
        separators=["\n", "\n\n"],
    )
    naver_news_loader = WebBaseLoader(
        web_paths=list(filter(lambda x: "https://n.news.naver.com" in x, urls)),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer("div", attrs={"id": ["newsct_article"]}),
        ),
    )
    another_news_loader = WebBaseLoader(
        web_paths=list(filter(lambda x: "https://n.news.naver.com" not in x, urls)),
    )

    def escape_content(text: str) -> str:
        return text.strip().replace("\t", "").replace("\n", "")

    documents = []
    for doc in naver_news_loader.load() + another_news_loader.load():
        doc.page_content = escape_content(doc.page_content)
        documents.append(doc)

    return text_splitter.split_documents(documents)


def create_vector_db(documents: List[Document]) -> Chroma:
    # logger.debug("create_vector_db...")
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
    # logger.debug("create_retriever...")
    bm25_retriever = BM25Retriever.from_documents(
        documents=documents,
        search_kwargs={
            "k": 5,
        },
    )
    vector_retriever = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5},
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
요약: 전체 내용에 대한 주제 (50단어 이내)
내용: 내용 요약 (200단어 이내) 
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
    st.title("💬 Langchain News")

    form = st.form("my_form")
    keyword = form.text_input("검색 하고 싶은 뉴스 키워드 (ex, 계엄령):")
    user_input = form.text_input("검색한 뉴스에 대해서 궁금하신걸 질문해주세요 (ex, 계엄령이 코스피에 미친 영향):")
    submitted = form.form_submit_button("Submit")

    if keyword and user_input and submitted:
        print(keyword, " / ", user_input)
        new_urls = get_news_urls_by_keyword(keyword, display=20)
        documents = load_documents(new_urls)
        vector_db = create_vector_db(documents)
        retriever = create_retriever(vector_db, documents)

        llm = ChatOllama(
            model="exaone3.5:7.8b",
            temparature=0,
        )
        prompt = create_prompt_for_news()
        chain = {"articles": retriever, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()

        output = chain.invoke(user_input)
        st.write(output)


if __name__ == '__main__':
    app_main()
