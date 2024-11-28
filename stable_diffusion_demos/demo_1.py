import os
import time
import uuid
from datetime import datetime

import torch
from diffusers import StableDiffusion3Pipeline, DPMSolverMultistepScheduler
from dotenv import load_dotenv

load_dotenv()
HUGGING_FACE_ACCESS_TOKEN = os.getenv("HUGGING_FACE_ACCESS_TOKEN")

# torch.backends.mps.enable_fallback_implementations = True
print(f"Starting inference... {datetime.now()}")

pipe = StableDiffusion3Pipeline.from_pretrained(
    "stabilityai/stable-diffusion-3.5-large",
    torch_dtype=torch.bfloat16,
    token=HUGGING_FACE_ACCESS_TOKEN,
    local_files_only=True,
    add_prefix_space=True,
    safety_checker=None,
)
# pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe = pipe.to("mps")  # cuda
# pipe.enable_attention_slicing()

# prompt = "A capybara holding a sign that reads Hello World"
# prompt = "The man is shooting a rifle at the computer in front of him"
# prompt = "a cinematic film still, a military combat Mecha, in the middle of snowfield in cold battlefield, lonely mood, cinematic lighting"
# prompt = "happy retriever with smile in the snow"
prompt = "A Russian Blue cat sitting on a chair in front of a laptop, typing or programming with a focused expression. The cat is in a cozy indoor setting with a wooden desk, a coffee cup beside the laptop, and a soft light illuminating the scene"

image = pipe(
    prompt,
    width=512,
    height=512,
    num_inference_steps=28,
    guidance_scale=3.5,
).images[0]
image.save(image_filename := os.path.join("images", f"{uuid.uuid4()}.png"))
print("Image saved to", image_filename, f"Finished inference... {datetime.now()}")
