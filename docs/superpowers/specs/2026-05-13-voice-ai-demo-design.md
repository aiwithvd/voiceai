# Voice AI Demo — Design Spec

**Date:** 2026-05-13
**Status:** Draft

## Overview

A fully self-hosted, open-source conversational voice AI assistant demo running on Apple Silicon. Uses LiveKit for WebRTC media transport, with a local AI pipeline: Silero VAD → Whisper STT → Ollama LLM → Edge-TTS, all configurable via environment variables.

## Architecture

```
Browser (Next.js + Agents UI)
    │ GET http://localhost:8001/token
    ▼
FastAPI Server (port 8001)
    ├── GET /token              → LiveKit JWT
    ├── GET /health             → health check
    └── LiveKit Agent Worker    → voice AI pipeline (background)
            │
            ▼ WebSocket
LiveKit Server (Docker, port 7880-7882)
            │
    ┌───────┴───────┐
    │ Audio In      │ Audio Out
    ▼               ▼
Voice Agent Pipeline (in-process):
    Silero VAD → Whisper STT → Ollama LLM → Edge-TTS
```

## Components

### 1. LiveKit Server (Docker)

- **Image:** `livekit/livekit-server:latest`
- **Ports:** 7880 (TCP, signaling), 7882 (UDP, media), 50000-60000 (UDP, WebRTC)
- **Auth:** API key/secret pair via environment variables
- **Config:** Single-node, no Redis needed for local demo
- **File:** `docker-compose.yml` + `livekit.yaml`

### 2. Voice Agent (Python/FastAPI)

A single Python process with two responsibilities:

**FastAPI server:**
- `GET /token?room=voice-room&identity=user` — generates a LiveKit JWT using `livekit-server-sdk`
- `GET /health` — returns server status

**LiveKit Agent Worker:**
- Registers with LiveKit server as a worker via WebSocket
- On user join: creates an `AgentSession` with the configurable STT → LLM → TTS pipeline
- Uses `livekit-agents` SDK v1.5+

**Pipeline (all configurable via .env):**

| Component | Default Choice | Configurable |
|---|---|---|
| VAD | Silero VAD (open-source) | silero (only option) |
| STT | Whisper via `faster-whisper` (`large-v3-turbo`) | whisper, openai_compatible |
| LLM | Ollama (`llama3.2:3b`), Metal-accelerated | ollama, openai_compatible |
| TTS | Edge-TTS (free, local) | edge-tts, openai_compatible |

**Model configuration via .env:**
```env
# STT
STT_PROVIDER=whisper
STT_MODEL=large-v3-turbo
STT_BASE_URL=

# LLM
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:3b
LLM_BASE_URL=http://localhost:11434/v1

# TTS
TTS_PROVIDER=edge-tts
TTS_MODEL=en-US-AriaNeural
TTS_BASE_URL=

# LiveKit
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

### 3. Frontend (Next.js + Agents UI)

- **Framework:** Next.js 15 (App Router), React 19, Tailwind CSS 4
- **UI Library:** LiveKit Agents UI (shadcn components)
- **Key components:**
  - `AgentSessionProvider` — session context
  - `AgentControlBar` — mic toggle, disconnect
  - `AgentChatTranscript` — conversation transcript
  - `AgentAudioVisualizerBar` — audio visualization
  - `StartAudioButton` — browser autoplay handling
- **Token:** Fetches from `GET http://localhost:8001/token` on page load
- **Port:** 3000
- **Install Agents UI:**
  ```
  npx shadcn@latest registry add @agents-ui
  npx shadcn@latest add @agents-ui/agent-session-view-01
  ```
  This installs components into `components/agents-ui/` as editable source files.
  Lower-level LiveKit React hooks come from `@livekit/components-react` (npm package).

### 4. Ollama (Local LLM Service)

- **Runs natively** on Apple Silicon (Metal GPU acceleration)
- **Exposes** OpenAI-compatible API at `http://localhost:11434/v1`
- **Default model:** `llama3.2:3b` (fast, good quality for conversation)
- **Alternatives:** `qwen2.5:7b`, `mistral`, `phi-4:14b`

## Data Flow

1. User opens `http://localhost:3000` → frontend fetches token from FastAPI
2. Browser connects to LiveKit server via WebRTC using the JWT
3. LiveKit server detects new participant → dispatches job to Agent Worker
4. Agent runs pipeline on each turn:
   - Silero VAD detects speech boundaries
   - Whisper transcribes audio to text
   - Ollama LLM generates response text
   - Edge-TTS synthesizes response to audio
