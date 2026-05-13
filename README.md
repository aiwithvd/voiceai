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
