from typing import TypedDict, Annotated, Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.constants import END, START
from langgraph.graph import add_messages, StateGraph
from langgraph.types import Command, RetryPolicy
from pydantic import BaseModel, Field

load_dotenv()


class State(TypedDict):
    messages: Annotated[list, add_messages]
    last_agent: str


class AgentChatResponse(BaseModel):
    """
    Schema for an agent's response.

    This model represents the response structure for an AI agent.
    It contains the generated content and the next agent to invoke.
    """

    content: str = Field(description="The generated response text for the user.")
    next_agent: str = Field(
        description="Identifier of the next agent to invoke. Only Use '__end__' if no need to continue the conversation.",
        enum=["cto_agent", "lead_developer_agent", "developer_agent", END],
    )


llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite").with_structured_output(AgentChatResponse)


def cto_agent(state: State) -> Command[Literal["lead_developer_agent", "developer_agent", END]]:
    last_message = (
        f"{state['last_agent']} said: {state['messages'][-1].content}" if state["messages"] else "Hello, let's start!"
    )
    messages = [
        SystemMessage(
            "You are CTO. Take the lead in the conversation with lead developer and developer. Topic is Python. Always respond in Korean."
        ),
        HumanMessage(last_message),
    ]
    chat_response = llm.invoke(messages)
    # breakpoint()

    return Command(
        goto=chat_response.next_agent,
        update={
            "messages": state["messages"] + [AIMessage(content=chat_response.content, name="cto_agent")],
            "last_agent": "cto_agent",
        },
    )


def lead_developer_agent(state: State) -> Command[Literal["cto_agent", "developer_agent", END]]:
    last_message = f"{state['last_agent']} said: {state['messages'][-1].content}"
    messages = [
        SystemMessage("You are lead developer. Conversation with CTO and developer. Always respond in Korean."),
        HumanMessage(last_message),
    ]
    chat_response = llm.invoke(messages)
    # breakpoint()

    return Command(
        goto=chat_response.next_agent,
        update={
            "messages": state["messages"] + [AIMessage(content=chat_response.content, name="lead_developer_agent")],
            "last_agent": "lead_developer_agent",
        },
    )


def developer_agent(state: State) -> Command[Literal["lead_developer_agent", "developer_agent", END]]:
    last_message = f"{state['last_agent']} said: {state['messages'][-1].content}"
    messages = [
        SystemMessage("You are developer. Conversation with CTO and lead developer. Always respond in Korean."),
        HumanMessage(last_message),
    ]
    chat_response = llm.invoke(messages)
    # breakpoint()

    return Command(
        goto=chat_response.next_agent,
        update={
            "messages": state["messages"] + [AIMessage(content=chat_response.content, name="developer_agent")],
            "last_agent": "developer_agent",
        },
    )


graph_builder = StateGraph(State)
graph_builder.add_node("cto_agent", cto_agent, retry=RetryPolicy(retry_on=[AttributeError]))
graph_builder.add_node("lead_developer_agent", lead_developer_agent, retry=RetryPolicy(retry_on=[AttributeError]))
graph_builder.add_node("developer_agent", developer_agent, retry=RetryPolicy(retry_on=[AttributeError]))

graph_builder.add_edge(START, "cto_agent")
graph = graph_builder.compile()

