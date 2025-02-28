from pprint import pprint

from prance import ResolvingParser

parser = ResolvingParser("openapi.yaml")
spec = parser.specification


endpoint = "/pet"
pprint(spec['paths'][endpoint])


from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

prompt = ChatPromptTemplate.from_messages(
    [
        {
            "role": "system",
            "content": """
You are an expert in parsing OpenAPI specifications and generating valid API requests.  
The user will provide an OpenAPI path specification (excluding unnecessary metadata like `openapi`, `info`, etc.).  
Your task is to generate `curl` commands with random payloads based on the given API definition.

# 📌 **Output Requirements**  
1. Identify all available HTTP methods (`GET`, `POST`, `PUT`, `DELETE`, etc.) in the provided path specification.  
2. Generate a `curl` request for each method following these rules:  
   - `GET`, `DELETE`: If query parameters exist, include random values.  
   - `POST`, `PUT`: Use the `requestBody` schema to generate a valid JSON payload with random values.  
3. Include necessary headers (`Content-Type: application/json`).  
4. If authentication is required (`security` settings), add an `Authorization: Bearer <TOKEN>` header.  
5. Ensure the generated `curl` request is fully executable.  

# ✨ **Additional Considerations**  
- Use OpenAPI-defined `type`, `enum`, and `format` to generate realistic random values.  
- Always include `required` fields, while optional fields should be included randomly.  
- For arrays (`type: array`), generate 1-3 random items.  
- If a field has `format: date-time`, generate a random ISO 8601 timestamp.  
- Numeric fields (`type: number` or `integer`) should contain reasonable random values.  
- Boolean fields should be randomly set to `true` or `false`.""".strip(),
        },
        {
            "role": "user",
            "content": "Generate a curl requests with payload randomly based on the following api-spec: {api_spec}",
        },
    ]
)

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
chain = prompt | llm

chat_response = chain.invoke({"api_spec": spec['paths'][endpoint]})
print(chat_response)
