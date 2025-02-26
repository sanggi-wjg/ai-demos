from autogen import ConversableAgent

config_list = [
    {
        "model": "exaone3.5:7.8b",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    }
]

hong = ConversableAgent(
    "레이너",
    system_message="저는 개발시에 테스트 코드가 필요하다고 생각 합니다.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",  # Never ask for human input.
)

kim = ConversableAgent(
    "로빈",
    system_message="저는 개발시에 테스트 코드가 필요 없다고 생각 합니다.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",  # Never ask for human input.
)

result = hong.initiate_chat(kim, message="테스트가 왜 필요 없죠", max_turns=5)
