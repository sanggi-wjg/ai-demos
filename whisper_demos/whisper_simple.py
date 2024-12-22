import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model_id = "openai/whisper-large-v3-turbo"
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id,
    torch_dtype=torch_dtype,
    low_cpu_mem_usage=True,
    use_safetensors=True,
)
model.to(device)

processor = AutoProcessor.from_pretrained(model_id)
pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device=device,
)

audio_files = [
    # "output.mp3",
    "track/12.mp3",
]
generate_kwargs = {
    # "max_new_tokens": 448,
    # "num_beams": 1,
    # "condition_on_prev_tokens": False,
    # "compression_ratio_threshold": 1.35,  # zlib compression ratio threshold (in token space)
    # "temperature": (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
    # "logprob_threshold": -1.0,
    # "no_speech_threshold": 0.6,
    "return_timestamps": True,
    "language": "korean",
}
output = pipe(audio_files, batch_size=len(audio_files), generate_kwargs=generate_kwargs)
print(output)
