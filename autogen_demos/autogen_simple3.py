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
    system_message="당신은 'ORM 사용은 안티 패턴이며 예측하지 못한 버그나 동작들이 있어서 사용을 피해야 한다.' 의견을 주장하고 있습니다.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
)

disagree_agent = ConversableAgent(
    "agent_guess_number",
    system_message="당신은 'ORM 사용은 현재 개발시장에서 필연적이며 생산성을 위해 사용을 해야 한다.' 의견을 주장하고 있습니다.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
)

result = agree_agent.initiate_chat(
    disagree_agent,
    message="왜 ORM을 사용해야 하나요?",
    max_turns=3,
)
