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

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Get the controller from the container
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

    @app.get("/api/audio")
    async def get_audio_stream(
            prompt: str = Query(..., description="The prompt to generate audio for"),
            voice: str = Query("de-DE-Chirp3-HD-Charon", description="The voice to use for TTS")
    ):
        """Stream audio response for a given prompt."""
        return await voicebot_controller.get_audio_stream(prompt, voice)

    @app.get("/api/text")
    async def get_text_response(
            prompt: str = Query(..., description="The prompt to generate response for"),
            voice: str = Query("de-DE-Chirp3-HD-Charon", description="The voice to use for TTS")
    ):
        """Get text response for a given prompt (non-streaming)."""
        return await voicebot_controller.get_text_response(prompt, voice)

    return app


# Create the app instance
app = create_app()
