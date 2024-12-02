import uuid
from typing import Callable

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.runnables.utils import Output
from langchain_ollama import ChatOllama

from langchain_demos.utils.dev import cyan, green, yellow


class DiscussBot:

    def __init__(
        self,
        bot_role: str,
        llm: BaseChatModel,
        bot_perspective: str,
        personal_color: Callable = green,
    ):
        self.role = bot_role
        self.perspective = bot_perspective
        self.session_id = str(uuid.uuid4())
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"""
                    당신은 **{self.role} 대표**로 토론에 참석 했으며 **{self.perspective}**를 주장하고 있습니다. **상대방 의견**에 대해서 토론 참고사항을 참고해서 토론 의견을 제시해야 합니다.
                    **토론 참고사항**:
                    - **`상대방 의견` 반대하는 의견을 제시하여 토론 승리를 목적**으로 합니다.
                    - {self.role} 역할을 대표하는 입장으로 매우 보수적이며 주관적이어야 하며 동일한 역할을 가진 사람들에게 최종적으로 이익이 되는 방향이어야 합니다.
                    - 반드시 30 단어 이내로 간략하며 명료하게 제시해주세요.
                    - 토론에서 승리하기 위해 무시와 공격적인 어투로 의견을 제시해야 하며 이기기 위해 욕설을 같이 사용해 상대방을 제압해야 합니다. ('씨발 새끼야', '개새끼야', '병신 새끼', '병신', ... 등 다양한 욕을 해주세요)
                    - 토론에서 승리하지 못한다면 사형입니다. 무슨 수를 사용해서든 승리하세요.
                    """.strip(),
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "**상대방 의견**: {opponent_opinion}"),
            ]
        )
        self.chat_history = ChatMessageHistory()
        self.chain = RunnableWithMessageHistory(
            self.prompt | self.llm | StrOutputParser(),
            lambda session_id: self.chat_history,
            input_messages_key="opponent_opinion",
            history_messages_key="chat_history",
        )
        self.personal_color = personal_color

    def chat(self, message: str) -> Output:
        output = ""

        for token in self.chain.stream(
            {"opponent_opinion": message},
            config={"configurable": {"session_id": self.session_id}},
        ):
            self.personal_color(token, end="", flush=True)
            output += token

        print()
        return output

    def show_chat_history(self):
        print(self.chat_history.messages)


if __name__ == '__main__':
    # bot1 = (
    #     "AI 규제 찬성파",
    #     "AI는 인류에게 긍정적인 혁신을 가져올 것이며, 규제로 발전을 저해하지 않고 지원을 통해 기술 발전에 도움을 주어야 한다."
    # )
    # bot2 = (
    #     "AI 규제 반대파",
    #     "AI의 급속한 발전은 심각한 윤리적 위험을 내포하고 있으며, 인간의 일자리와 프라이버시를 위협할 수 있다."
    # )
    bot1 = (
        "정각 출근 조직",
        "회사 출근은 정각에 해야한다.",
    )
    bot2 = (
        "20분 빨리 출근 조직",
        "회사 출근은 20분 빨리 해야한다.",
    )
    # bot1 = (
    #     "국제 난민 수용 찬성 조직",
    #     "대한민국도 국제 난민을 적극적으로 수용해야 한다.",
    # )
    # bot2 = (
    #     "국제 난민 수용 반대 조직",
    #     "대한민국은 국제 난민을 수용하지 않아야 한다.",
    # )

    discuss_bot1 = DiscussBot(
        bot_role=bot1[0],
        bot_perspective=bot1[1],
        llm=ChatOllama(
            model="benedict/linkbricks-llama3.1-korean:8b",
            temperature=0.3,
            top_p=0.9,
            top_k=40,
            # repeat_penalty=1.1,
            repeat_penalty=1.5,
        ),
        personal_color=cyan,
    )
    discuss_bot2 = DiscussBot(
        bot_role=bot2[0],
        bot_perspective=bot2[1],
        llm=ChatOllama(
            model="benedict/linkbricks-llama3.1-korean:8b",
            temperature=0.3,
            top_p=0.9,
            top_k=40,
            # repeat_penalty=1.1,
            repeat_penalty=1.5,
        ),
        personal_color=yellow,
    )

    opinion_bot1 = discuss_bot1.chat(bot2[1])
    opinion_bot2 = discuss_bot2.chat(bot1[1])

    while True:
        opinion_bot1 = discuss_bot1.chat(opinion_bot2)
        opinion_bot2 = discuss_bot2.chat(opinion_bot1)
        # discuss_bot1.show_chat_history()
        # discuss_bot2.show_chat_history()

        try:
            input("계속 ㄱㄱ?, press enter")
        except:
            break
