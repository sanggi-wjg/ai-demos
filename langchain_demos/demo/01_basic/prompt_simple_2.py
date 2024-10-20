from pprint import pprint

from langchain.chains.llm import LLMChain
from langchain.chains.sequential import SequentialChain
from langchain.globals import set_debug, set_verbose
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import (
    StrOutputParser,
)
from langchain_core.prompts import ChatPromptTemplate


world_view_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You have a remarkable ability to create a world-building that rivals Steven Spielberg. Please create a world view of the given topic.",
        ),
        ("human", "{topic_of_story}"),
    ]
)

story_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You have a remarkable ability to create a story that rivals Steven Spielberg. Please create a story based on the world view.",
        ),
        ("human", "{world_view}"),
    ]
)

character_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You have a remarkable ability to create a character that rivals Steven Spielberg. Please create character based on the story with world view given.",
        ),
        ("human", "{world_view}\n\n{story}"),
    ]
)


translate_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Translate the given texts to Korean."),
        ("human", "{world_view}\n\n{story}\n\n{character}"),
    ]
)

llm = ChatOllama(model="llama3.1", temparature=0.5)


world_view_prompt_chain = LLMChain(
    llm=llm, prompt=world_view_prompt, output_key="world_view", output_parser=StrOutputParser()
)
story_prompt_chain = LLMChain(llm=llm, prompt=world_view_prompt, output_key="story", output_parser=StrOutputParser())
character_prompt_chain = LLMChain(
    llm=llm, prompt=character_prompt, output_key="character", output_parser=StrOutputParser()
)
translate_prompt_chain = LLMChain(
    llm=llm, prompt=translate_prompt, output_key="translated", output_parser=StrOutputParser()
)

# set_debug(True)
chain = SequentialChain(
    chains=[world_view_prompt_chain, story_prompt_chain, character_prompt_chain, translate_prompt_chain],
    input_variables=["topic_of_story"],
    output_variables=["world_view", "story", "character", "translated"],
    # verbose=True,
    # return_all=True,
)
res = chain.invoke({"topic_of_story": "백엔드 개발자의 세계정복 이야기"})
pprint(res)
