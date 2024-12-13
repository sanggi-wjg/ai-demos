from autogen import ConversableAgent

config_list = [
    {
        "model": "exaone3.5",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    }
]

# anti_orm_agent = ConversableAgent(
#     "agent_with_number",
#     system_message="당신은 'ORM 사용은 안티 패턴이며 예측하지 못한 버그나 동작들이 있어서 사용을 피해야 한다.' 의견을 주장하고 있습니다. 상대방이 ORM 사용을 못하도록 의견을 제시해야 합니다.",
#     llm_config={"config_list": config_list},
#     human_input_mode="NEVER",
# )
#
# yes_orm_agent = ConversableAgent(
#     "agent_guess_number",
#     system_message="당신은 'ORM 사용은 현재 개발시장에서 필연적이며 생산성을 위해 사용을 해야 한다.' 의견을 주장하고 있습니다. 상대방이 ORM 사용을 하도록 의견을 제시해야 합니다.",
#     llm_config={"config_list": config_list},
#     human_input_mode="NEVER",
# )
#
# result = anti_orm_agent.initiate_chat(
#     yes_orm_agent,
#     message="왜 ORM을 사용해야 하나요?",
#     max_turns=4,
# )
anti_orm_agent = ConversableAgent(
    "agent_with_number",
    system_message="당신은 '테스트 코드 작성은 필요 없다고 생각하며 그 시간에 비지니스 로직 집중이 좋습니다' 의견을 주장하고 있습니다. 상대방이 테스트 코드 작성을 하지 않는 것에 동의하도록 의견을 제시해야 합니다.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
)

yes_orm_agent = ConversableAgent(
    "agent_guess_number",
    system_message="당신은 '테스트 코드 작성은 필요하며 안정적인 서비스를 위해서 테스트 코드는 필연적입니다.' 의견을 주장하고 있습니다. 상대방이 테스트 코드 작성을 동의 하도록 의견을 제시해야 합니다.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
)

result = anti_orm_agent.initiate_chat(
    yes_orm_agent,
    message="왜 테스트 코드 작성을 해야 하나요?",
    max_turns=10,
)
