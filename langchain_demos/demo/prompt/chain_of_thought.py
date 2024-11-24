from simple_func import simple_chat

user_input = """
본부대에서는 영점 사격 훈련을 위해 탄약 총 1000발을 사격장으로 준비했다. 
김상병은 영점사격 1번을 진행했다.
최이병은 영점사격 2번을 진행했다. 

* 영점 사격은 1번 진행시 9발의 탄약을 소비한다.

현재 남아있는 탄약의 수는?
""".strip()

simple_chat(
    user_input=user_input,
    temperature=0,
)
