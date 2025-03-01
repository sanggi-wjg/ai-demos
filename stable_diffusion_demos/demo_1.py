import os
import uuid
from datetime import datetime

import torch
from diffusers import StableDiffusion3Pipeline
from dotenv import load_dotenv

load_dotenv()
HUGGING_FACE_ACCESS_TOKEN = os.getenv("HUGGING_FACE_ACCESS_TOKEN")

"""
https://prompthero.com/stable-diffusion-cartoon-prompts
"""

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

# prompt = "A hamster holding a sign that reads Hello World"
# prompt = "happy retriever with smile in the snow"
# prompt = """"Cat's Table", A cartoon in the style of John Tenniel, Punch magazine, 1890"""
# prompt = "Marylin monroe full-body shot detailed background in a 50th ambiente in a diner"
prompt = "An imaginative scene of a small white hamster enthusiastically running on a large hamster wheel, generating electricity to power a rack of servers in a server room. Environment is lit with a soft glow from the servers. The servers emit a soft light, The floor is covered in wood shavings."

image = pipe(
    prompt,
    width=512,
    height=512,
    num_inference_steps=50,
    guidance_scale=8.0,
).images[0]
image.save(image_filename := os.path.join("images", f"{uuid.uuid4()}.png"))
print("Image saved to", image_filename, f"Finished inference... {datetime.now()}")
