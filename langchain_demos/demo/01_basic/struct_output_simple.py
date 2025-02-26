from pprint import pprint
from typing import Optional

from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

load_dotenv()


class Joke(BaseModel):
    """Joke to tell user."""

    setup: str = Field(description="The setup of the joke")
    punchline: str = Field(description="The punchline to the joke")
    rating: Optional[int] = Field(description="How funny the joke is, from 1 to 10")


prompt = ChatPromptTemplate.from_messages(
    [
        {
            "role": "system",
            "content": "You are a helpful AI assistant. Please answer the user's questions kindly with emoticons. Answer me in Korean no matter what.",
        },
        {"role": "human", "content": "Please tell me joke about '{topic}' in Korean."},
    ]
)

llm = ChatOllama(model="raynor").bind_tools([Joke])
# llm = ChatGroq(model="deepseek-r1-distill-llama-70b").bind_tools([Joke])

chain = prompt | llm
chat_response = chain.invoke({"topic": "개발자"})
print(chat_response.response_metadata)

joke_response = Joke.model_validate(chat_response.tool_calls[0]["args"])
print(joke_response)
