import faiss
from langchain_community.docstore import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_experimental.autonomous_agents import BabyAGI
from langchain_ollama import OllamaEmbeddings, ChatOllama

embeddings = OllamaEmbeddings(model="mxbai-embed-large")
embedding_size = 1024
index = faiss.IndexFlatL2(embedding_size)

vector_db = FAISS(
    embedding_function=embeddings.embed_query,
    index=index,
    docstore=InMemoryDocstore({}),
    index_to_docstore_id={},
)
llm = ChatOllama(
    model="llama3.1",
    temparature=0,
)

agi = BabyAGI.from_llm(
    llm=llm,
    vectorstore=vector_db,
    verbose=True,
    max_iterations=3,
)

agi.invoke({"objective": "Write a song about a cat"})
