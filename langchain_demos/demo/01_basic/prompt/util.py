import os
import uuid
from typing import Literal

from langchain_community.chat_message_histories import FileChatMessageHistory, ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_ollama import ChatOllama


def create_session_of_chat_factory(
    session_id: str = str(uuid.uuid4()),
) -> FileChatMessageHistory:
    base_dir = ".chat.history"

    if not os.path.exists(base_dir):
        os.mkdir(base_dir)

    persist_directory = os.path.join(base_dir, f'${session_id}.json')
    chat_history = FileChatMessageHistory(persist_directory)
    return chat_history


def simple_chat(
    user_input: str,
    temperature: float = 0.8,
    top_p: float = 0.9,
    top_k: int = 40,
    repeat_penalty: float = 1.1,
    output_format: Literal["", "json"] = "",
):
    llm = ChatOllama(
        # model="llama3.1",
        model="benedict/linkbricks-llama3.1-korean:8b",
        # model="phi3:medium",
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        repeat_penalty=repeat_penalty,
        format=output_format,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{user_input}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    for token in chain.stream({"user_input": user_input}):
        print(token, end="", flush=True)


def simple_chat_with_history():
    llm = ChatOllama(
        model="benedict/linkbricks-llama3.1-korean:8b",
        temperature=0,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_input}"),
        ]
    )
    message_history = ChatMessageHistory()
    chain = RunnableWithMessageHistory(
        prompt | llm | StrOutputParser(),
        lambda session_id: message_history,
        input_messages_key="user_input",
        history_messages_key="chat_history",
    )

    while True:
        user_input = input("\nHuman:")

        for token in chain.stream(
            {"user_input": user_input},
            config={"configurable": {"session_id": "MyTestSessionID"}},
        ):
            print(token, end="", flush=True)
        print("")
