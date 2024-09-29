import os
from typing import Callable, List

from dotenv import load_dotenv
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.document_loaders import TextLoader
from langchain_community.tools import TavilySearchResults
from langchain_community.vectorstores import Chroma
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool, create_retriever_tool
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DialogueAgent:
    def __init__(
        self,
        name: str,
        system_message: SystemMessage,
        llm: BaseChatModel,
    ):
        self.name = name
        self.system_message = system_message
        self.llm = llm
        self.prefix = f"{self.name}: "
        self.message_history = []
        self.reset()

    def reset(self):
        self.message_history = ["here is the conversation so far"]

    def send(self):
        return self.llm(
            [
                self.system_message,
                HumanMessage(content="\n".join([self.prefix] + self.message_history)),
            ]
        ).content

    def receive(self, name: str, message: str):
        self.message_history.append(f"{name}: {message}")


class DialogueSimulator:

    def __init__(
        self,
        agents: list[DialogueAgent],
        selection_func: Callable[[int, List[DialogueAgent]], int],
    ):
        self.agents = agents
        self.select_next_speaker = selection_func
        self._step = 0

    def incr_step(self):
        self._step += 1

    def reset_all_agents(self):
        for agent in self.agents:
            agent.reset()

    def inject(self, name: str, message: str):
        for agent in self.agents:
            agent.receive(name, message)

        self.incr_step()

    def step(self):
        speaker_idx = self.select_next_speaker(self._step, self.agents)
        speaker = self.agents[speaker_idx]
        message = speaker.send()

        for agent in self.agents:
            agent.receive(speaker.name, message)

        self.incr_step()
        return speaker.name, message


class DialogueAgentWithTools(DialogueAgent):

    def __init__(
        self,
        name: str,
        system_message: SystemMessage,
        llm: BaseChatModel,
        tools: List[Tool],
    ):
        self.tools = tools
        super().__init__(name, system_message, llm)

    def invoke(self) -> str:
        template = """
        """
        prompt = PromptTemplate.from_template(template)

        agent = create_react_agent(self.llm, self.tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )
        message = AIMessage(
            content=agent_executor.invoke(
                {"input": "\n".join([self.system_message.content] + [self.prefix] + self.message_history)}
            )["output"]
        )
        return message.content


load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

llama = ChatOllama(model="llama3.1", temparature=0)
embeddings = OllamaEmbeddings(model="mxbai-embed-large")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=50,
    length_function=len,
    is_separator_regex=False,
    separators=["\n\n"],
)

search_tool = Tool(
    name="web search",
    func=TavilySearchResults(k=5).invoke,
    description="실시간 웹 정보를 검색합니다. 실시간 정보가 필요하다면 이 도구를 사용해주세요.",
)


def create_my_tool(
    pdf_path: str,
    vector_persist_path: str,
    tool_name: str,
    tool_description: str,
) -> Tool:
    loader = TextLoader(pdf_path)
    docs_agree = loader.load_and_split(text_splitter)

    vector_db = Chroma.from_documents(
        documents=docs_agree,
        embedding=embeddings,
        persist_directory=vector_persist_path,
    )
    retriever = vector_db.as_retriever(search_type="mmr", search_kwargs={"k": 5})
    tool = create_retriever_tool(
        retriever,
        name=tool_name,
        description=tool_description,
    )
    return tool


agree_retriever_tool = create_my_tool(
    pdf_path="../../data/의대증원찬성.txt",
    vector_persist_path=".vector.docs.agree",
    tool_name="agree document search",
    tool_description="의대 증원 찬성에 대한 문서 입니다. 의대 확장 반대에 대한 반박을 제시하고자 할 때 이 문서를 참고하십시오.",
)
disagree_retriever_tool = create_my_tool(
    pdf_path="../../data/의대증원반대.txt",
    vector_persist_path=".vector.docs.disagree",
    tool_name="disagree document search",
    tool_description="의대 증원 반대에 대한 문서 입니다. 의대 확장론자들에게 반박의견을 제시하고자 할 때 이 문서를 참고하십시오.",
)


the_agents = {
    "의사 증원 찬성론자": [agree_retriever_tool, search_tool],
    "의사 증원 반대": [disagree_retriever_tool, search_tool],
}
topic = "대한민국 의학 대학교 증원 확대가 필요할까요?"
word_limit = 50
