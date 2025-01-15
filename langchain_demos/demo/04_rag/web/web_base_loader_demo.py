import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama

loader = WebBaseLoader(
    web_paths=("https://a16z.com/big-ideas-in-tech-2024/",),
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            # "article", attrs={"id": ["single-blog-post"]}
            class_=("content-col",),
        ),
    ),
)
docs = loader.load()

prompt = PromptTemplate.from_template(
    """
    문서 전체 내용을 A4 한 장 분량으로 요약해 주세요. 반드시 답변 내용은 한글로 해주세요.
    
    ---
    {text}
    ---
    """
)

llm = ChatOllama(model="exaone3.5:7.8b", temparature=0)
chain = prompt | llm | StrOutputParser()

for token in chain.stream({"text": "\n".join([doc.page_content for doc in docs])}):
    print(token, end="", flush=True)
