import enum
from typing import List

import streamlit as st
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.embeddings import CacheBackedEmbeddings
from langchain.globals import set_debug
from langchain.retrievers import EnsembleRetriever
from langchain.storage import LocalFileStore
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.vectorstores import VectorStore
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentMetadataCategoryEnum(enum.Enum):
    IT = "IT"
    HR = "HR"
    ETC = "ETC"


def load_documents() -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=0,
        add_start_index=True,
        length_function=len,
        is_separator_regex=False,
        separators=["\n\n"],
    )
    documents = [
        Document(
            page_content="""
회사의 복리후생 정책은 무엇인가요?
- 회사는 직원들을 위한 건강보험, 연간 보너스, 연차 휴가 정책을 제공합니다.
- 건강보험은 가족 구성원을 포함하며, 연간 보너스는 성과에 기반합니다. 연차 휴가는 15일에서 시작하여 근속 기간에 따라 증가합니다.
- 자세한 내용은 [사내 복리후생 가이드](https://company.intranet/benefits)를 참조하세요.
        """.strip(),
            metadata={
                "category": DocumentMetadataCategoryEnum.IT.value,
                "url": "https://company.intranet/benefits",
            },
        ),
        Document(
            page_content="""
사내 이메일 계정 설정은 어떻게 하나요?
- 사내 이메일 계정은 첫 출근일에 IT 지원팀에서 제공합니다.
- 초기 비밀번호로 로그인 후, 보안 강화를 위해 반드시 변경하세요.
- 이메일 클라이언트 설정이 필요한 경우 IT 지원팀에게 IMAP/SMTP 정보를 요청하세요.
- 자세한 내용은 [IT 지원 가이드](https://company.intranet/email-setup)를 참조하세요.
        """.strip(),
            metadata={
                "category": DocumentMetadataCategoryEnum.IT.value,
                "url": "https://company.intranet/email-setup",
            },
        ),
        Document(
            page_content="""
입사 후 IT 장비는 언제 받을 수 있나요?
- IT 장비는 입사 첫날 배포됩니다.
- 장비에 대한 문제가 발생할 경우, [IT 지원팀 연락처 및 FAQ](https://company.intranet/it-support)를 참조하세요.
        """.strip(),
            metadata={
                "category": DocumentMetadataCategoryEnum.IT.value,
                "url": "https://company.intranet/it-support",
            },
        ),
        Document(
            page_content="""
사내 VPN은 어떻게 사용하나요?
- VPN 연결은 사내 네트워크에 원격으로 접근하기 위해 필요합니다.
- VPN 클라이언트 앱을 다운로드하여 제공된 사용자 ID와 비밀번호로 로그인하세요.
- 설정 가이드 및 다운로드 링크는 [VPN 사용 매뉴얼](https://company.intranet/vpn-guide)을 참조하세요.
- 연결 문제가 발생하면 IT 지원팀에 문의하세요.
        """.strip(),
            metadata={
                "category": DocumentMetadataCategoryEnum.IT.value,
                "url": "https://company.intranet/vpn-guide",
            },
        ),
        Document(
            page_content="""
연차 휴가는 어떻게 신청하나요?
- 연차 신청은 사내 포털에서 “휴가 신청” 메뉴를 통해 가능합니다.
- 신청 시, 승인 절차는 상급자와 인사팀의 확인이 필요합니다.
- 연차 사용은 최소 3일 전에 신청해야 하며, 긴급 상황에서는 예외가 허용됩니다.
- 연차 잔여일 및 신청 상태는 [사내 포털 휴가 관리](https://company.intranet/vacation)에서 확인할 수 있습니다.
        """.strip(),
            metadata={
                "category": DocumentMetadataCategoryEnum.HR.value,
                "url": "https://company.intranet/vacation",
            },
        ),
        Document(
            page_content="""
급여 명세서를 어디서 확인할 수 있나요?
- 급여 명세서는 매월 25일 이후 사내 포털에서 확인 가능합니다.
- “인사 관리” 메뉴 아래 “급여 명세서” 탭을 클릭하여 최근 기록을 조회하세요.
- 오류가 있는 경우, 인사팀에 즉시 문의하세요.
- 자세한 안내는 [급여 관리 가이드](https://company.intranet/payroll-guide)를 참조하세요.
        """.strip(),
            metadata={
                "category": DocumentMetadataCategoryEnum.HR.value,
                "url": "https://company.intranet/payroll-guide",
            },
        ),
        Document(
            page_content="""
교육 및 직무 연수는 어떻게 신청하나요?
- 직무 연수 및 교육 프로그램은 사내 학습 포털에서 확인 가능합니다.
- “교육 신청” 메뉴에서 원하는 과정을 선택하고 신청 버튼을 클릭하세요.
- 신청 후, 관리자의 승인이 필요하며 승인 상태는 이메일로 알림이 발송됩니다.
- 교육 프로그램의 전체 목록은 [학습 포털](https://company.intranet/education)에서 확인하세요.
        """.strip(),
            metadata={
                "category": DocumentMetadataCategoryEnum.HR.value,
                "url": "https://company.intranet/education",
            },
        ),
        Document(
            page_content="""
사내 메신저는 어떻게 설치하나요?
- 사내 메신저는 PC와 모바일에서 모두 사용 가능합니다.
- [다운로드 페이지](https://company.intranet/messenger-download)에서 운영체제에 맞는 설치 파일을 다운로드하세요.
- 로그인 정보는 사내 이메일 계정과 동일합니다.
- 앱 설정 및 사용법은 [메신저 가이드](https://company.intranet/mail)를 참고하세요.
        """.strip(),
            metadata={
                "category": DocumentMetadataCategoryEnum.IT.value,
                "url": "https://company.intranet/messenger-download",
            },
        ),
        Document(
            page_content="""
식사 제공 정책은 어떻게 되나요?
- 사내 식당에서 점심 식사가 제공되며, 메뉴는 매주 월요일 업데이트됩니다.
- 특별한 식단이 필요한 경우, 사전에 HR 부서에 요청하세요.
- 야근 시 저녁 식사비는 회사에서 지원하며, 지정된 절차에 따라 청구하세요.
- 주간 메뉴는 [사내 식당 페이지](https://company.intranet/dining)에서 확인할 수 있습니다.
        """.strip(),
            metadata={
                "category": DocumentMetadataCategoryEnum.HR.value,
                "url": "https://company.intranet/dining",
            },
        ),
    ]
    return documents


