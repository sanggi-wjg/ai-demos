import os

from langchain_community.document_loaders import PDFPlumberLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

# pdf_filepath = os.path.join("../../../data", "SK_ESG_2023.pdf")
pdf_filepath = os.path.join("../../../data", "국회회의록_21대_410회_국정감사_여성가족위원회.PDF")
# loader = PDFMinerLoader(pdf_filepath)
loader = PDFPlumberLoader(pdf_filepath)


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=0,
    length_function=len,
    is_separator_regex=False,
)
docs = loader.load_and_split(text_splitter)

template = """
# Instruction
당신은 문서 요약을 도와주는 AI 입니다. 문서 내용을 A4 한 장 분량으로 요약해 주세요. 다음 지침을 따라 요약해 주세요:
1. A4 한 장 분량으로 작성해 주세요.
2. 요약의 구조: 
   - 도입: 문서의 목적과 주요 주제를 간략히 설명해 주세요.
   - 주요 내용: 문서의 각 주요 섹션을 포함해 중요한 세부 사항과 논점을 정리해 주세요.
   - 결론 및 요점: 문서의 결론과 주요 결과를 요약하고, 주요 포인트를 정리해 주세요.
3. 핵심 내용 강조: 문서에서 가장 중요한 정보, 데이터, 또는 논쟁점을 명확히 제시해 주세요.
4. 어조 및 스타일: 전문적이고 객관적인 어조로 작성해 주세요.

# 문서:
{pdf_content}

# 요약
"""
prompt = ChatPromptTemplate.from_template(template)

llm = ChatOllama(
    # model="benedict/linkbricks-llama3.1-korean:8b",
    model="exaone3.5:7.8b",
    temparature=0,
)
chain = prompt | llm | StrOutputParser()

for token in chain.stream({"pdf_content": "\n".join([doc.page_content for doc in docs])}):
    print(token, end="", flush=True)
