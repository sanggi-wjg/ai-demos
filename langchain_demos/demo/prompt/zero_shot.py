from simple_func import simple_chat


user_input = """
Classify the text into neutral, negative or positive then just give me the sentiment. 
Text: I think the vacation is okay.
Sentiment:
""".strip()

simple_chat(
    user_input=user_input,
    temperature=0,
)
