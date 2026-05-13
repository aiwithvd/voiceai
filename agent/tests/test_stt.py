import pytest
from stt import create_stt
from config import Settings


@pytest.fixture
def base_settings():
    return Settings(
        LIVEKIT_URL="ws://localhost:7880",
        LIVEKIT_API_KEY="key",
        LIVEKIT_API_SECRET="secret",
    )


@pytest.mark.asyncio
async def test_create_whisper_stt(base_settings):
    settings = base_settings.model_copy(update={"STT_PROVIDER": "whisper"})
    stt = create_stt(settings)
    assert stt is not None


@pytest.mark.asyncio
async def test_create_openai_compatible_stt(base_settings):
    settings = base_settings.model_copy(update={
        "STT_PROVIDER": "openai_compatible",
        "STT_BASE_URL": "http://localhost:8080/v1",
    })
    stt = create_stt(settings)
    assert stt is not None


def test_invalid_provider_raises(base_settings):
    settings = base_settings.model_copy(update={"STT_PROVIDER": "fake_provider"})
    with pytest.raises(ValueError, match="Unknown STT provider"):
        create_stt(settings)
