import os
import time
import uuid

import torch
from diffusers import StableDiffusion3Pipeline, DPMSolverMultistepScheduler
from dotenv import load_dotenv

load_dotenv()
HUGGING_FACE_ACCESS_TOKEN = os.getenv("HUGGING_FACE_ACCESS_TOKEN")

torch.backends.mps.enable_fallback_implementations = True
print(f"Starting inference... ${time.time()}")

pipe = StableDiffusion3Pipeline.from_pretrained(
    "stabilityai/stable-diffusion-3.5-large",
    torch_dtype=torch.bfloat16,
    token=HUGGING_FACE_ACCESS_TOKEN,
    local_files_only=True,
    add_prefix_space=True,
    safety_checker=None,
)
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe = pipe.to("mps")  # cuda
# pipe.enable_attention_slicing()


# prompt = "A capybara holding a sign that reads Hello World"
prompt = "A hamster holding a sign that reads Hello World"

image = pipe(
    prompt,
    width=512,
    height=512,
    num_inference_steps=28,
    guidance_scale=3.5,
    # num_inference_steps=28,
    # guidance_scale=9.0,
).images[0]
image.save(image_filename := os.path.join("images", f"{uuid.uuid4()}.png"))
print("Image saved to", image_filename)
print(f"Finished inference... ${time.time()}")
