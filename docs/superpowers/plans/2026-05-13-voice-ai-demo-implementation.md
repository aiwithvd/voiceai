# Voice AI Demo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fully self-hosted, open-source conversational voice AI demo on Apple Silicon.

**Architecture:** LiveKit Server (Docker) for WebRTC transport → Python FastAPI + Voice Agent (Silero VAD → Whisper STT → Ollama LLM → Edge-TTS) → Next.js Frontend with Agents UI. All model providers configurable via `.env`.

**Tech Stack:** LiveKit Agents SDK 1.5+, fastapi 0.115+, faster-whisper, ollama, edge-tts, Next.js 15, Agents UI (shadcn), Docker

---

### Task 1: Infrastructure Setup — Docker + LiveKit + Project Scaffolding

**Files:**
- Create: `docker-compose.yml`
- Create: `livekit.yaml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `agent/` directory
- Create: `frontend/` directory
- Create: `tests/` directory

- [ ] **Step 1: Create project root files**

Write `.gitignore`:
```gitignore
__pycache__/
*.pyc
.env
.venv/
node_modules/
.next/
dist/
```

Write `docker-compose.yml`:
```yaml
services:
  livekit-server:
    image: livekit/livekit-server:latest
    container_name: livekit
    restart: unless-stopped
    command: --config /etc/livekit.yaml
    environment:
      LIVEKIT_KEYS: "${LIVEKIT_API_KEY}: ${LIVEKIT_API_SECRET}"
    volumes:
      - ./livekit.yaml:/etc/livekit.yaml
    ports:
      - "7880:7880"
      - "7881:7881"
      - "7882:7882/udp"
```

Write `livekit.yaml`:
```yaml
port: 7880
bind_addresses:
  - "0.0.0.0"
rtc:
  tcp_port: 7881
  udp_port: 7882
  port_range_start: 50000
  port_range_end: 60000
  use_external_ip: false
```

Write `.env.example`:
```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

STT_PROVIDER=whisper
STT_MODEL=large-v3-turbo
STT_BASE_URL=

LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:3b
LLM_BASE_URL=http://localhost:11434/v1

TTS_PROVIDER=edge-tts
TTS_MODEL=en-US-AriaNeural
TTS_BASE_URL=

# Frontend
NEXT_PUBLIC_TOKEN_SERVER=http://localhost:8001
NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880
```

- [ ] **Step 2: Create directory structure**

```bash
mkdir -p agent/tests frontend/{app,components,lib,public} tests/{agent,e2e,fixtures}
```

- [ ] **Step 3: Commit scaffolding**

```bash
git init
git add docker-compose.yml livekit.yaml .env.example
git commit -m "chore: add docker compose, livekit config, env template"
```

---

### Task 2: Agent Config Module

**Files:**
- Create: `agent/config.py`
- Test: `agent/tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Write `agent/tests/test_config.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd agent && pip install pydantic pytest && python -m pytest tests/test_config.py -v`
Expected: Import errors / class not defined

- [ ] **Step 3: Write config module**

Write `agent/config.py`:
```python
from pydantic_settings import BaseSettings
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

    class Config:
        env_file = ".env"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent && python -m pytest tests/test_config.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add agent/config.py agent/tests/test_config.py
git commit -m "feat: add agent config module with pydantic settings"
```

---

### Task 3: STT Factory Module

**Files:**
- Create: `agent/stt.py`
- Test: `agent/tests/test_stt.py`

- [ ] **Step 1: Write failing STT factory tests**

Write `agent/tests/test_stt.py`:
```python
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

def test_create_whisper_stt(base_settings):
    settings = base_settings.model_copy(update={"STT_PROVIDER": "whisper"})
    stt = create_stt(settings)
    assert stt is not None

def test_create_openai_compatible_stt(base_settings):
    settings = base_settings.model_copy(update={
        "STT_PROVIDER": "openai_compatible",
        "STT_BASE_URL": "http://localhost:8080/v1",
    })
    stt = create_stt(settings)
    assert stt is not None

def test_invalid_provider_raises(base_settings):
    from livekit.agents.stt import STT
    settings = base_settings.model_copy(update={"STT_PROVIDER": "fake_provider"})
    with pytest.raises(ValueError, match="Unknown STT provider"):
        create_stt(settings)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd agent && python -m pytest tests/test_stt.py -v`
