import faiss
from dotenv import load_dotenv
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_community.docstore import InMemoryDocstore
from langchain_community.tools import TavilySearchResults, WriteFileTool, ReadFileTool
from langchain_community.vectorstores import FAISS
from langchain_core.tools import Tool
from langchain_experimental.autonomous_agents import AutoGPT
from langchain_ollama import OllamaEmbeddings, ChatOllama

load_dotenv()

search = TavilySearchResults(k=5)

tools = [
    Tool(
        name="search",
        func=search.invoke,
        description="useful for when you need to answer questions about current events. You should ask targeted questions",
    ),
    WriteFileTool(),
    ReadFileTool(),
]

embeddings = OllamaEmbeddings(model="mxbai-embed-large")
embedding_size = 1024
index = faiss.IndexFlatL2(embedding_size)

vector_db = FAISS(
    embedding_function=embeddings.embed_query,
    index=index,
    docstore=InMemoryDocstore({}),
    index_to_docstore_id={},
)

agent = AutoGPT.from_llm_and_tools(
    ai_name="Bot",
    ai_role="Assistant",
    tools=tools,
    llm=ChatOllama(model="llama3.1", temparature=0),
    memory=vector_db.as_retriever(),
    chat_history_memory=FileChatMessageHistory(".chat.history"),
)
agent.chain.verbose = False
agent.run(
    [
        "What were the winning boston marathon times for the past 5 years (ending in 2022)? Generate a table of the year, name, country of origin, and times."
    ]
)
