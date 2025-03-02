from typing import TypedDict, Annotated, Literal

from langchain_experimental.utilities import PythonREPL
from langchain_ollama import ChatOllama
from langgraph.constants import END, START
from langgraph.graph import add_messages, StateGraph
from langgraph.types import Command, RetryPolicy
from pydantic import BaseModel, Field

repl = PythonREPL()


class State(TypedDict):
    messages: Annotated[list, add_messages]


class AgentChatResponse(BaseModel):
    """Response to the user."""

    content: str = Field(description="content of response")
    next_agent: Literal["agent_1", "agent_2", "agent_3", END] = Field(description="next agent to call")


def agent_1(state: State) -> Command[Literal["agent_2", "agent_3", END]]:
    # llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite")
    llm = ChatOllama(model="qwen2.5:14b-instruct-q8_0").with_structured_output(AgentChatResponse)
    chat_response = llm.invoke("Tell me a fact that nobody knows about SpringBoot.")
    return Command(
        goto=chat_response.next_agent,
        update={"messages": [chat_response.content]},
    )


def agent_2(state: State) -> Command[Literal["agent_1", "agent_3", END]]:
    # llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite")
    llm = ChatOllama(model="qwen2.5:14b-instruct-q8_0").with_structured_output(AgentChatResponse)
    chat_response = llm.invoke("Tell me a fact that nobody knows about Django.")
    return Command(
        goto=chat_response.next_agent,
        update={"messages": [chat_response.content]},
    )


def agent_3(state: State) -> Command[Literal["agent_1", "agent_2", END]]:
    # llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite")
    llm = ChatOllama(model="qwen2.5:14b-instruct-q8_0").with_structured_output(AgentChatResponse)
    chat_response = llm.invoke("Tell me a fact that nobody knows about Laravel.")
    return Command(
        goto=chat_response.next_agent,
        update={"messages": [chat_response.content]},
    )


graph_builder = StateGraph(State)
graph_builder.add_node("agent_1", agent_1, retry=RetryPolicy(retry_on=[AttributeError]))
graph_builder.add_node("agent_2", agent_2, retry=RetryPolicy(retry_on=[AttributeError]))
graph_builder.add_node("agent_3", agent_3, retry=RetryPolicy(retry_on=[AttributeError]))

graph_builder.add_edge(START, "agent_1")
graph = graph_builder.compile()

with open(f"network_01.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())

events = graph.stream(
    {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Always answer in Korean."},
            {"role": "user", "content": "Tell me a fact."},
        ],
    }
)
for event in events:
    print(event, end="", flush=True)
