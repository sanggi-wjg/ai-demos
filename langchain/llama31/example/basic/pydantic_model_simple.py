from langchain_community.chat_models import ChatOllama
from langchain_core.pydantic_v1 import BaseModel

from llama.example.basic.impl.ollama_impl import OllamaFunctions

llm = OllamaFunctions(model="llama3.1")


class Person(BaseModel):
    name: str


model = llm.with_structured_output(Person)
res = model.invoke('Bob is a person.')

print(res)
