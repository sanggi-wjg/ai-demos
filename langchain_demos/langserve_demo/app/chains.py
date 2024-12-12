import os.path
import uuid

from dotenv import load_dotenv
from langchain.chains.llm import LLMChain
from langchain.chains.sequential import SequentialChain
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_community.document_loaders import DirectoryLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import (
    RunnableSerializable,
    RunnablePassthrough,
    RunnableWithMessageHistory,
)
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()


def _session_of_chat_factory(
    session_id: str = str(uuid.uuid4()),
) -> FileChatMessageHistory:
    base_dir = ".chat.history"

    if not os.path.exists(base_dir):
        os.mkdir(base_dir)

    persist_directory = os.path.join(base_dir, f'${session_id}.json')
    chat_history = FileChatMessageHistory(persist_directory)
    return chat_history


def simple_chain() -> RunnableSerializable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"You are a helpful AI assistant. Please answer the user's questions kindly with emoticons. Answer me in Korean no matter what.",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            (
                "human",
                "Question: {question}",
            ),
        ]
    )
    llm = ChatOllama(model="llama3.1")
    return RunnableWithMessageHistory(
        prompt | llm | StrOutputParser(),
        _session_of_chat_factory,
        input_messages_key="question",
        history_messages_key="chat_history",
    )


def simple_groq_chain() -> RunnableSerializable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"You are a helpful AI assistant. Please answer the user's questions kindly with emoticons. Answer me in Korean no matter what.",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            (
                "human",
                "Question: {question}",
            ),
        ]
    )
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        max_tokens=None,
        max_retries=2,
        timeout=None,
    )
    return RunnableWithMessageHistory(
        prompt | llm | StrOutputParser(),
        _session_of_chat_factory,
        input_messages_key="question",
        history_messages_key="chat_history",
    )


def joke_of_topic_chain() -> RunnableSerializable:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"Tell me a really funny joke about the given Topic. Answer me in Korean no matter what.",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            (
                "human",
                "Topic: {topic}",
            ),
        ]
    )
    llm = ChatOllama(model="benedict/linkbricks-llama3.1-korean:8b")

    return RunnableWithMessageHistory(
        prompt | llm | StrOutputParser(),
        _session_of_chat_factory,
        input_messages_key="topic",
        history_messages_key="chat_history",
    )


def simple_rag_chain() -> RunnableSerializable:
    # retriever = TavilySearchAPIRetriever(k=5)
    # docs = retriever.invoke("한국 GDP 성장률")
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    vector_path = ".vector.rag"

    if not os.path.exists(vector_path):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=100,
            chunk_overlap=30,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n"],
        )
        loader = DirectoryLoader(path="./data/simple", glob="금투세*.txt")
        docs = loader.load_and_split(text_splitter)

        # cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
        #     underlying_embeddings=embeddings,
        #     document_embedding_cache=LocalFileStore(".store.rag"),
        #     namespace=embeddings.model,
        # )
        vector_db = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=vector_path,
        )
    else:
        vector_db = Chroma(
            embedding_function=embeddings,
            persist_directory=vector_path,
        )

    # bm25_retriever = BM25Retriever.from_documents(docs, search_kwargs={"k": 10})
    chroma_retriever = vector_db.as_retriever(search_type="mmr", search_kwargs={"k": 10})
    # ensemble_retriever = EnsembleRetriever(retrievers=[bm25_retriever, chroma_retriever], weights=[0.6, 0.4])

    prompt = ChatPromptTemplate.from_template(
        """
        Answer the question based only on the context provided. Answer me in Korean no matter what.    
        
        Context: {context}
        
        Question: {question} 
        """.strip()
    )
    # llm = ChatOllama(model="llama3.1", temparature=0)
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0,
        max_tokens=None,
        max_retries=2,
        timeout=None,
    )
    return {"context": chroma_retriever, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()


def simple_story_chain() -> RunnableSerializable:
    world_view_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You have a remarkable ability to create a world-building that rivals Steven Spielberg. Please create a world view of the given topic.",
            ),
            ("human", "{topic_of_story}"),
        ]
    )

    story_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You have a remarkable ability to create a story that rivals Steven Spielberg. Please create a story based on the world view.",
            ),
            ("human", "{world_view}"),
        ]
    )

    character_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You have a remarkable ability to create a character that rivals Steven Spielberg. Please create character based on the story with world view given.",
            ),
            ("human", "{world_view}\n\n{story}"),
        ]
    )

    translate_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a translator. Translate the texts given to Korean."),
            ("human", "{world_view}\n\n{story}\n\n{character}"),
        ]
    )

    llm = ChatOllama(model="llama3.1", temparature=0.8)

    world_view_prompt_chain = LLMChain(
        llm=llm, prompt=world_view_prompt, output_key="world_view", output_parser=StrOutputParser()
    )
    story_prompt_chain = LLMChain(
        llm=llm, prompt=world_view_prompt, output_key="story", output_parser=StrOutputParser()
    )
    character_prompt_chain = LLMChain(
        llm=llm, prompt=character_prompt, output_key="character", output_parser=StrOutputParser()
    )
    translate_prompt_chain = LLMChain(
        llm=llm, prompt=translate_prompt, output_key="translated", output_parser=StrOutputParser()
    )

    chain = SequentialChain(
        chains=[world_view_prompt_chain, story_prompt_chain, character_prompt_chain, translate_prompt_chain],
        input_variables=["topic_of_story"],
        output_variables=["world_view", "story", "character", "translated"],
    )
    return RunnableWithMessageHistory(
        chain,
        _session_of_chat_factory,
        input_messages_key="topic_of_story",
        history_messages_key="chat_history",
    )
