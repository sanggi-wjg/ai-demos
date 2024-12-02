import os
from typing import List

from dotenv import load_dotenv
from langchain_community.document_loaders import ConfluenceLoader
from langchain_community.document_loaders.confluence import ContentFormat
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()
# set_verbose(True)
# set_debug(False)

JIRA_SPACE_PO = os.getenv("JIRA_SPACE_PO")
JIRA_SPACE_DEV = os.getenv("JIRA_SPACE_DEV")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_URL = os.getenv("JIRA_API_URL")
JIRA_API_KEY = os.getenv("JIRA_API_KEY")
JIRA_CONFLUENCE_API_URL = f"{JIRA_API_URL}/wiki"

DOCUMENTS_CACHE_PATH = "./docs_bot_2.pkl"


def get_one_pager_documents_ids_in_confluence() -> List[str]:
    return [
        "241860609",
    ]


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
    # confluence_docs = recursive_text_splitter.split_documents(
    #     [doc for doc in confluence_loader.load() if doc.page_content != ""]
    # )
    return confluence_loader.load()


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

    prompt = ChatPromptTemplate.from_template(
        """
    # Instruction:
    당신은 회사 직원들을 위한 내부 문서와 정책을 잘 이해하고 있는 도우미 입니다. 
    
    주어진 질문에 대해 정확하고 상세한 답변을 해주는 역할을 가지고 있습니다. 다음 지침을 따라 답변해주세요:
    - 반드시 Documents들을 기반으로 질문에 대해서 답변을 해야합니다.
    - 전체 내용을 50단어 이내로 요약한 '요약' 필드를 작성해 주세요.
    - 핵심 내용들을 간결하게 정리해서 '키 포인트' 필드에 작성해 주세요.
    - 만약 모르는 정보라면 `모르는 정보 입니다.`라고 답변 해주세요. 
    - 모든 답변은 한글이어야 합니다.
    - 요약은 객관적이고 중립성을 유지해주세요.
    
    응답은 반드시 아래 형식을 따라 주세요:
    요약: "전체 내용 요약 (50단어 이내)"
    키 포인트:
      - "핵심 포인트 1" 
      - "핵심 포인트 2"
      - "핵심 포인트 3"
      ...
     
    # Documents: 
    {document_context}
    """.strip(),
    )
    # translate_prompt = ChatPromptTemplate.from_template("Translate '{text_to_translate}' to Korean.")

    analyze_chain = prompt | llm | StrOutputParser()
    # translate_chain = {"text_to_translate": analyze_chain} | translate_prompt | llm | StrOutputParser()

    for token in analyze_chain.stream({"document_context": load_documents()[0].page_content}):
        print(token, end="", flush=True)

    # while True:
    #     for token in chain.stream({"document_context": load_documents()[0].page_content}):
    #         print(token, end="", flush=True)


if __name__ == "__main__":
    main()