Expected: Import errors

- [ ] **Step 3: Write STT factory**

Write `agent/stt.py`:
```python
from livekit.agents.stt import STT, StreamAdapter
from livekit.plugins import silero

from config import Settings


def create_stt(settings: Settings) -> STT:
    provider = settings.STT_PROVIDER
    model = settings.STT_MODEL

    if provider == "whisper":
        from faster_whisper import WhisperModel
        from livekit.agents.stt import STT as BaseSTT

        class LocalWhisperSTT(BaseSTT):
            def __init__(self, model_size: str = "large-v3-turbo"):
                super().__init__(capabilities={"streaming": False})
                self._model = WhisperModel(
                    model_size,
                    device="auto",
                    compute_type="float16" if model_size == "large-v3-turbo" else "int8",
                )

            async def _recognize(self, audio):
                import numpy as np
                audio_array = np.frombuffer(audio.data, dtype=np.int16).astype(np.float32) / 32768.0
                segments, _ = self._model.transcribe(audio_array, beam_size=5)
                text = " ".join(seg.text for seg in segments)
                return text

        base_stt = LocalWhisperSTT(model_size=model)
        vad = silero.VAD.load()
        return StreamAdapter(base_stt, vad.stream())

    elif provider == "openai_compatible":
        from livekit.plugins import openai as openai_stt
        base_stt = openai_stt.STT(
            base_url=settings.STT_BASE_URL,
            model=model,
        )
        vad = silero.VAD.load()
        return StreamAdapter(base_stt, vad.stream())

    raise ValueError(f"Unknown STT provider: {provider}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent && python -m pytest tests/test_stt.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add agent/stt.py agent/tests/test_stt.py
git commit -m "feat: add STT factory with whisper and openai-compatible providers"
```

---

### Task 4: LLM Factory Module

**Files:**
- Create: `agent/llm.py`
- Test: `agent/tests/test_llm.py`

- [ ] **Step 1: Write failing LLM factory tests**

Write `agent/tests/test_llm.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd agent && python -m pytest tests/test_llm.py -v`
Expected: Import errors

- [ ] **Step 3: Write LLM factory**

Write `agent/llm.py`:
```python
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
        )

    elif provider == "openai_compatible":
        from livekit.plugins import openai as openai_llm
        return openai_llm.LLM(
            base_url=settings.LLM_BASE_URL,
            model=model,
        )

    raise ValueError(f"Unknown LLM provider: {provider}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent && python -m pytest tests/test_llm.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add agent/llm.py agent/tests/test_llm.py
git commit -m "feat: add LLM factory with ollama and openai-compatible providers"
```

---

### Task 5: TTS Factory Module

**Files:**
- Create: `agent/tts.py`
- Test: `agent/tests/test_tts.py`

- [ ] **Step 1: Write failing TTS factory tests**

Write `agent/tests/test_tts.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd agent && python -m pytest tests/test_tts.py -v`
Expected: Import errors

- [ ] **Step 3: Write TTS factory**

Write `agent/tts.py`:
```python
from livekit.agents.tts import TTS

from config import Settings


def create_tts(settings: Settings) -> TTS:
    provider = settings.TTS_PROVIDER

    if provider == "edge-tts":
        from edge_tts import Communicate
        from livekit.agents.tts import TTS as LKTTS

        class EdgeTTS(LKTTS):
            def __init__(self, voice: str = "en-US-AriaNeural"):
                super().__init__(capabilities={"streaming": False})
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent && python -m pytest tests/test_tts.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add agent/tts.py agent/tests/test_tts.py
git commit -m "feat: add TTS factory with edge-tts and openai-compatible providers"
```

---

### Task 6: Voice Agent Entrypoint

**Files:**
- Create: `agent/agent.py`

- [ ] **Step 1: Write the LiveKit agent entrypoint**

Write `agent/agent.py`:
```python
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
```

- [ ] **Step 2: Commit**

```bash
git add agent/agent.py
git commit -m "feat: add LiveKit voice agent entrypoint with error handling and test mode"
```

---

### Task 7: FastAPI Server (Token + Health)

**Files:**
- Create: `agent/main.py`
- Test: `agent/tests/test_main.py`

