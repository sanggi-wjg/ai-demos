from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import (
    StrOutputParser,
    MarkdownListOutputParser,
    NumberedListOutputParser,
)
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOllama(model="llama3.1", temparature=1, format="json")
prompt = "유럽 여행지 10곳을 알려주세요. key: `places`. resonse in JSON format."

res = llm.invoke(prompt)
print(res)
