from autogen import ConversableAgent

config_list = [
    {
        "model": "exaone3.5",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    }
]

agree_agent = ConversableAgent(
    "agent_with_number",
    system_message="당신은 'AI는 인류에게 긍정적인 혁신을 가져올 것이며, 규제로 발전을 저해하지 않고 지원을 통해 기술 발전에 도움을 주어야 한다.' 의견을 주장하고 있습니다.",
    llm_config={"config_list": config_list},
    # is_termination_msg=lambda msg: "53" in msg["content"],
    human_input_mode="NEVER",
)

disagree_agent = ConversableAgent(
    "agent_guess_number",
    system_message="당신은 'AI의 급속한 발전은 심각한 윤리적 위험을 내포하고 있으며, 인간의 일자리와 프라이버시를 위협할 수 있다.' 의견을 주장하고 있습니다.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
)

result = agree_agent.initiate_chat(
    disagree_agent,
    message="왜 AI 기술을 규제해야 하나요?",
)
