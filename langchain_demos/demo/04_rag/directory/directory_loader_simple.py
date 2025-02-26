from langchain_community.chat_models import ChatOllama
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory

loader = DirectoryLoader(path="../../../data", glob="*.sql")
extract = loader.load()
content = "\n".join([e.page_content for e in extract])

llama = ChatOllama(model="exaone3.5:7.8b", temparature=0.7)
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"""
        # Instruction 
        당신은 MySQL 쿼리 작성의 전문가 입니다. 현재 DB Scheme을 참고하여 주어진 질문에 대한 적합한 쿼리를 설명과 함께 제공해주세요.
        
        # 현재 DB Scheme
        {content}
        """,
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "#Question\n{user_input}"),
    ]
)
chain = prompt | llama | StrOutputParser()

store = {}


def get_session_history(session_id):
    print(f"[대화 세션ID]: {session_id}")
    return store[session_id] if session_id in store else ChatMessageHistory()


chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="user_input",
    history_messages_key="chat_history",
)

while True:
    # 상품별 상품 옵션의 개수를 조회하는 쿼리 알려줘
    # SKU별 주문 판매 개수 조회하는 쿼리 알려줘
    res = chain_with_history.invoke(
        {"user_input": input("\n유저 입력: ")},
        config={"configurable": {"session_id": "test123"}},
    )
    print(res)
