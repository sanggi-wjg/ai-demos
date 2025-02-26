import os

from langchain_community.document_loaders import PDFMinerLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from langchain_demos.utils.dev import green

# pdf_filepath = os.path.join("../../../data", "SK_ESG_2023.pdf")
pdf_filepath = os.path.join("../../../data", "01-34-2-n1-9.pdf")
loader = PDFMinerLoader(pdf_filepath)
docs = loader.load()

# template = """
# # Instruction
# 이 PDF 문서의 전체 내용을 A4 한 장 분량으로 요약해 주세요. 다음 지침을 따라 요약해 주세요:
# 1. A4 한 장(약 500-600 단어) 분량으로 작성해 주세요.
# 2. 요약의 구조:
#    - 도입: 문서의 목적과 주요 주제를 간략히 설명해 주세요.
#    - 주요 내용: 문서의 각 주요 섹션을 포함해 중요한 세부 사항과 논점을 정리해 주세요.
#    - 결론 및 요점: 문서의 결론과 주요 결과를 요약하고, 주요 포인트를 정리해 주세요.
# 3. 핵심 내용 강조: 문서에서 가장 중요한 정보, 데이터, 또는 논쟁점을 명확히 제시해 주세요.
# 4. 어조 및 스타일: 전문적이고 객관적인 어조로 작성해 주세요.
# 5. 목적: 이 요약은 문서의 전체 내용을 빠르고 정확하게 파악할 수 있도록 하기 위해 사용될 것입니다.
#
# # PDF Document
# {pdf_content}
# """
# prompt = ChatPromptTemplate.from_template(template)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
As a professional information analyst, you provide accurate and reliable information about questions.
It analyzes related search results and generates answers based on them, and provides additional information through reasonable reasoning and analysis, if necessary.
Always respond with accuracy and reliability as the top priority.
""",
        ),
        ("human", "{pdf_content}"),
    ]
)

llm = ChatOllama(
    # model="benedict/linkbricks-llama3.1-korean:8b",
    # model="exaone3.5:7.8b",
    model="deepseek-r1:14b",
    temparature=0,
)
chain = prompt | llm | StrOutputParser()
result = ""

for token in chain.stream({"pdf_content": "\n".join([doc.page_content for doc in docs])}):
    print(token, end="", flush=True)
    result += token

exaone = ChatOllama(
    model="exaone3.5:7.8b",
    temparature=0,
)
translate_prompt = ChatPromptTemplate.from_template("Translate the following text to Korean: {text}")
translate_chain = translate_prompt | exaone | StrOutputParser()

for token in translate_chain.stream({"text": result}):
    green(token, end="", flush=True)
