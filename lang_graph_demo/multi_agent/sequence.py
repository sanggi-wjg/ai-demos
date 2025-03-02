from typing import TypedDict, Annotated, Literal, List

from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langgraph.constants import END, START
from langgraph.graph import add_messages, StateGraph
from langgraph.types import Command, RetryPolicy
from pydantic import BaseModel, Field

load_dotenv()


class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_input: Annotated[str, "User input"]
    agent_order: Annotated[List[str], "List of agent names in the order they should be called"]
    current_index: Annotated[int, "Index of the current agent"]


class AgentChatResponse(BaseModel):
    """
    Schema for an agent's response.

    This model represents the response structure for an AI agent.
    """

    content: str = Field(description="The generated response text for the user.")


# llm = ChatOllama(model="qwen2.5:14b-instruct-q8_0").with_structured_output(AgentChatResponse)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite").with_structured_output(AgentChatResponse)


def agent_1(state: State) -> Command[Literal["agent_2"]]:
    chat_response = llm.invoke(f"{state["user_input"]} Python.")
    # breakpoint()

    return Command(
        goto=state["agent_order"][state["current_index"] + 1],
        update={
            "messages": [AIMessage(chat_response.content, name="agent_1")],
            "current_index": state["current_index"] + 1,
        },
    )


def agent_2(state: State) -> Command[Literal["agent_3"]]:
    chat_response = llm.invoke(f"{state["user_input"]} Kotlin.")
    # breakpoint()

    return Command(
        goto=state["agent_order"][state["current_index"] + 1],
        update={
            "messages": [AIMessage(chat_response.content, name="agent_2")],
            "current_index": state["current_index"] + 1,
        },
    )


def agent_3(state: State) -> Command[Literal["__end__"]]:
    chat_response = llm.invoke(f"{state["user_input"]} PHP.")
    # breakpoint()

    return Command(
        goto=END,
        update={
            "messages": [AIMessage(chat_response.content, name="agent_3")],
        },
    )


graph_builder = StateGraph(State)
graph_builder.add_node("agent_1", agent_1, retry=RetryPolicy(retry_on=[AttributeError]))
graph_builder.add_node("agent_2", agent_2, retry=RetryPolicy(retry_on=[AttributeError]))
graph_builder.add_node("agent_3", agent_3, retry=RetryPolicy(retry_on=[AttributeError]))

graph_builder.add_edge(START, "agent_1")
graph = graph_builder.compile()

# with open(f"sequence_01.png", "wb") as f:
#     f.write(graph.get_graph().draw_mermaid_png())

events = graph.stream(
    {
        "user_input": "Tell me a fact that nobody knows about",
        "agent_order": ["agent_1", "agent_2", "agent_3"],
        "current_index": 0,
    },
)
for event in events:
    print(event)
