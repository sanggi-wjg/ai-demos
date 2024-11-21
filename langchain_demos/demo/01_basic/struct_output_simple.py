from pprint import pprint
from typing import Optional

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field


class Joke(BaseModel):
    """Joke to tell user."""

    setup: str = Field(description="The setup of the joke")
    punchline: str = Field(description="The punchline to the joke")
    rating: Optional[int] = Field(description="How funny the joke is, from 1 to 10")


prompt = ChatPromptTemplate.from_template("Please tell me joke about '{topic}' in Korean.")
parser = PydanticOutputParser(pydantic_object=Joke)
prompt.partial(format=parser.get_format_instructions())

llm = ChatOllama(model="llama3.1")
chain = prompt | llm

res = chain.invoke({"topic": "개발자"})
pprint(res)
