from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str

    STT_PROVIDER: str = "whisper"
    STT_MODEL: str = "large-v3-turbo"
    STT_BASE_URL: str = ""

    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "llama3.2:3b"
    LLM_BASE_URL: str = ""

    TTS_PROVIDER: str = "edge-tts"
    TTS_MODEL: str = "en-US-AriaNeural"
    TTS_BASE_URL: str = ""

    AGENT_PORT: int = 8001
    AGENT_HOST: str = "0.0.0.0"

    @model_validator(mode="after")
    def validate_providers(self):
        if self.STT_PROVIDER == "openai_compatible" and not self.STT_BASE_URL:
            raise ValueError("STT_BASE_URL required for openai_compatible STT")
        if self.LLM_PROVIDER not in ("ollama", "openai_compatible"):
            raise ValueError(f"Unknown LLM provider: {self.LLM_PROVIDER}")
        if self.LLM_PROVIDER == "openai_compatible" and not self.LLM_BASE_URL:
            raise ValueError("LLM_BASE_URL required for openai_compatible LLM")
        if self.TTS_PROVIDER == "openai_compatible" and not self.TTS_BASE_URL:
            raise ValueError("TTS_BASE_URL required for openai_compatible TTS")
        return self

    model_config = SettingsConfigDict(env_file=".env")
