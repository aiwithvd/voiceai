# Voice AI Demo — Agent Instructions

## Architecture

Two services: **Python agent** (FastAPI + LiveKit Agent Worker in background thread) and **Next.js frontend**. One `.env` file at project root drives all config.

Startup order: LiveKit Docker → Ollama → Agent → Frontend.

## Commands

```bash
# Agent (run from repo root)
cd agent && pip install --break-system-packages -r requirements.txt && python main.py
python main.py --test-mode     # stubs real STT/LLM/TTS for CI

# Frontend
cd frontend && npm install && npm run dev

# Tests
cd agent && python -m pytest tests/ -v                     # 15 tests
cd agent && PYTHONPATH=. python -m pytest ../tests/ -v     # pipeline + E2E
cd frontend && npm test                                    # 4 tests (vitest)
```

## Gotchas

- `livekit-api` (not `livekit-server-sdk`) — the old package was deleted from PyPI
- `--break-system-packages` required on macOS (PEP 668 homebrew protection)
- First agent run downloads Whisper model (~3GB) — subsequent runs are instant
- `agent/main.py` is the single entrypoint — it starts uvicorn + agent worker thread (`threading.Thread(target=run_worker, daemon=True)`)
- Tests in `tests/` (root level) need `PYTHONPATH=.` to import from `agent/` package
- `conftest.py` inside agent tests intentionally empty — env vars set in `test_main.py` at module level
- Env var `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` must be set (or in `.env`) for any `Settings()` instantiation
- `agent/agent.py` instantiates `settings = Settings()` at module import time — importing it without env vars will crash
- `openai_compatible` STT/LLM/TTS providers require `*_BASE_URL` in `.env` — validated on startup

## Config File

`.env` at repo root. Only `.env.example` is tracked. Copy it to get started. All model choices (STT/LLM/TTS provider, model name, base URL) are runtime configurable.

## Frontend

- Next.js 15 App Router, React 19, Tailwind CSS 4
- LiveKit Agents UI components from shadcn registry (`npx shadcn@latest add @agents-ui/...`)
- `@` path alias → project root (configured in `vitest.config.ts` for tests, `tsconfig.json` for Next.js)
- `POSTCSS`, `@tailwindcss/postcss` plugin required (in `postcss.config.mjs`)
- Vitest with jsdom environment for component tests

## Git

- Remote: `git@aiwithvd:aiwithvd/voiceai.git` (SSH host alias, not `github.com`)
- SSH config: `~/.ssh/config` has `Host aiwithvd` with `HostName github.com` + `IdentityFile ~/.ssh/aiwithvd`

## Test Mode

`--test-mode` flag loads `tests/fixtures/stubs.py` (FakeSTT, FakeLLM, FakeTTS) instead of real model factories. No model downloads or GPU needed.