- [ ] **Step 1: Write failing server tests**

Write `agent/tests/conftest.py`:
```python
import os

os.environ["LIVEKIT_URL"] = "ws://localhost:7880"
os.environ["LIVEKIT_API_KEY"] = "test-key"
os.environ["LIVEKIT_API_SECRET"] = "test-secret"
```

Write `agent/tests/test_main.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from config import Settings
from main import create_app

@pytest.fixture
def test_settings():
    return Settings(
        LIVEKIT_URL="ws://localhost:7880",
        LIVEKIT_API_KEY="test_key",
        LIVEKIT_API_SECRET="test_secret",
    )

@pytest.mark.asyncio
async def test_health_endpoint(test_settings):
    app = create_app(test_settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"

@pytest.mark.asyncio
async def test_token_endpoint_returns_jwt(test_settings):
    app = create_app(test_settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/token?room=test-room&identity=test-user")
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert len(data["token"]) > 0

@pytest.mark.asyncio
async def test_token_missing_room(test_settings):
    app = create_app(test_settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/token")
    assert resp.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd agent && pip install httpx pytest-asyncio && python -m pytest tests/test_main.py -v`
Expected: Import errors

- [ ] **Step 3: Write FastAPI server**

Write `agent/main.py`:
```python
import argparse
import logging
import threading

import uvicorn
from fastapi import FastAPI, Query
from livekit import api

from config import Settings
from agent import run_worker, set_test_mode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-server")


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title="Voice AI Agent")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/token")
    async def get_token(
        room: str = Query(default="voice-room"),
        identity: str = Query(default="user"),
    ):
        try:
            token = api.AccessToken(
                settings.LIVEKIT_API_KEY,
                settings.LIVEKIT_API_SECRET,
            ).with_grants(api.VideoGrants(
                room_join=True,
                room=room,
            )).with_identity(identity).to_jwt()
            return {"token": token}
        except Exception as e:
            logger.error(f"token generation failed: {e}")
            return {"error": "Failed to generate token"}, 500

    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-mode", action="store_true", help="Run with test stubs")
    args = parser.parse_args()

    if args.test_mode:
        logger.info("starting in test mode")
        set_test_mode()

    settings = Settings()
    app = create_app(settings)

    agent_thread = threading.Thread(target=run_worker, daemon=True)
    agent_thread.start()
    uvicorn.run(app, host=settings.AGENT_HOST, port=settings.AGENT_PORT)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent && python -m pytest tests/test_main.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add agent/main.py agent/tests/test_main.py
git commit -m "feat: add FastAPI server with token and health endpoints"
```

---

### Task 8: Agent Dependencies + Dockerfile

**Files:**
- Create: `agent/requirements.txt`
- Create: `agent/Dockerfile`

- [ ] **Step 1: Write requirements.txt**

Write `agent/requirements.txt`:
```txt
livekit-agents[openai,silero,turn-detector]~=1.5
livekit-server-sdk>=0.9
fastapi>=0.115
uvicorn[standard]>=0.34
pydantic-settings>=2.7
edge-tts>=6.1
httpx>=0.27
faster-whisper>=1.1
numpy>=1.26
```

- [ ] **Step 2: Write Dockerfile**

Write `agent/Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["python", "main.py"]
```

- [ ] **Step 3: Commit**

```bash
git add agent/requirements.txt agent/Dockerfile
git commit -m "chore: add agent dependencies and Dockerfile"
```

---

### Task 9: Frontend — Next.js + Agents UI Scaffolding

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.js`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.mjs`
- Create: `frontend/components.json`
- Create: `frontend/app/globals.css`
- Create: `frontend/app/layout.tsx`

- [ ] **Step 1: Scaffold Next.js project**

Write `frontend/package.json`:
```json
{
  "name": "voice-ai-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "vitest"
  },
  "dependencies": {
    "next": "^15",
    "react": "^19",
    "react-dom": "^19",
    "@livekit/components-react": "^2.9",
    "@livekit/components-styles": "^1.1",
    "livekit-client": "^2.9"
  },
  "devDependencies": {
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "typescript": "^5",
    "tailwindcss": "^4",
    "vitest": "^3",
    "@testing-library/react": "^16",
    "@vitejs/plugin-react": "^4",
    "jsdom": "^25"
  }
}
```

