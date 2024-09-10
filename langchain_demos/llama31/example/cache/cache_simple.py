from langchain.globals import set_llm_cache, set_debug, set_verbose
from langchain_community.cache import SQLiteCache
from langchain_core.caches import InMemoryCache
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

llama = ChatOllama(model="llama3.1", temparature=0)
set_llm_cache(InMemoryCache())
set_llm_cache(SQLiteCache(database_path="llm_cache.db"))

# set_debug(True)
# set_verbose(False)

prompt = ChatPromptTemplate.from_template("{country}에 대해서 100자 정도로 요약해서 알려줘.")
chain = prompt | llama | StrOutputParser()

# 스트림은 캐시가 작동 안한다.
# while True:
#     for token in chain.stream({"country": input("\n국가명: ")}):
#         print(token, end="", flush=True)


while True:
    res = chain.invoke({"country": input("\n국가명: ")})
    print(res)
