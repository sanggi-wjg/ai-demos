import os

from langchain_community.chat_models import ChatOllama
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

llama = ChatOllama(model="llama3.1", temparature=0)

pdf_filepath = os.path.join("../data", "SK_ESG_2023.pdf")
# pdf_filepath = os.path.join("../data", "정유화학에너지.pdf")

loader = PyPDFLoader(pdf_filepath)
pages = loader.load()
pdf_content = "\n".join([page.page_content for page in pages])


template = """
# Instruction
이 PDF 문서의 전체 내용을 A4 한 장 분량으로 요약해 주세요. 
다음 지침을 따라 요약해 주세요:

1. **요약의 길이**: A4 한 장(약 500-600 단어) 분량으로 작성해 주세요.
2. **요약의 구조**: 
   - **도입**: 문서의 목적과 주요 주제를 간략히 설명해 주세요.
   - **주요 내용**: 문서의 각 주요 섹션을 포함해 중요한 세부 사항과 논점을 정리해 주세요.
   - **결론 및 요점**: 문서의 결론과 주요 결과를 요약하고, 주요 포인트를 정리해 주세요.
3. **핵심 내용 강조**: 문서에서 가장 중요한 정보, 데이터, 또는 논쟁점을 명확히 제시해 주세요.
4. **어조 및 스타일**: 전문적이고 객관적인 어조로 작성해 주세요.
5. **목적**: 이 요약은 문서의 전체 내용을 빠르고 정확하게 파악할 수 있도록 하기 위해 사용될 것입니다.

# Input
{pdf_content}
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | llama | StrOutputParser()

for token in chain.stream({"pdf_content": pdf_content}):
    print(token, end="", flush=True)
