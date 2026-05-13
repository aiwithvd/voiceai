import pytest
from llm import create_llm
from config import Settings


@pytest.fixture
def base_settings():
    return Settings(
        LIVEKIT_URL="ws://localhost:7880",
        LIVEKIT_API_KEY="key",
        LIVEKIT_API_SECRET="secret",
    )


def test_create_ollama_llm(base_settings):
    settings = base_settings.model_copy(update={
        "LLM_PROVIDER": "ollama",
        "LLM_BASE_URL": "http://localhost:11434/v1",
    })
    llm = create_llm(settings)
    assert llm is not None


def test_create_openai_compatible_llm(base_settings):
    settings = base_settings.model_copy(update={
        "LLM_PROVIDER": "openai_compatible",
        "LLM_BASE_URL": "http://localhost:8080/v1",
    })
    llm = create_llm(settings)
    assert llm is not None


def test_invalid_provider_raises(base_settings):
    settings = base_settings.model_copy(update={"LLM_PROVIDER": "bad"})
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        create_llm(settings)
