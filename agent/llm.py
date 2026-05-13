from livekit.agents.llm import LLM

from config import Settings


def create_llm(settings: Settings) -> LLM:
    provider = settings.LLM_PROVIDER
    model = settings.LLM_MODEL

    if provider == "ollama":
        from livekit.plugins import openai as openai_llm
        return openai_llm.LLM(
            base_url=settings.LLM_BASE_URL or "http://localhost:11434/v1",
            model=model,
            api_key="not_required",
        )

    elif provider == "openai_compatible":
        from livekit.plugins import openai as openai_llm
        return openai_llm.LLM(
            base_url=settings.LLM_BASE_URL,
            model=model,
            api_key="not_required",
        )

    raise ValueError(f"Unknown LLM provider: {provider}")
