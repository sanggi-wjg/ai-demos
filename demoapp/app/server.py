from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes

from langchain_demos.llama31.example.basic.output_simple import chain2
from langchain_demos.llama31.example.memory.conversation_buffer_simple import chain as conversation_chain

app = FastAPI()


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


add_routes(app, conversation_chain, path="/demo")
add_routes(app, chain2, path="/demo2")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
