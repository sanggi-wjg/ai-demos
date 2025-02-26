import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

llama = ChatOllama(model="deepseek-r1:14b", temparature=0)


def naver_news():
    urls = (
        "https://n.news.naver.com/mnews/article/050/0000079549",
        "https://n.news.naver.com/mnews/article/050/0000079544",
        "https://n.news.naver.com/mnews/article/015/0005030964",
    )

    loader = WebBaseLoader(
        web_paths=urls,
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer("article", attrs={"id": ["dic_area"]}),
        ),
    )
    docs = loader.load()

    template = """
# Instruction
당신은 경제 기사 요약의 전문가 입니다.

아래의 기사를 읽고, 다음 지침에 따라 요약해 주세요:
1. 전체 내용을 50단어 이내로 요약한 'summary' 필드를 작성해 주세요.
2. 핵심 내용을 간결하게 정리해서 'key_points' 필드에 작성해 주세요.
3. 각 key_points 내용은 한 문장으로, 20단어를 넘지 않도록 해주세요.
4. 텍스트의 핵심 키워드와 관련된 단어나 개념을 10개 내외로 'tags' 필드에 추가해 주세요.
5. 전문 용어가 있다면 간단히 설명을 덧붙여 주세요.
6. 숫자나 통계가 있다면 반드시 포함시켜 주세요.
7. 요약은 객관적이고 중립적인 톤을 유지해 주세요.

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

# Input
{article}

위 지침에 따라 JSON 형식으로 요약해 주세요.
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
