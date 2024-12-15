import os

import pyaudio
import wave

from pydub import AudioSegment

FORMAT = pyaudio.paInt32
CHANNELS = 1
RATE = 96000
CHUNK = 4096
RECORD_SECONDS = 120
WAV_OUTPUT_FILENAME = "output.wav"
MP3_OUTPUT_FILENAME = "output.mp3"

audio = pyaudio.PyAudio()
stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
)
print("Recording...")

frames = []
for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("Recording finished.")

stream.stop_stream()
stream.close()
audio.terminate()

with wave.open(WAV_OUTPUT_FILENAME, "wb") as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))

print(f"Saved recording to {WAV_OUTPUT_FILENAME}")


sound = AudioSegment.from_wav(WAV_OUTPUT_FILENAME)
sound.export(MP3_OUTPUT_FILENAME, format="mp3")
os.remove(WAV_OUTPUT_FILENAME)
