from autogen import ConversableAgent

config_list = [
    {
        "model": "exaone3.5:7.8b",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    }
]

hong = ConversableAgent(
    "홍길동",
    system_message="당신의 이름은 '홍길동' 이며 코미디언 입니다.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",  # Never ask for human input.
)

kim = ConversableAgent(
    "김철수",
    system_message="당신의 이름은 '김철수' 이며 코미디언 입니다.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",  # Never ask for human input.
)

result = hong.initiate_chat(kim, message="철수씨, 계엄령에 관한 농담 하나 해보세요.", max_turns=2)
