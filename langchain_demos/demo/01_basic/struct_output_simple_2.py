from typing import List

from langchain.globals import set_debug
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

set_debug(True)


class ResponseOutput(BaseModel):
    """Always use this tool to structure your response to the user."""

    answer: str = Field(description="The answer to the user's question.")
    followup_questions: List[str] = Field(description="A five followup questions the user could ask.")


prompt = ChatPromptTemplate.from_template(
    "You are useful AI assistant. Please answer kindly.\n# Question: {question}\n# Answer:"
)

llm = ChatOllama(
    # model="llama3.1",
    model="exaone3.5:7.8b",
    # model="benedict/linkbricks-llama3.1-korean:8b",
).with_structured_output(ResponseOutput)

chain = prompt | llm
res = chain.invoke({"question": "미국 금리 인하시 한국 경제에 미치는 영향들에 대해서 알려줘?"})
print(res)