Write `frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

Write `frontend/next.config.js`:
```js
/** @type {import('next').NextConfig} */
const nextConfig = {};
module.exports = nextConfig;
```

Write `frontend/postcss.config.mjs`:
```js
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
export default config;
```

Write `frontend/tailwind.config.ts`:
```ts
import type { Config } from "tailwindcss";
const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: { extend: {} },
  plugins: [],
};
export default config;
```

Write `frontend/components.json`:
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": true,
  "tsx": true,
  "tailwind": { "config": "tailwind.config.ts", "css": "app/globals.css", "baseColor": "neutral", "cssVariables": true },
  "aliases": { "components": "@/components", "utils": "@/lib/utils" },
  "registries": {
    "@agents-ui": "https://livekit.io/ui/r/{name}.json"
  }
}
```

Write `frontend/app/globals.css`:
```css
@import "tailwindcss";
@import "@livekit/components-styles";
```

Write `frontend/app/layout.tsx`:
```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Voice AI Demo",
  description: "Open-source voice assistant",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 2: Install Agents UI components**

```bash
cd frontend && npm install && npx shadcn@latest registry add @agents-ui && npx shadcn@latest add @agents-ui/agent-session-provider @agents-ui/agent-control-bar @agents-ui/agent-chat-transcript @agents-ui/agent-audio-visualizer-bar @agents-ui/start-audio-button
```

- [ ] **Step 3: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold Next.js frontend with Agents UI"
```

---

### Task 10: Frontend — Token Fetch + Main Page

**Files:**
- Create: `frontend/lib/token.ts`
- Create: `frontend/app/page.tsx`
- Test: `frontend/__tests__/token.test.ts`

- [ ] **Step 1: Write failing token fetch test**

Write `frontend/__tests__/token.test.ts`:
```ts
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("fetchToken", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("returns token on success", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ token: "test-jwt-token" }),
    } as Response);

    const { fetchToken } = await import("../lib/token");
    const token = await fetchToken("test-room", "test-user");
    expect(token).toBe("test-jwt-token");
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8001/token?room=test-room&identity=test-user"
    );
  });

  it("throws on HTTP error", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 500,
    } as Response);

    const { fetchToken } = await import("../lib/token");
    await expect(fetchToken("room", "user")).rejects.toThrow("Failed to fetch token");
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run`
Expected: Import errors

- [ ] **Step 3: Write token fetch lib**

Write `frontend/lib/token.ts`:
```ts
const TOKEN_SERVER = process.env.NEXT_PUBLIC_TOKEN_SERVER || "http://localhost:8001";

export async function fetchToken(room: string = "voice-room", identity: string = "user"): Promise<string> {
  const url = `${TOKEN_SERVER}/token?room=${encodeURIComponent(room)}&identity=${encodeURIComponent(identity)}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error("Failed to fetch token");
  const data = await resp.json();
  return data.token;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: All tests PASS

- [ ] **Step 5: Write main page**

Write `frontend/app/page.tsx`:
```tsx
"use client";

import { useEffect, useState, useMemo } from "react";
import { TokenSource, Room } from "livekit-client";
import { useSession, useAgent, useSessionContext, useSessionMessages } from "@livekit/components-react";
import { AgentSessionProvider } from "@/components/agents-ui/agent-session-provider";
import { AgentControlBar } from "@/components/agents-ui/agent-control-bar";
import { AgentChatTranscript } from "@/components/agents-ui/agent-chat-transcript";
import { AgentAudioVisualizerBar } from "@/components/agents-ui/agent-audio-visualizer-bar";
import { StartAudioButton } from "@/components/agents-ui/start-audio-button";
import { fetchToken } from "@/lib/token";

function AgentUI() {
  const session = useSessionContext();
  const agent = useAgent(session);
  const messages = useSessionMessages(session);

  return (
    <div className="flex flex-col items-center gap-6 p-8 min-h-screen bg-black text-white">
      <h1 className="text-2xl font-semibold">Voice AI Demo</h1>

      <div className="w-full max-w-md">
        {agent.audioTrack ? (
          <AgentAudioVisualizerBar
            track={agent.audioTrack}
            state={agent.state}
            barCount={5}
          />
        ) : (
          <div className="h-20 flex items-center justify-center text-gray-400">
            {agent.state === "connecting" ? "Connecting..." : "Press mic to start"}
          </div>
        )}
      </div>

      <AgentChatTranscript messages={messages} agentState={agent.state} />

      <AgentControlBar
        variant="livekit"
        isConnected={session.isConnected}
        controls={{ microphone: true, camera: false, screenShare: false }}
      />

      <StartAudioButton label="Start audio" />
    </div>
  );
}

function VoiceChat({ token }: { token: string }) {
  const tokenSource = useMemo(() => TokenSource.fromToken(token), [token]);
  const session = useSession(tokenSource);

  useEffect(() => {
    session.start();
    return () => { session.end(); };
  }, [session]);

  return (
    <AgentSessionProvider session={session}>
      <AgentUI />
    </AgentSessionProvider>
  );
}

export default function Home() {
  const [token, setToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchToken()
      .then(setToken)
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white gap-4">
        <p className="text-red-400">Failed to connect: {error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-white text-black rounded"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black text-white">
        Connecting to agent...
      </div>
    );
  }

  return <VoiceChat token={token} />;
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/lib/token.ts frontend/__tests__/token.test.ts frontend/app/page.tsx
git commit -m "feat: add frontend main page with Agents UI components"
```

