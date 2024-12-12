import base64
import os.path
from io import BytesIO

from PIL import Image, ImageFile
from langchain_ollama import OllamaLLM, ChatOllama

from langchain_demos.utils.dev import green, magenta, yellow


def convert_to_base64(image: ImageFile.ImageFile) -> str:
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def summarize_image(base64_encoded: str) -> str:
    prompt = """
    You are an assistant tasked with summarizing images for retrieval.
    These summaries will be embedded and used to retrieve the raw image. 
    Give a concise summary of the image that is well optimized for retrieval.
    """.strip()

    llm = OllamaLLM(model="llava")
    return llm.bind(images=[base64_encoded]).invoke(prompt)


if __name__ == '__main__':
    image_filepaths = []
    # image_filepaths = ["../../../data/image.png"]

    for root, _, files in os.walk("../../../data"):
        image_filepaths = [
            os.path.join(root, file)
            for file in files
            if file.endswith(".png") or file.endswith(".jpg") or file.endswith(".jpeg")
        ]

    for filepath in image_filepaths:
        yellow(filepath)
        image_base64 = convert_to_base64(Image.open(filepath))
        summary = summarize_image(image_base64)
        magenta(summary)

        llm = ChatOllama(model="exaone3.5:7.8b", temparature=0)
        result = llm.invoke(f"다음 영어 문장을 한글로 번역해주세요.\nText: ${summary}\nKorean:")
        green(result.content, "\n")