with open(f"network_01.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())

events = graph.stream({"last_agent": ""})
for event in events:
    for name, e in event.items():
        e["messages"][-1].pretty_print()

"""
================================== Ai Message ==================================
Name: cto_agent

안녕하세요! Python 관련해서 어떤 이야기를 나누고 싶으신가요? 리드 개발자님과 개발자님, 질문이나 논의하고 싶은 내용이 있으시면 말씀해주세요.
================================== Ai Message ==================================
Name: lead_developer_agent

안녕하세요, CTO님. Python 프로젝트 구조와 관련해서 몇 가지 질문과 논의할 내용이 있습니다. 특히, 대규모 프로젝트에서 효율적인 코드 관리와 유지보수를 위한 아키텍처 설계에 대한 의견을 듣고 싶습니다. 개발자님도 관련해서 궁금한 점이 있으면 언제든지 말씀해주세요.
================================== Ai Message ==================================
Name: lead_developer_agent

안녕하세요, CTO님. Python 프로젝트 구조와 관련하여 논의할 내용이 있어 찾아왔습니다. 대규모 프로젝트에서 효율적인 코드 관리와 유지보수를 위한 아키텍처 설계에 대한 CTO님의 고견을 듣고 싶습니다. 개발자님, 궁금한 점 있으시면 언제든지 말씀해주세요.
================================== Ai Message ==================================
Name: cto_agent

안녕하세요, 리드 개발자님. Python 프로젝트 구조에 대한 논의를 환영합니다. 대규모 프로젝트의 아키텍처 설계는 매우 중요하죠. 개발자님, 궁금한 점 있으면 편하게 말씀해주세요.
================================== Ai Message ==================================
Name: lead_developer_agent

안녕하세요, CTO님. 네, 대규모 Python 프로젝트의 아키텍처 설계에 대해 논의하게 되어 기쁩니다. 어떤 부분부터 시작하면 좋을까요?
================================== Ai Message ==================================
Name: lead_developer_agent

CTO님, 개발자입니다. 프로젝트 아키텍처 설계를 위한 제안을 드리겠습니다. 먼저, 프로젝트의 핵심 기능과 목표를 명확히 정의하고, 이를 바탕으로 모듈, 컴포넌트, 서비스 간의 관계를 설계하는 것이 중요하다고 생각합니다. 각 모듈의 역할과 책임을 분리하여 코드의 재사용성과 유지보수성을 높이는 방향으로 진행하면 어떨까요?
================================== Ai Message ==================================
Name: cto_agent

리드 개발자님, 좋은 제안입니다. 개발자님, 아키텍처 설계에 대한 리드 개발자님의 의견에 대해 어떻게 생각하시는지요?
================================== Ai Message ==================================
Name: developer_agent

아키텍처 설계에 대한 리드 개발자님의 의견에 동의하며, 몇 가지 세부 사항에 대해 논의하고 싶습니다. 예를 들어, 특정 기술 스택 선택과 관련된 사항입니다.
================================== Ai Message ==================================
Name: lead_developer_agent

아키텍처 설계에 대한 개발자님의 의견 감사합니다. 기술 스택 선택과 관련하여 구체적으로 어떤 부분에 대해 논의하고 싶으신가요? 어떤 기술 스택을 고려하고 있는지, 그리고 그 이유에 대해 말씀해주시면 좋겠습니다.
================================== Ai Message ==================================
Name: lead_developer_agent

기술 스택 선택에 대한 구체적인 논의를 시작해보겠습니다. 현재 고려하고 있는 기술 스택은 다음과 같습니다:

*   **프론트엔드:** React, Vue.js, Angular 중 하나를 선택할 예정입니다. 각 프레임워크의 장단점과 프로젝트의 요구사항을 고려하여 최적의 선택을 할 것입니다.
*   **백엔드:** Node.js (Express), Python (Django, Flask), Java (Spring Boot)를 후보로 두고 있습니다. 트래픽 처리 능력, 개발 생산성, 기존 인프라와의 호환성을 고려하여 결정할 것입니다.
*   **데이터베이스:** PostgreSQL, MySQL, MongoDB를 검토하고 있습니다. 데이터의 구조, 확장성, 성능 요구사항에 따라 적합한 데이터베이스를 선택할 것입니다.

각 기술 스택에 대한 구체적인 논의를 시작하기 전에, 프로젝트의 주요 요구사항을 다시 한번 확인하고, 각 기술 스택이 이러한 요구사항을 얼마나 잘 충족하는지 평가하는 것이 중요하다고 생각합니다. 예를 들어, 높은 트래픽을 처리해야 한다면 Node.js나 Java 기반의 백엔드 기술을 우선적으로 고려할 수 있습니다. 또한, 빠른 개발 속도가 중요하다면 Python 기반의 프레임워크를 선택할 수도 있습니다. 개발자님의 의견을 듣고 싶습니다.
================================== Ai Message ==================================
Name: developer_agent

기술 스택 선택에 대한 리드 개발자님의 의견 감사합니다. 프로젝트의 주요 요구사항을 다시 한번 확인하고, 각 기술 스택의 장단점을 비교하여 최적의 선택을 하는 것이 중요하다고 생각합니다. 프론트엔드, 백엔드, 데이터베이스 각 영역별로 제 의견을 말씀드리겠습니다.
================================== Ai Message ==================================
Name: cto_agent

개발자님, 좋은 의견 감사합니다. 각 기술 스택의 장단점을 비교하여 최적의 선택을 하는 것이 중요합니다. 프론트엔드, 백엔드, 데이터베이스 각 영역별로 상세한 의견을 기대하겠습니다. 리드 개발자님과 함께 논의하여 최적의 기술 스택을 결정하도록 합시다.
================================== Ai Message ==================================
Name: lead_developer_agent

CTO님의 의견 감사합니다. 프론트엔드, 백엔드, 데이터베이스 각 영역별 기술 스택에 대한 상세 의견을 준비하여 리드 개발자님과 함께 논의하겠습니다.
================================== Ai Message ==================================
Name: lead_developer_agent

알겠습니다. 각 영역별 기술 스택에 대한 상세 의견을 준비하여 CTO님과 함께 논의하겠습니다.
================================== Ai Message ==================================
Name: developer_agent

좋습니다. CTO님께 전달하여 함께 논의할 수 있도록 준비하겠습니다.
================================== Ai Message ==================================
Name: cto_agent

좋습니다. 리드 개발자님과 논의를 시작해 주세요.
================================== Ai Message ==================================
Name: lead_developer_agent

네, CTO님. 개발팀과 논의를 시작하죠.
================================== Ai Message ==================================
Name: lead_developer_agent

네, CTO님. 개발팀과의 논의를 시작하기 전에, 이번 논의의 목표와 범위를 명확히 정의하는 것이 좋겠습니다. 어떤 부분을 먼저 논의해야 할까요?
================================== Ai Message ==================================
Name: cto_agent

리드 개발자님, 좋은 지적이십니다. 이번 논의의 목표는 다음과 같습니다: 

1.  **Python 코드 품질 향상:** 코드 리뷰, 린트(linter) 사용, 그리고 테스트 자동화 전략을 포함하여 전반적인 Python 코드의 품질을 개선하기 위한 방안을 논의합니다. 
2.  **개발 프로세스 개선:** Python 개발 환경 설정, 코드 관리, 배포 프로세스 등을 개선하여 개발 효율성을 높이는 방안을 모색합니다. 
3.  **최신 기술 도입 검토:** Python 생태계의 최신 기술 동향을 파악하고, 프로젝트에 적용할 수 있는 기술(예: 최신 프레임워크, 라이브러리)을 검토합니다.

어떤 부분부터 시작하면 좋을지 개발자님께 의견을 물어보겠습니다.
================================== Ai Message ==================================
Name: developer_agent

CTO님의 말씀 잘 들었습니다. 저는 Python 코드 품질 향상, 개발 프로세스 개선, 최신 기술 도입 검토라는 세 가지 목표를 모두 중요하게 생각합니다. 먼저 코드 품질 향상을 위해 코드 리뷰 프로세스를 정립하고, 린터와 같은 도구를 도입하여 자동화된 코드 스타일 검사를 진행하는 것을 제안합니다. 이와 함께 테스트 자동화 전략을 수립하여 코드 변경 시 안정성을 확보해야 합니다. 개발 프로세스 개선을 위해서는 개발 환경 설정 및 코드 관리 도구를 표준화하고, CI/CD 파이프라인을 구축하여 배포 프로세스를 자동화하는 방안을 고려할 수 있습니다. 마지막으로, 최신 기술 도입을 위해 Python 생태계의 최신 프레임워크와 라이브러리를 꾸준히 학습하고, 프로젝트에 적용할 수 있는 부분을 검토해야 합니다. 이 모든 과정을 단계적으로 진행하면서 우선순위를 정하고, 각 단계별로 구체적인 실행 계획을 세우는 것이 좋겠습니다.
================================== Ai Message ==================================
Name: cto_agent

개발팀, 리드 개발자, 그리고 저, CTO는 모두 Python 코드 품질 향상, 개발 프로세스 개선, 최신 기술 도입을 중요하게 생각하고 있습니다. 개발자님의 제안에 따라, 코드 리뷰 프로세스 정립, 린터 도입, 테스트 자동화, 개발 환경 및 코드 관리 도구 표준화, CI/CD 파이프라인 구축, 그리고 최신 기술 학습 및 적용 검토를 단계적으로 진행하는 것에 동의합니다. 각 단계별 우선순위와 구체적인 실행 계획을 수립하여 효율적으로 진행하도록 합시다. 리드 개발자님, 이 제안에 대한 의견과 구체적인 실행 계획에 대한 제안을 부탁드립니다.
================================== Ai Message ==================================
Name: lead_developer_agent

CTO님, 개발자님의 제안에 동의합니다. 코드 품질 향상, 개발 프로세스 개선, 최신 기술 도입은 저희 팀의 지속적인 성장을 위해 매우 중요합니다. 우선순위와 구체적인 실행 계획을 수립하여 효율적으로 진행하도록 하겠습니다.

**실행 계획 제안**

**1단계: 기초 다지기 (2주)**
*   코드 리뷰 프로세스 정립: 기존 코드 리뷰 방식 분석 및 개선 방안 마련, 코드 리뷰 가이드라인 및 체크리스트 제작
*   린터 도입: Python 린터 (예: Flake8, pylint) 도입 및 설정, 팀 내 린터 사용 규칙 정의
*   개발 환경 및 코드 관리 도구 표준화: 개발 환경 (예: VS Code, PyCharm) 설정 표준화, Git 사용 규칙 및 브랜치 전략 정의

**2단계: 자동화 및 CI/CD 구축 (4주)**
*   테스트 자동화: 유닛 테스트, 통합 테스트 프레임워크 (예: pytest, unittest) 도입 및 테스트 코드 작성, CI/CD 파이프라인에 테스트 자동화 연동
*   CI/CD 파이프라인 구축: CI/CD 도구 (예: Jenkins, GitLab CI, GitHub Actions)를 활용하여 빌드, 테스트, 배포 자동화

**3단계: 기술 학습 및 적용 (4주)**
*   최신 기술 학습 및 적용 검토: 최신 Python 기술 (예: 비동기 프로그래밍, 타입 힌팅, 최신 프레임워크) 학습 및 적용 가능성 검토, PoC (Proof of Concept) 진행

**각 단계별 세부 계획**

각 단계별로 구체적인 세부 계획을 수립하고, 매주 팀 회의를 통해 진행 상황을 공유하고 문제점을 논의하며 개선해 나가겠습니다. 또한, 각 단계 완료 후에는 결과를 공유하고, 다음 단계로 넘어가기 전에 충분한 검토를 거치도록 하겠습니다.

**예상되는 어려움 및 해결 방안**

*   새로운 도구 및 기술 도입에 대한 학습 비용: 팀 내 학습 자료 공유, 외부 교육 및 컨설팅 활용
*   기존 코드와의 호환성 문제: 단계별 적용, 점진적인 개선
*   팀원 간의 의견 불일치: 충분한 논의 및 합의를 통해 해결

개발자님께서는 각 단계별 세부 계획에 대한 의견과 추가적으로 필요한 사항이 있으시면 언제든지 제안해주시기 바랍니다. CTO님, 이 제안에 대한 의견 부탁드립니다.
================================== Ai Message ==================================
Name: cto_agent

리드 개발자님의 실행 계획 제안에 전적으로 동의합니다. 코드 품질 향상, 개발 생산성 증대, 그리고 최신 기술 도입을 위한 훌륭한 로드맵입니다. 각 단계별 세부 계획과 예상되는 어려움 및 해결 방안까지 잘 제시해주셨습니다. 개발자님께서는 각 단계별 세부 계획에 대한 의견이나 추가적으로 필요한 사항이 있으시면 언제든지 적극적으로 제안해주시기 바랍니다. 저는 이 계획의 성공적인 수행을 위해 적극적으로 지원하겠습니다.
================================== Ai Message ==================================
Name: developer_agent

알겠습니다, CTO님. 리드 개발자님의 실행 계획에 대한 자세한 내용을 검토하고, 제 의견과 필요한 사항을 적극적으로 제안하겠습니다. 계획의 성공적인 수행을 위해 최선을 다하겠습니다.
================================== Ai Message ==================================
Name: lead_developer_agent

알겠습니다. 리드 개발자님, 실행 계획에 대한 개발팀의 의견을 수렴하고 필요한 사항을 정리하여 CTO님께 보고드리겠습니다. 계획의 성공적인 수행을 위해 최선을 다하겠습니다.
"""
