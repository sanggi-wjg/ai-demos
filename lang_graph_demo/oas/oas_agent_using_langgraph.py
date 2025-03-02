from typing import TypedDict, Annotated

import yaml
from dotenv import load_dotenv
from langchain.globals import set_debug
from langchain.tools import tool
from langchain_community.agent_toolkits.openapi import planner
from langchain_community.agent_toolkits.openapi.spec import ReducedOpenAPISpec
from langchain_community.utilities.requests import RequestsWrapper
from langchain_core.utils.json_schema import dereference_refs
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.constants import END, START
from langgraph.graph import add_messages, StateGraph
from langgraph.types import interrupt, RetryPolicy

load_dotenv()


def reduce_my_openapi_spec(
    spec: dict,
    target_server: str = None,
    target_tags: list[str] = None,
    dereference: bool = True,
) -> ReducedOpenAPISpec:
    target_server = target_server or "dev"
    target_tags = set(tag.lower() for tag in target_tags) or set()
    target_methods = ["get", "post", "patch", "put", "delete"]

    endpoints = []
    for route, operation in spec["paths"].items():
        for operation_name, docs in operation.items():
            ok_method = operation_name.lower() in target_methods
            ok_tag = set(tag.lower() for tag in docs.get("tags")).intersection(target_tags) != set()

            if ok_method and ok_tag:
                endpoints.append((f"{operation_name.upper()} {route}", docs.get("description"), docs))

    if dereference:
        endpoints = [
            (name, description, dereference_refs(docs, full_schema=spec)) for name, description, docs in endpoints
        ]

    def reduce_endpoint_docs(docs: dict) -> dict:
        out = {}
        if docs.get("description"):
            out["description"] = docs.get("description")
        if docs.get("parameters"):
            out["parameters"] = [parameter for parameter in docs.get("parameters", []) if parameter.get("required")]
        if "200" in docs["responses"]:
            out["responses"] = docs["responses"]["200"]
        if docs.get("requestBody"):
            out["requestBody"] = docs.get("requestBody")
        return out

    def filter_servers(servers: list[dict]) -> list[dict]:
        servers = [server for server in servers if target_server in server["url"]]
        if not servers:
            raise ValueError(f"Server {target_server} not found in {spec['servers']}")
        return servers

    endpoints = [(name, description, reduce_endpoint_docs(docs)) for name, description, docs in endpoints]
    return ReducedOpenAPISpec(
        servers=filter_servers(spec["servers"]),
        description="",
        endpoints=endpoints,
    )


@tool
def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"query": query})
    return human_response["data"]


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


def openapi_agent_node(state: State):
    # tag_input = state["messages"][-1].content
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temparature=0.0)
    # llm = ChatOllama(model="qwen2.5:14b-instruct-q8_0", temparature=0.0)
    # llm = ChatOllama(model="qwen2.5:32b-instruct-q4_0", temparature=0.0)

    agent = planner.create_openapi_agent(
        api_spec,
        RequestsWrapper(headers={"Authorization": f"Bearer {access_token_input}"}),
        llm,
        allow_dangerous_requests=True,
        allowed_operations=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    query = """
You are an agent responsible for testing APIs based on a given OpenAPI specification.  
Your task is to analyze the OpenAPI spec, plan API test execution, and systematically call the APIs.

## **Objectives**

### 1️⃣ Plan API Calls
- Analyze the OpenAPI spec and determine the sequence of API calls.
- Identify relationships between available API endpoints, regardless of whether they support **Create (POST), Read (GET), Update (PUT), or Delete (DELETE)**.
- If only **GET APIs** are available, proceed with testing **all retrievable resources**.

### 2️⃣ Execute API Tests
- Call APIs according to the planned sequence and log responses.
- If Create (POST) and Update (PUT) APIs exist, use **random payloads**.
- If only Read (GET) APIs exist, call them systematically to ensure coverage.
- Continue testing even if an API call fails.

### 3️⃣ Utilize Dynamic Data (If Applicable)
- If an API provides an **ID in the response**, use it in related requests.
- If an API allows filtering or query parameters, generate diverse test cases.
- If an API provides pagination, ensure multiple pages are tested.

### 4️⃣ Error Handling & Logging
- Log request and response details for each API call.
- If an API fails, analyze the failure reason and continue testing.
- Implement retry logic for retriable failures.
""".strip()
    chat_response = agent.invoke(query)
    return {
        "messages": state["messages"] + [{"role": "assistant", "content": chat_response["output"]}],
    }


graph_builder.add_node("openapi_agent", openapi_agent_node, retry=RetryPolicy(retry_on=[ValueError, KeyError]))
graph_builder.add_edge(START, "openapi_agent")
graph_builder.add_edge("openapi_agent", END)
graph = graph_builder.compile()


with open(f"03_graph.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())


# tag_user_input = input("TAG (ex, banner, product, user): ")
# server_user_input = input("SERVER (ex, dev, stg, rc): ")
# access_token_input = input("ACCESS_TOKEN: ")

set_debug(False)

tag_user_input = "abtest"
server_user_input = "stg"
access_token_input = ""


with open("dataset/donotcommit.yaml", "r") as f:
    json_api_spec = yaml.safe_load(f)
api_spec = reduce_my_openapi_spec(json_api_spec, target_server=server_user_input, target_tags=[tag_user_input])

events = graph.stream(
    {
        "messages": [
            {
                "role": "user",
                # "content": "POST /store/order 생성 후 response body의 id로 정상 생성 되었는지 GET /store/order/{orderId} 조회 해줘",
                "content": f"Analyze the OpenAPI spec, plan API test execution, and systematically call the APIs.",
            },
        ]
    }
)
for event in events:
    print(event)
# for output in outputs:
#     output["messages"][-1].pretty_print()
