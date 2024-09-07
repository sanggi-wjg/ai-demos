import bs4
from langchain.chains.summarize import load_summarize_chain
from langchain_community.chat_models import ChatOllama
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_text_splitters import CharacterTextSplitter

llama = ChatOllama(model="llama3.1", temparature=0)


def naver_news():
    url1 = "https://n.news.naver.com/mnews/article/015/0005030964"

    loader = WebBaseLoader(
        web_paths=(url1,),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer("article", attrs={"id": ["dic_area"]}),
        ),
    )
    docs = loader.load()

    template = """
    다음 기사를 한글로 요약 해주세요.
    {article}
    
    응답은 반드시 아래의 JSON 형식을 따라 주세요: 
    {{
        "summary": "전체 내용 요약 (50단어 이내)",
        "key_points": [
            "핵심 포인트 1 (20단어 이내)",
            "핵심 포인트 2 (20단어 이내)",
            "핵심 포인트 3 (20단어 이내)",
            "핵심 포인트 4 (20단어 이내)",
            "핵심 포인트 5 (20단어 이내)",
            ...
        ],
        "tags": ["태그1", "태그2", "태그3", ...]
    }}
    """

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llama | StrOutputParser()

    for doc in docs:
        for token in chain.stream({"article": doc.page_content}):
            print(token, end="", flush=True)


def tistory_articles():
    url1 = "https://sanggi-jayg.tistory.com/entry/%EB%A9%B1%EB%93%B1%EC%84%B1-Idempotence%EC%99%80-HTTP-API-%EC%84%A4%EA%B3%84"
    url2 = "https://sanggi-jayg.tistory.com/entry/Kotlin-Spring-Boot-%EC%97%90%EC%84%9C-data-class%EB%A5%BC-%ED%86%B5%ED%95%B8-Validation-%EB%A1%9C%EC%A7%81-%EC%9E%91%EC%84%B1%ED%95%98%EA%B8%B0"

    loader = WebBaseLoader(
        web_paths=(
            url1,
            url2,
        ),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer("div", attrs={"id": ["article"]}),
        ),
    )
    docs = loader.load()

    for doc in docs:
        print(doc.page_content.strip())
        print(doc.metadata)


# tistory_articles()
naver_news()
