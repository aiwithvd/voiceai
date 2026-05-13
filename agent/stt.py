from livekit import rtc
from livekit.agents import APIConnectOptions, NotGivenOr, NOT_GIVEN
from livekit.agents.stt import STT, STT as BaseSTT, StreamAdapter, SpeechEvent, SpeechEventType, SpeechData
from livekit.plugins import silero

from config import Settings


def create_stt(settings: Settings) -> STT:
    provider = settings.STT_PROVIDER
    model = settings.STT_MODEL

    if provider == "whisper":
        from faster_whisper import WhisperModel
        import numpy as np

        class LocalWhisperSTT(BaseSTT):
            def __init__(self, model_size: str = "large-v3-turbo"):
                super().__init__(capabilities={"streaming": False})
                self._model = WhisperModel(
                    model_size,
                    device="auto",
                    compute_type="int8",
                )

            async def _recognize_impl(
                self,
                buffer: rtc.AudioFrame | list[rtc.AudioFrame],
                *,
                language: NotGivenOr[str] = NOT_GIVEN,
                conn_options: APIConnectOptions,
            ) -> SpeechEvent:
                audio_frame = rtc.combine_audio_frames(buffer)
                audio_array = (
                    np.frombuffer(audio_frame.data, dtype=np.int16).astype(np.float32) / 32768.0
                )
                segments, _ = self._model.transcribe(audio_array, beam_size=5)
                text = " ".join(seg.text for seg in segments)
                return SpeechEvent(
                    type=SpeechEventType.FINAL_TRANSCRIPT,
                    alternatives=[SpeechData(language="en", text=text)],
                )

        base_stt = LocalWhisperSTT(model_size=model)
        vad = silero.VAD.load()
        return StreamAdapter(stt=base_stt, vad=vad)

    elif provider == "openai_compatible":
        from livekit.plugins import openai as openai_stt
        base_stt = openai_stt.STT(
            base_url=settings.STT_BASE_URL,
            model=model,
            api_key="not_required",
        )
        vad = silero.VAD.load()
        return StreamAdapter(stt=base_stt, vad=vad)

    raise ValueError(f"Unknown STT provider: {provider}")
