import yaml
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec

with open("openapi.yaml", "r") as f:
    json_api_spec = yaml.load(f, Loader=yaml.Loader)

api_spec = reduce_openapi_spec(json_api_spec)
print(json_api_spec, "\n============\n", api_spec)
