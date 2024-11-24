import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

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
아래의 기사를 읽고, 다음 지침에 따라 요약해 주세요:
1. 전체 내용을 50단어 이내로 요약한 '제목' 필드를 작성해 주세요.
2. 핵심 내용을 간결하게 정리해서 '내용' 필드에 작성해 주세요.
3. 각 '내용'은 한 문장으로, 20단어를 넘지 않도록 해주세요.
4. 텍스트의 핵심 키워드와 관련된 단어나 개념을 10개 내외로 '태그' 필드에 추가해 주세요.
5. 전문 용어가 있다면 간단히 설명을 덧붙여 주세요.
6. 숫자나 통계가 있다면 반드시 포함시켜 주세요.
7. 요약은 객관적이고 중립적인 톤을 유지해 주세요.

반드시 아래 응답 형식을 따라 주세요: 
"제목": "전체 내용 요약 (50단어 이내)",
"내용": 
- "핵심 내용 1 (20단어 이내)",
- "핵심 내용 2 (20단어 이내)",
- "핵심 내용 3 (20단어 이내)",
- "핵심 내용 4 (20단어 이내)",
- ...
"태그": ["태그 1", "태그 2", "태그 3", ...]

# Article
{article}
""".strip()
prompt = ChatPromptTemplate.from_template(template)

llama = ChatOllama(
    # model="llama3.1",
    model="benedict/linkbricks-llama3.1-korean:8b",
    temparature=0,
)
chain = prompt | llama | StrOutputParser()

for doc in docs:
    for token in chain.stream({"article": doc.page_content}):
        print(token, end="", flush=True)
    print()
