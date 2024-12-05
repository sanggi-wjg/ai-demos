from langchain.chains.conversation.base import ConversationChain
from langchain.globals import set_debug
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_ollama import ChatOllama


memory = ConversationBufferMemory()  # 이 메모리는 메시지를 저장한 다음 변수에 메시지를 추출할 수 있게 해줍니다.
memory.save_context(
    inputs={
        "human": "핏펫몰 주문 상태는 어떻게 되나요?",
    },
    outputs={
        "ai": "핏펫몰에서는 주문 상태를 총 5단계로 신규 주문, 배송 준비, 배송 중, 배송 완료, 구매확정 단계를 가집니다.",
    },
)
memory.save_context(
    inputs={
        "human": "핏펫몰 주문 취소 가능한 단계에 대해서 알려주세요.",
    },
    outputs={
        "ai": "주문 취소는 신규 주문 상태에서만 취소가 가능합니다.",
    },
)
memory.save_context(
    inputs={
        "human": "핏펫몰 교환 가능한 단계에 대해서 알려주세요.",
    },
    outputs={
        "ai": "교환은 배송 완료에서 요청 가능하며 구매확정 상태로 변경되면 교환이 불가능합니다.",
    },
)
memory.save_context(
    inputs={
        "human": "핏펫몰 어드민 유저는 어떻게 생성할 수 있나요?",
    },
    outputs={
        "ai": "각 팀에서 어드민 유저 권한을 가진 직원이 어드민에서 권한 부여를 통해서 생성할 수 있습니다.",
    },
)
memory.save_context(
    inputs={
        "human": "어드민 유저 권한 부여시 주의할 점이 있나요?",
    },
    outputs={
        "ai": """
        주의 해야할 점들은 다음과 같습니다.
        1. 유저 메일 계정이 회사 계정으로 되어있는지 확인해주세요.
        2. 유저 핸드폰 번호가 일치하는지 확인해주세요.
        """,
    },
)
memory.save_context(
    inputs={
        "human": "현재 사용되고 있는 백엔드 배치들의 목적과 실행 시간에 대해서 알려줘",
    },
    outputs={
        "ai": """
        - 자동 구매확정 상태로 변경
            - 역할: 핏펫몰 정책으로 일정 시간 이후 배송완료 주문을 구매확정으로 변경 시킵니다.
            - 시간: 일요일 20시 마다
            - 실행: 장고 배치
        - 데이터 클리닝
            - 역할: 어떠한 이유로 지저분하게 남아 있는 데이터 혹은 필요 없어진 데이터들을 청소합니다.
            - 시간: 일요일 23시 마다
            - 실행: 장고 배치
        - 레이너 점심식사
            - 역할: 점심시간이여서 밥을 먹습니다.
            - 시간: 평일 14시 마다
            - 실행: 장고 배치
        - 상품 기획전 데이터 생성
            - 역할: 주어진 정보에 따라 필요시 상품 기획전을 갱신 합니다.
            - 시간: 일요일 23시 50분 마다
            - 실행: 스프링 배치
        - 메인 홈 데이터 캐시 갱신 (매시간)
            - 역할: 홉화면 캐시 데이터를 계속 갱신시킵니다.
            - 시간: 10분마다
            - 실행: 스프링 배치
        - 슬랙 웹훅 알림 (매 5분 마다)
            - 역할: 빨리 밥 먹으라고 슬랙 웹훅을 보냅니다.
            - 시간: 평일 14시 마다
            - 실행: 스프링 배치
        """
    },
)
memory.save_context(
    inputs={
        "human": "백엔드 배치 인프라 구성에 대해서 알려줘",
    },
    outputs={
        "ai": "핏펫몰 백엔드 인프라 구성 중 배치 부분은 스프링 배치와 장고 Celery를 사용하고 있으며 스프링 배치는 k8s CronJob을 통해서 실행되며 장고는 Celery Beat를 통해서 실행되고 있습니다.",
    },
)
# a = memory.load_memory_variables({})

template = """
# Instruction:
The following is a friendly conversation between a human and an AI. 
The AI is talkative and provides lots of specific details from its context. 
If the AI does not know the answer to a question, it truthfully says it does not know. 

# IMPORTANT INSTRUCTION:
**The AI ONLY uses information contained in the "Relevant Information" section and does not hallucinate.**

# Relevant Information:
{history}

# Conversation:
Human: {input}
AI:"""
prompt = PromptTemplate(input_variables=["history", "input"], template=template)

llm = ChatOllama(model="llama3.1", temperature=0)
# llm = ChatOllama(model="phi3:medium", temperature=0)
chain = ConversationChain(llm=llm, memory=memory, prompt=prompt)

# set_debug(True)

while True:
    user_input = input("질문 입력: ")
    resp = chain.predict(input=user_input)
    print(resp)

    memory.save_context(inputs={"human": user_input}, outputs={"ai": resp})
