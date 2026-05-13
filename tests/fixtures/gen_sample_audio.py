import struct
import wave
from pathlib import Path


def generate_silent_wav(path: str, duration_ms: int = 1000, sample_rate: int = 16000):
    num_samples = int(sample_rate * duration_ms / 1000)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{num_samples}h", *([0] * num_samples)))


if __name__ == "__main__":
    fixture_path = Path(__file__).resolve().parent / "sample-speech.wav"
    generate_silent_wav(str(fixture_path))
