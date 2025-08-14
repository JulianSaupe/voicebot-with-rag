"""FastAPI application using hexagonal architecture."""

from fastapi import FastAPI, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.internal.container import container


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="VoiceBot API",
        description="API for streaming audio responses from the VoiceBot using Hexagonal Architecture"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    voicebot_controller = container.get_voicebot_controller()

    # Register routes
    @app.get("/")
    async def root():
        """Root endpoint to check if the API is running."""
        return {"message": "VoiceBot API is running with Hexagonal Architecture"}

    @app.websocket("/ws/speech")
    async def websocket_transcribe_audio(websocket: WebSocket):
        """WebSocket endpoint for real-time audio transcription."""
        await voicebot_controller.transcribe_audio_websocket(websocket)

    @app.websocket("/ws/text")
    async def websocket_text_input(websocket: WebSocket):
        """WebSocket endpoint for text input with audio response streaming."""
        await voicebot_controller.text_input_websocket(websocket)

    return app


# Create the app instance
app = create_app()
