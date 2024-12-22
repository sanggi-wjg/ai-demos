import os

from dotenv import load_dotenv
from pyannote.audio import Pipeline

load_dotenv()

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=os.getenv("HUGGING_FACE_ACCESS_TOKEN"),
)
# pipeline.to(torch.device("cuda"))

diarization = pipeline("output.mp3")

for turn, _, speaker in diarization.itertracks(yield_label=True):
    print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