---

### Task 11: Additional Tests

**Files:**
- Test: `frontend/__tests__/page.render.test.tsx`
- Test: `tests/agent/test_pipeline.py`
- Create: `tests/e2e/test_roundtrip.py`
- Create: `tests/fixtures/test-config.env`
- Create: `tests/fixtures/stubs.py`

- [ ] **Step 1: Write page render test**

Write `frontend/__tests__/page.render.test.tsx`:
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@/lib/token", () => ({
  fetchToken: vi.fn().mockRejectedValue(new Error("no server")),
}));

vi.mock("@/components/agents-ui/agent-session-provider", () => ({
  AgentSessionProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@/components/agents-ui/agent-control-bar", () => ({
  AgentControlBar: () => <div data-testid="control-bar" />,
}));

vi.mock("@/components/agents-ui/agent-chat-transcript", () => ({
  AgentChatTranscript: () => <div data-testid="chat-transcript" />,
}));

vi.mock("@/components/agents-ui/agent-audio-visualizer-bar", () => ({
  AgentAudioVisualizerBar: () => <div data-testid="visualizer" />,
}));

vi.mock("@livekit/components-react", () => ({
  useSession: vi.fn(),
  useAgent: vi.fn(),
  useSessionContext: vi.fn(),
  useSessionMessages: vi.fn(),
}));

import Home from "@/app/page";

describe("Home page", () => {
  it("shows connecting state initially", () => {
    render(<Home />);
    expect(screen.getByText(/Connecting to agent/)).toBeTruthy();
  });

  it("shows error state when token fetch fails", async () => {
    render(<Home />);
    const errorMsg = await screen.findByText(/Failed to connect/);
    expect(errorMsg).toBeTruthy();
  });
});
```

- [ ] **Step 2: Create sample audio fixture**

Write `tests/fixtures/gen_sample_audio.py`:
```python
import struct
import wave
from pathlib import Path


def generate_silent_wav(path: str, duration_ms: int = 1000, sample_rate: int = 16000):
    num_samples = int(sample_rate * duration_ms / 1000)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{num_samples}h", *([0] * num_samples)))


if __name__ == "__main__":
    fixture_path = Path(__file__).resolve().parent / "sample-speech.wav"
    generate_silent_wav(str(fixture_path))
```

Run: `python tests/fixtures/gen_sample_audio.py`

- [ ] **Step 3: Write pipeline integration test**

Write `tests/agent/test_pipeline.py`:
```python
import asyncio
import struct
import wave
from pathlib import Path

import pytest
from config import Settings
from stt import create_stt
from llm import create_llm
from tts import create_tts

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


@pytest.fixture
def settings():
    return Settings(
        LIVEKIT_URL="ws://localhost:7880",
        LIVEKIT_API_KEY="test",
        LIVEKIT_API_SECRET="test",
        STT_PROVIDER="whisper",
        STT_MODEL="tiny",
        LLM_PROVIDER="ollama",
        LLM_MODEL="llama3.2:3b",
        LLM_BASE_URL="http://localhost:11434/v1",
        TTS_PROVIDER="edge-tts",
        TTS_MODEL="en-US-AriaNeural",
    )


