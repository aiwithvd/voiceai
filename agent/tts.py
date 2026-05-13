from livekit.agents.tts import TTS

from config import Settings


def create_tts(settings: Settings) -> TTS:
    provider = settings.TTS_PROVIDER

    if provider == "edge-tts":
        from edge_tts import Communicate
        from livekit.agents.tts import TTS as LKTTS

        class EdgeTTS(LKTTS):
            def __init__(self, voice: str = "en-US-AriaNeural"):
                super().__init__(
                    capabilities={"streaming": False},
                    sample_rate=24000,
                    num_channels=1,
                )
                self._voice = voice

            async def synthesize(self, text: str) -> bytes:
                communicate = Communicate(text, self._voice)
                audio = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio += chunk["data"]
                return audio

        return EdgeTTS(voice=settings.TTS_MODEL)

    elif provider == "openai_compatible":
        from livekit.plugins import openai as openai_tts

        return openai_tts.TTS(
            base_url=settings.TTS_BASE_URL,
            model=settings.TTS_MODEL,
        )

    raise ValueError(f"Unknown TTS provider: {provider}")
