# LangServe

```shell
pip install "langserve[server]" langchain-cli

langchain app new demoapp     
```

```python
from langchain_demos.llama31.example.memory.conversation_buffer_simple import chain as conversation_chain

...

add_routes(app, conversation_chain, path="/demo")
```

http://localhost:8000/demo/playground/ 접속

## Ref

* https://python.langchain.com/docs/langserve
