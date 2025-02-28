import uuid
from typing import TypedDict, Annotated

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.tools import TavilySearchResults
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import add_messages, StateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.types import interrupt

load_dotenv()

memory = MemorySaver()


@tool
def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"query": query})
    return human_response["data"]


class State(TypedDict):
    messages: Annotated[list, add_messages]


search_tool = TavilySearchResults(max_results=5)
tools = [search_tool, human_assistance]

graph_builder = StateGraph(State)
llm_with_tools = ChatOllama(model="qwen2.5:7b").bind_tools(tools)


def chatbot(state: State):
    return {
        "messages": [llm_with_tools.invoke(state["messages"])],
    }


graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools))
graph_builder.add_conditional_edges("chatbot", tools_condition)

graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")
graph = graph_builder.compile(checkpointer=memory)


def stream_graph_updates(user_input: str, thread_id: str):
    events = graph.stream(
        {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant. Always answer in Korean."},
                {"role": "user", "content": user_input},
            ],
        },
        config={"configurable": {"thread_id": thread_id}},
        stream_mode="values",
    )
    for event in events:
        event["messages"][-1].pretty_print()


with open(f"02_graph.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())

thread_id = str(uuid.uuid4())

while True:
    # LangGraph에 대해서 알고 싶은데 간략하게 소개 해줄래?
    user_input = input("Human: ")
    if user_input in ("exit", "quit"):
        break

    stream_graph_updates(user_input, thread_id=thread_id)