def create_vector_db(documents: List[Document]) -> Chroma:
    chroma_path = ".vector.qnabot"
    store_path = ".store.qnabot"

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
    bm25_retriever = BM25Retriever.from_documents(
        documents=documents,
        search_kwargs={"k": 3},
    )
    vector_retriever = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 3},
    )
    return EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.5, 0.5],
    )


def create_prompt() -> ChatPromptTemplate:
    template = """
You are an assistant for new employees. Based on the provided documents, answer the user's question concisely, kindly and clearly. Add appropriate emojis to your responses.
If you don't know the answer, just say "모르는 정보 입니다. 인사팀에 문의해주세요.", don't try to make up an answer.
Ensure that all answers are in Korean.

Documents:
{context}

User's Question:
{input}

Answer:
    """.strip()
    return ChatPromptTemplate.from_template(template)


def parse_relevant_documents(documents: List[Document]) -> List[str]:
    def truncate_text(text: str, length: int = 20):
        if len(text) > length:
            return f"{text[:length]}..."
        return text

    return [
        f"[{doc.metadata.get('category')}] {truncate_text(doc.page_content)} {doc.metadata.get('url')}"
        for doc in documents
    ]


def start_streamlit(chain: Runnable):
    st.title("💬 Langchain QnA Chatbot")

    user_input = st.text_input("궁금하신걸 질문해주세요:")
    if user_input:
        output: dict = chain.invoke({"input": user_input})
        answer = output.get("answer")
        relevant_documents = parse_relevant_documents(output.get("context"))

        st.write(answer)
        st.write("[관련문서]")
        st.write(*["\n\n".join(relevant_documents)])
        st.write(output)


def app_main():
    documents = load_documents()
    vector_db = create_vector_db(documents)
    retriever = create_retriever(vector_db, documents)

    llm = ChatOllama(
        # model="llama3.1",
        model="exaone3.5:7.8b",
        # model="benedict/linkbricks-llama3.1-korean:8b",
        temparature=0,
    )
    prompt = create_prompt()
    qa_chain = create_stuff_documents_chain(llm, prompt)
    chain = create_retrieval_chain(retriever, qa_chain)
    start_streamlit(chain)

    # while True:
    #     user_input = input("\n유저 입력: ")
    #     res = chain.invoke({"input": user_input})
    #     print(res.get('context'))
    #     print(res.get('answer'))


if __name__ == '__main__':
    set_debug(False)
    app_main()
