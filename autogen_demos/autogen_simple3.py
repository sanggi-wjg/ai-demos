from autogen import ConversableAgent

config_list = [
    {
        "model": "exaone3.5",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    }
]

# anti_orm_agent = ConversableAgent(
#     "anti_orm_agent",
#     system_message="당신은 'ORM 사용은 안티 패턴이며 예측하지 못한 버그나 동작들이 있어서 사용을 피해야 한다.' 의견을 주장하고 있습니다. 상대방이 ORM 사용을 못하도록 의견을 제시해야 합니다.",
#     llm_config={"config_list": config_list},
#     human_input_mode="NEVER",
# )
#
# yes_orm_agent = ConversableAgent(
#     "yes_orm_agent",
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

junior_developer = ConversableAgent(
    "신입 개발자",
    system_message="나는 당신이 스프링 부트를 공부하려는 신입 개발자로 행동하기를 바랍니다.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
)
senior_developer = ConversableAgent(
    "시니어 개발자",
    system_message="나는 당신이 스프링 부트에 대해서 잘 알고 있는 시니어 개발자로 행동하기를 바랍니다.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
)

result = junior_developer.initiate_chat(
    senior_developer,
    message="스프링 부트 공부하는데 좋은 방법을 알려주세요.",
    max_turns=10,
)