def test_pipeline_creates_all_components(settings):
    stt = create_stt(settings)
    assert stt is not None
    assert hasattr(stt, "recognize") or hasattr(stt, "stream")

    llm = create_llm(settings)
    assert llm is not None
    assert hasattr(llm, "chat")

    tts = create_tts(settings)
    assert tts is not None
    assert hasattr(tts, "synthesize")


def test_tts_synthesize_returns_bytes(settings):
    tts = create_tts(settings)
    result = asyncio.run(tts.synthesize("Hello world"))
    assert isinstance(result, bytes)
    assert len(result) > 0
```

- [ ] **Step 4: Write test mode stubs**

Write `tests/fixtures/stubs.py`:
```python
class FakeSTT:
    def __init__(self):
        self.capabilities = {"streaming": False}

    async def recognize(self, audio):
        return "this is a test transcription"

    def stream(self):
        return self


class FakeLLM:
    async def chat(self, chat_ctx):
        return "This is a test LLM response."

    def chat_stream(self, chat_ctx):
        class FakeStream:
            def __aiter__(self):
                return self
            async def __anext__(self):
                raise StopAsyncIteration
        return FakeStream()


class FakeTTS:
    async def synthesize(self, text: str):
        import struct
        duration_ms = 1000
        sample_rate = 24000
        num_samples = int(sample_rate * duration_ms / 1000)
        audio_data = struct.pack(f"<{num_samples}h", *([0] * num_samples))
        return audio_data
```

- [ ] **Step 5: Write test config fixture**

Write `tests/fixtures/test-config.env`:
```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
STT_PROVIDER=whisper
STT_MODEL=tiny
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:3b
LLM_BASE_URL=http://localhost:11434/v1
TTS_PROVIDER=edge-tts
TTS_MODEL=en-US-AriaNeural
```

- [ ] **Step 6: Write E2E roundtrip test**

Write `tests/e2e/test_roundtrip.py`:
```python
import pytest
import requests

SERVER_URL = "http://localhost:8001"


@pytest.fixture(scope="module")
def ensure_agent_running():
    try:
        resp = requests.get(f"{SERVER_URL}/health", timeout=3)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
    except (requests.ConnectionError, AssertionError):
        pytest.skip("Agent server not running on port 8001")


def test_health_endpoint(ensure_agent_running):
    resp = requests.get(f"{SERVER_URL}/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_token_generation(ensure_agent_running):
    resp = requests.get(f"{SERVER_URL}/token?room=test-room&identity=e2e-user")
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert isinstance(data["token"], str)
    assert len(data["token"]) > 50
```

- [ ] **Step 7: Commit**

```bash
git add tests/ frontend/__tests__/page.render.test.tsx
git commit -m "test: add pipeline, render, stubs, fixtures, and E2E tests"
```

---

### Task 12: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

Write `README.md`:
```md
# Voice AI Demo

A fully self-hosted, open-source conversational voice AI assistant running on Apple Silicon.

## Architecture

```
Browser (Next.js + Agents UI) → FastAPI (token + agent) → LiveKit Server (Docker)
                                                              ↕
Voice Pipeline: Silero VAD → Whisper STT → Ollama LLM → Edge-TTS
```

## Prerequisites

- Docker (for LiveKit server)
- Python 3.12+
- Node.js 22+
- [Ollama](https://ollama.ai) with a model pulled (`ollama pull llama3.2:3b`)

## Quick Start

### 1. Start LiveKit Server

```bash
cp .env.example .env
docker compose up -d
```

### 2. Start Ollama

```bash
ollama serve
ollama pull llama3.2:3b
```

### 3. Start Agent

```bash
cd agent
pip install -r requirements.txt
python main.py
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Configuration

All model choices are configurable in `.env`. See `.env.example` for all options.

## Testing

```bash
# Agent unit & integration tests
cd agent && python -m pytest tests/ -v

# Root-level pipeline & E2E tests (requires env vars, LiveKit server)
cd agent && PYTHONPATH=. python -m pytest ../tests/ -v

# Frontend tests
cd frontend && npm test
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup instructions"
```
