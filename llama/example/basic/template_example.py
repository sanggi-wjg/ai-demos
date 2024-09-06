from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

llm = ChatOllama(model="llama3.1")
prompt = PromptTemplate.from_template("'{topic}'에 대해서 설명해줘.")

chain = prompt | llm | StrOutputParser()

for token in chain.stream({"topic": "Replica lag"}):
    print(token, end="", flush=True)
