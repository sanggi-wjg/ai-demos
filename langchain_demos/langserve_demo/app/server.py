from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes

import chains

app = FastAPI()


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


add_routes(app, chains.ChatOllama(model="llama3.1"), path="/llama")
add_routes(app, chains.ChatOllama(model="benedict/linkbricks-llama3.1-korean:8b"), path="/llama-korean")
# add_routes(app, chains.llama_32, path="/llama-32")

add_routes(app, chains.simple_chain(), path="/simple")
add_routes(app, chains.simple_groq_chain(), path="/simple-groq")
add_routes(app, chains.joke_of_topic_chain(), path="/joke")

add_routes(app, chains.simple_rag_chain(), path="/rag")
add_routes(app, chains.simple_story_chain(), path="/story")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8090)
