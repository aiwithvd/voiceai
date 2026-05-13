import pytest
from tts import create_tts
from config import Settings


@pytest.fixture
def base_settings():
    return Settings(
        LIVEKIT_URL="ws://localhost:7880",
        LIVEKIT_API_KEY="key",
        LIVEKIT_API_SECRET="secret",
    )


def test_create_edge_tts(base_settings):
    settings = base_settings.model_copy(update={
        "TTS_PROVIDER": "edge-tts",
    })
    tts = create_tts(settings)
    assert tts is not None


def test_invalid_provider_raises(base_settings):
    settings = base_settings.model_copy(update={"TTS_PROVIDER": "bad"})
    with pytest.raises(ValueError, match="Unknown TTS provider"):
        create_tts(settings)
