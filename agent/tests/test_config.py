import pytest
from config import Settings

def test_requires_livekit_url():
    with pytest.raises(ValueError, match="LIVEKIT_URL"):
        Settings()

def test_defaults_are_correct():
    s = Settings(
        LIVEKIT_URL="ws://localhost:7880",
        LIVEKIT_API_KEY="key",
        LIVEKIT_API_SECRET="secret",
    )
    assert s.STT_PROVIDER == "whisper"
    assert s.LLM_PROVIDER == "ollama"
    assert s.TTS_PROVIDER == "edge-tts"

def test_stt_openai_compatible_requires_base_url():
    with pytest.raises(ValueError, match="STT_BASE_URL"):
        Settings(
            LIVEKIT_URL="ws://localhost:7880",
            LIVEKIT_API_KEY="key",
            LIVEKIT_API_SECRET="secret",
            STT_PROVIDER="openai_compatible",
        )

def test_llm_openai_compatible_requires_base_url():
    with pytest.raises(ValueError, match="LLM_BASE_URL"):
        Settings(
            LIVEKIT_URL="ws://localhost:7880",
            LIVEKIT_API_KEY="key",
            LIVEKIT_API_SECRET="secret",
            LLM_PROVIDER="openai_compatible",
        )
