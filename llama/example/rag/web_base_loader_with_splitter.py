import bs4
from langchain.chains.summarize import load_summarize_chain
from langchain_community.chat_models import ChatOllama
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import CharacterTextSplitter

llama = ChatOllama(model="llama3.1", temparature=0)


def naver_news():
    urls = (
        "https://n.news.naver.com/mnews/article/050/0000079549",
        # "https://n.news.naver.com/mnews/article/050/0000079544",
        # "https://n.news.naver.com/mnews/article/015/0005030964",
    )

    loader = WebBaseLoader(
        web_paths=urls,
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer("article", attrs={"id": ["dic_area"]}),
        ),
    )
    splitter = CharacterTextSplitter(
        separator="",
        chunk_size=1000,
        chunk_overlap=100,  # 접한 청크 사이에 중복으로 포함될 문자의 수
        length_function=len,
        is_separator_regex=False,
    )
    docs = loader.load_and_split(splitter)

    summary_prompt = PromptTemplate(
        template="""
        다음 내용을 요약해줘
        {text}
        """,
        input_variables=['text'],
    )
    combine_prompt = PromptTemplate(
        template="""
        다음 내용을 제목,서론,본론,결론에 따라 요약해줘
        {text}
        """,
        input_variables=['text'],
    )
    chain = load_summarize_chain(
        llama,
        map_prompt=summary_prompt,
        combine_prompt=combine_prompt,
        chain_type="map_reduce",
        verbose=False,
    )
    res = chain.run(docs)
    print(res)


naver_news()
