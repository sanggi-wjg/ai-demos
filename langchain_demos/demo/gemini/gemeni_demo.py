import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

load_dotenv()
# GEMENI_API_KEY = os.getenv("GEMINI_API_KEY")


class Fact(BaseModel):
    """Fact to tell user"""

    fact: str = Field(description="The fact that nobody knows")
    category: str = Field(description="The category of the fact")


prompt = ChatPromptTemplate.from_messages(
    [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Please tell me a fact about {category}."},
    ]
)

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite").with_structured_output(Fact)

chain = prompt | llm
chat_response = chain.invoke({"category": "space"})
print(chat_response)
# for token in chain.stream({"category": "space"}):
#     print(token, end="", flush=True)
