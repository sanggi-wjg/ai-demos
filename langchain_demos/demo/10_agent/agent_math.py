import uuid
from math import factorial

from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import tool
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_ollama import ChatOllama


@tool
def basic_calculator_tool(query):
    """Basic calculator tool"""
    try:
        return f"The result is {eval(query)}"
    except (SyntaxError, NameError) as e:
        return f"Sorry, I couldn't calculate that due to an error: {e}"


@tool
def equation_solver_tool(query):
    """Equation solver tool"""
    # Basic equation solver (placeholder)
    # Implement specific logic for solving equations
    return "Equation solver: This feature is under development."


@tool
def factorial_calculator_tool(query):
    """Factorial tool"""
    # Implement factorial logic
    try:
        return f"The result is {factorial(int(query))}"
    except ValueError as e:
        return f"Sorry, I couldn't calculate that due to an error: {e}"


def create_math_agent():
    template = """You are specialized in solving math-related questions. Return the answer to the user's question.
    You have access to the following tools.
    **답변은 꼭 한글로 해주세요!**
    
    {tools}
    
    Use the following format:
    
    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question
    
    질문: {input}
    생각: {agent_scratchpad}"""
    prompt = PromptTemplate.from_template(template)
    message_history = ChatMessageHistory()
    tools = [basic_calculator_tool, equation_solver_tool, factorial_calculator_tool]

    llm = ChatOllama(model="llama3.1", temparature=0)

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
    )
    agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor,
        lambda session_id: message_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    return agent_with_chat_history


math_agent = create_math_agent()
user_input = input("유저 입력:")

for token in math_agent.stream(
    {"input": user_input},
    config={"configurable": {"session_id": f"{uuid.uuid4()}"}},
):
    print(token, end="", flush=True)
