from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import (
    StrOutputParser,
)
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOllama(model="llama3.1")
prompt1 = ChatPromptTemplate.from_template("translate '{korean_input}' to English.")
prompt2 = ChatPromptTemplate.from_template("Explain '{translated_korean_input}' briefly.")

chain1 = prompt1 | llm | StrOutputParser()
chain2 = {"translated_korean_input": chain1} | prompt2 | llm | StrOutputParser()
for token in chain2.stream({"korean_input": "인터넷 방송"}):
    print(token, end="", flush=True)
