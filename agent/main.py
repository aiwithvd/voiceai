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
        room: str = Query(...),
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
