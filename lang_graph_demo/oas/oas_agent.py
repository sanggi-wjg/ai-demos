import yaml
from dotenv import load_dotenv
from langchain_community.agent_toolkits.openapi import planner
from langchain_community.agent_toolkits.openapi.spec import ReducedOpenAPISpec
from langchain_community.utilities.requests import RequestsWrapper
from langchain_core.utils.json_schema import dereference_refs
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

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


def openapi_agent():
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temparature=0.0)
    # llm = ChatOllama(model="qwen2.5:32b-instruct-q4_0", temparature=0.0)
    # llm = ChatOllama(model="qwen2.5:7b", temparature=0.0)

    agent = planner.create_openapi_agent(
        api_spec,
        RequestsWrapper(headers={"Authorization": f"Bearer {access_token_input}"}),
        llm,
        allow_dangerous_requests=True,
        allowed_operations=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    return agent


# tag_user_input = input("TAG (ex, banner, product, user): ")
# server_user_input = input("SERVER (ex, dev, stg, rc): ")
# access_token_input = input("ACCESS_TOKEN: ")

tag_user_input = "abtest"
server_user_input = "stg"
access_token_input = ""


with open("../dataset/donotcommit.yaml", "r") as f:
    json_api_spec = yaml.safe_load(f)
api_spec = reduce_my_openapi_spec(json_api_spec, target_server=server_user_input, target_tags=[tag_user_input])


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

agent = openapi_agent()
chat_response = agent.invoke({"input": query})
print(chat_response)
