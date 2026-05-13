import logging

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm as livekit_llm,
    metrics,
)
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero

from config import Settings
from stt import create_stt
from llm import create_llm
from tts import create_tts

logger = logging.getLogger("voice-agent")
settings = Settings()
TEST_MODE = False


def set_test_mode():
    global TEST_MODE
    TEST_MODE = True


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


class SafeSTT:
    def __init__(self, stt):
        self._stt = stt
        self.capabilities = stt.capabilities
        self._fallback_text = "Sorry, I could not understand that."

    def stream(self):
        return self._stt.stream()

    async def recognize(self, audio):
        try:
            return await self._stt.recognize(audio)
        except Exception as e:
            logger.error(f"STT failed: {e}")
            return self._fallback_text


class SafeLLM:
    def __init__(self, llm):
        self._llm = llm
        self._fallback = "I am having trouble processing that. Please try again."

    async def chat(self, chat_ctx):
        try:
            return await self._llm.chat(chat_ctx)
        except Exception as e:
            logger.error(f"LLM failed: {e}")
            return self._fallback

    def chat_stream(self, chat_ctx):
        return self._llm.chat_stream(chat_ctx)


class SafeTTS:
    def __init__(self, tts):
        self._tts = tts

    async def synthesize(self, text: str):
        try:
            return await self._tts.synthesize(text)
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return b""


async def entrypoint(ctx: JobContext):
    initial_ctx = livekit_llm.ChatContext().append(
        role="system",
        text=(
            "You are a helpful voice assistant. "
            "Keep responses concise and conversational."
        ),
    )

    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for {participant.identity}")

    if TEST_MODE:
        logger.info("running in test mode with stubs")
        from tests.fixtures.stubs import FakeSTT, FakeLLM, FakeTTS
        stt = FakeSTT()
        llm = FakeLLM()
        tts = FakeTTS()
    else:
        try:
            raw_stt = create_stt(settings)
            raw_llm = create_llm(settings)
            raw_tts = create_tts(settings)
            stt = SafeSTT(raw_stt)
            llm = SafeLLM(raw_llm)
            tts = SafeTTS(raw_tts)
        except Exception as e:
            logger.error(f"failed to initialize pipeline: {e}")
            await ctx.shutdown()
            return

    agent = Agent(
        instructions="You are a helpful voice assistant. Keep responses concise.",
        chat_ctx=initial_ctx,
    )

    try:
        session = AgentSession(
            vad=ctx.proc.userdata["vad"],
            stt=stt,
            llm=llm,
            tts=tts,
        )
    except Exception as e:
        logger.error(f"failed to create agent session: {e}")
        await ctx.shutdown()
        return

    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(
        instructions="Greet the user and ask how you can help them today."
    )

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(mtrcs: metrics.AgentMetrics):
        metrics.log_metrics(mtrcs)
        usage_collector.collect(mtrcs)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)


def run_worker():
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
