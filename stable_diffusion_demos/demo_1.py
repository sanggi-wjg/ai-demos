import os
import uuid

import torch
from PIL import Image
from diffusers import StableDiffusion3Pipeline, DPMSolverMultistepScheduler
from dotenv import load_dotenv
from huggingface_hub import TextToImageTargetSize, InferenceClient

load_dotenv()
HUGGING_FACE_ACCESS_TOKEN = os.getenv("HUGGING_FACE_ACCESS_TOKEN")

torch.backends.mps.enable_fallback_implementations = True

pipe = StableDiffusion3Pipeline.from_pretrained(
    "stabilityai/stable-diffusion-3.5-medium",
    torch_dtype=torch.bfloat16,
    token=HUGGING_FACE_ACCESS_TOKEN,
    local_files_only=True,
    add_prefix_space=True,
    safety_checker=None,
)
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
# pipe = pipe.to("cuda")
# pipe = pipe.to("mps")

# _client.py.text_to_image()
image = pipe(
    "Black-and-white photography of an elegant woman with soft orange paint brush strokes on her face, minimalist in style, with a bold orange circle behind her head --ar 4:3 --v 6.1 --style raw",
    # "A capybara holding a sign that reads Hello World",
    width=512,
    height=512,
    # num_inference_steps=28,
    # guidance_scale=3.5,
    num_inference_steps=40,
    guidance_scale=4.5,
).images[0]
image.save(image_filename := f"{uuid.uuid4()}.png")
print("Image saved to", image_filename)
