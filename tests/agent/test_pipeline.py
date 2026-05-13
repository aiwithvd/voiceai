import asyncio
import struct
import wave
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture(scope="module", autouse=True)
def ensure_sample_audio():
    path = FIXTURES_DIR / "sample-speech.wav"
    if not path.exists():
        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        sample_rate = 16000
        duration_ms = 1000
        num_samples = int(sample_rate * duration_ms / 1000)
        with wave.open(str(path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(struct.pack(f"<{num_samples}h", *([0] * num_samples)))
