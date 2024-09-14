from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import (
    StrOutputParser,
    MarkdownListOutputParser,
    NumberedListOutputParser,
)
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOllama(model="llama3.1")
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful AI assistant. Please answer the user's questions kindly with emoticons. Answer me in Korean no matter what.",
        ),
        (
            "human",
            "{user_input}",
        ),
    ]
)

chain = prompt | llm | StrOutputParser()
for token in chain.stream({"user_input": "안녕? 너가 할수 있는것들은 뭐가 있니?"}):
    print(token, end="", flush=True)

print("\n\n")

chain2 = prompt | llm | MarkdownListOutputParser()
for token in chain2.stream({"user_input": "안녕? 너가 할수 있는것들은 뭐가 있니?"}):
    print(token, end="", flush=True)

print("\n\n")

chain3 = prompt | llm | NumberedListOutputParser()
for token in chain3.stream({"user_input": "안녕? 너가 할수 있는것들은 뭐가 있니?"}):
    print(token, end="", flush=True)
