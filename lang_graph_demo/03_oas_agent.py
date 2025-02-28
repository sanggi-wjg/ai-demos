from typing import TypedDict, Annotated

import yaml
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.agent_toolkits import OpenAPIToolkit
from langchain_community.agent_toolkits.openapi import planner
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain_community.utilities.requests import RequestsWrapper
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langgraph.constants import END, START
from langgraph.graph import add_messages, StateGraph
from langgraph.types import interrupt, RetryPolicy

load_dotenv()


@tool
def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"query": query})
    return human_response["data"]


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


def plan_agent_node(state: State):
    tag_input = state["messages"][-1].content

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    agent = planner.create_openapi_agent(
        api_spec,
        RequestsWrapper(headers={}),
        llm,
        allow_dangerous_requests=False,
        allowed_operations=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )

    chat_response = agent.invoke("Plan API calls for endpoints with tag:" + tag_input)
    return {
        "messages": state["messages"] + [{"role": "assistant", "content": chat_response["output"]}],
    }


def openapi_agent_node(state: State):
    plan_input = state["messages"][-1].content

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temparature=0.0)
    # llm = ChatOllama(model="qwen2.5:7b", temparature=0.0)
    agent = planner.create_openapi_agent(
        api_spec,
        RequestsWrapper(headers={}),
        llm,
        allow_dangerous_requests=True,
        allowed_operations=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    chat_response = agent.invoke(plan_input)
    return {
        "messages": state["messages"] + [{"role": "assistant", "content": chat_response["output"]}],
    }


graph_builder.add_node("plan_agent", plan_agent_node)
# graph_builder.add_node("openapi_agent", openapi_agent_node, retry=RetryPolicy(retry_on=[ValueError, KeyError]))

graph_builder.add_edge(START, "plan_agent")
# graph_builder.add_edge("plan_agent", "openapi_agent")
# graph_builder.add_edge("openapi_agent", END)
graph_builder.add_edge("plan_agent", END)

graph = graph_builder.compile()


with open(f"03_graph.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())

with open("data/openapi.yaml", "r") as f:
    json_api_spec = yaml.load(f, Loader=yaml.Loader)
    json_spec = yaml.safe_load(f)
api_spec = reduce_openapi_spec(json_api_spec)

inputs = {
    "messages": [
        {
            "role": "user",
            # "content": "POST /store/order 생성 후 response body의 id로 정상 생성 되었는지 GET /store/order/{orderId} 조회 해줘",
            "content": "USER",
        },
    ]
}
events = graph.stream(inputs)
for event in events:
    print(event)
# for output in outputs:
#     output["messages"][-1].pretty_print()