5. Agent audio streams back through LiveKit → browser plays it
6. Transcript updates in `AgentChatTranscript` component

## Project Structure

```
voiceai/
├── docker-compose.yml
├── livekit.yaml
├── .env.example
├── README.md
│
├── agent/
│   ├── main.py              # FastAPI app (token, health)
│   ├── agent.py             # LiveKit agent entrypoint
│   ├── stt.py               # STT factory (whisper, openai_compatible)
│   ├── llm.py               # LLM factory (ollama, openai_compatible)
│   ├── tts.py               # TTS factory (edge-tts, openai_compatible)
│   ├── config.py            # Pydantic settings from .env
│   ├── requirements.txt
│   └── Dockerfile
│
└── frontend/
    ├── app/
    │   ├── page.tsx
    │   ├── layout.tsx
    │   └── globals.css
    ├── components/
    │   └── agents-ui/       # Installed via shadcn CLI
    ├── lib/
    │   └── token.ts         # Token fetch helper
    ├── package.json
    ├── next.config.js
    ├── tsconfig.json
    ├── tailwind.config.ts
    └── components.json
```

## Running the Demo (Startup Order)

1. **LiveKit Server** — `docker compose up -d` (Docker, ports 7880-7882)
2. **Ollama** — `ollama serve` (native process, port 11434) + `ollama pull llama3.2:3b`
3. **Agent** — `python agent/main.py` (FastAPI + Agent Worker, port 8001)
4. **Frontend** — `npm run dev` in `frontend/` (Next.js, port 3000)

The Agent is a **single Python process**: `main.py` starts both the FastAPI server (via uvicorn) and the LiveKit Agent Worker (via `livekit.agents.cli` in a background thread or asyncio task). They share the same process, env vars, and lifecycle.

## Error Handling

- **LiveKit connection failures:** Frontend shows connection status, retries
- **STT/TTS failures:** Agent logs error, sends fallback text response
- **LLM failures:** Agent returns "I'm having trouble processing that" response
- **Token generation failures:** Frontend shows error message, retry button

## Testing Strategy

### Component-Level Tests

**Agent (Python):**

| Test | Type | What it covers |
|---|---|---|
| `tests/agent/test_config.py` | Unit | `.env` parsing, model config validation, provider selection |
| `tests/agent/test_token.py` | Integration | `/token` endpoint returns valid JWT, rejects invalid room/identity |
| `tests/agent/test_pipeline.py` | Integration | Each stage independently: give Whisper a sample audio → check transcription; ping Ollama → check LLM response; feed TTS text → verify audio output |
| `tests/agent/test_factories.py` | Unit | STT/LLM/TTS factory creates correct provider based on config, raises on invalid provider |

**Frontend (Next.js):**

| Test | Type | What it covers |
|---|---|---|
| `frontend/__tests__/token-fetch.test.ts` | Unit | Token fetch helper handles success/error/network failure |
| `frontend/__tests__/page.render.test.tsx` | Component | Page renders without crashing, shows connection states |

### End-to-End Test

| Test | Purpose |
|---|---|
| `tests/e2e/test_voice_roundtrip.py` | Spin up LiveKit server + Agent, connect a simulated client, verify a voice round-trip completes |

The E2E test uses a **fake pipeline** (mock STT/LLM/TTS) to avoid requiring model downloads or GPU during CI. The real models are used only in manual testing.

### Test Fixtures

- `tests/fixtures/sample-speech.wav` — short audio clip for STT tests
- `tests/fixtures/test-config.env` — isolated env vars for config tests
- `tests/fixtures/` — mocked LLM responses

### Running Tests

```bash
# Agent tests
cd agent && python -m pytest tests/

# Frontend tests
cd frontend && npm test

# E2E (requires LiveKit server running)
python -m pytest tests/e2e/
```

### Pipeline Test Mode

The agent supports a `--test-mode` flag that replaces the real STT/LLM/TTS with test stubs. In test mode:
- STT reads from a fixture file
- LLM returns a pre-configured response
- TTS writes to /dev/null

This allows the full pipeline to be tested without any model dependencies.

## Non-Goals (for v1 demo)

- No user authentication/multi-user support
- No conversation persistence (stateless per session)
- No horizontal scaling (single node)
- No telephony integration
- No video/vision support
