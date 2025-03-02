import yaml
from langchain_community.agent_toolkits.openapi.spec import ReducedOpenAPISpec
from langchain_core.utils.json_schema import dereference_refs


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
        # if docs.get("description"):
        #     out["description"] = docs.get("description")
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
        description=spec["info"].get("description", ""),
        endpoints=endpoints,
    )


with open("../donotcommit.yaml", "r") as f:
    json_api_spec = yaml.safe_load(f)
api_spec = reduce_my_openapi_spec(json_api_spec, target_server="stg", target_tags=["banner"], dereference=True)
# print(json_api_spec, "\n============\n", api_spec)


print(api_spec)
print()
