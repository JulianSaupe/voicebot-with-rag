import asyncio
import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.app.llm.gemini import Gemini
from backend.app.llm.prompt_builder import PromptBuilder
from backend.app.pipeline.async_pipeline import AsyncPipeline
from backend.app.pipeline.pipeline_calls import RAGStageCall
from backend.app.pipeline.stages.llm_stage import LLMStage
from backend.app.pipeline.stages.rag_stage import RAGStage
from backend.app.pipeline.stages.tts_stage import TTSStage
from backend.app.rag.all_mpnet_base_v2 import AllMPNetBaseV2
from backend.app.rag.postgres_db import PostgresVectorDB

# Create FastAPI app
app = FastAPI(title="VoiceBot API", description="API for streaming audio responses from the VoiceBot")

# Add CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components (similar to main.py)
llm = Gemini()
embedding_calculator = AllMPNetBaseV2()
vector_db = PostgresVectorDB(embedding_calculator)
rag_stage = RAGStage(embedding_calculator=llm, vector_db=vector_db)
llm_stage = LLMStage(llm=llm, prompt_builder=PromptBuilder(
    "Du bist ein KI Agent, welcher Antworten auf Fragen von den Nutzer geben kann."
    "Rege den Nutzer am Ende deiner Antwort an weitere Fragen zu stellen und mache dazu einige Vorschläge."
    "Gebe nur ganze Sätze wieder, welche mit Hilfe von TTS an den Benutzer ausgegeben werden."
    "Um die Fragen besser beantworten zu können, wird unter 'Kontext' weiterer Kontext bereitgestellt."
    "Beachte den Kontext nur, wenn dieser auch dazu beiträgt bessere Antworten zu geben."
    "Die Frage des Nutzers ist unter 'Frage' gegeben."
))
tts_stage = TTSStage()

# Create pipeline with TTS stage
pipeline = AsyncPipeline(stages=[rag_stage, llm_stage, tts_stage])


async def audio_generator(prompt: str, voice: str):
    """Generate audio chunks from the pipeline."""
    try:
        # Get audio stream from pipeline
        audio_stream = pipeline.run(RAGStageCall(prompt=prompt, voice=voice))

        # Process audio chunks as they come from the pipeline
        chunk_count = 0
        total_samples = 0
        start_time = time.time()

        # Buffer for combining very small chunks
        buffer = bytearray()
        min_chunk_size = 2048  # Minimum bytes to send (1024 samples)

        async for audio_chunk in audio_stream:
            chunk_count += 1
            total_samples += len(audio_chunk)

            # Convert numpy array to bytes
            audio_bytes = audio_chunk.tobytes()

            # If the chunk is very small, buffer it until we have enough data
            # This helps reduce overhead and improve streaming efficiency
            if len(audio_bytes) < min_chunk_size and len(buffer) < min_chunk_size * 2:
                buffer.extend(audio_bytes)

                # If we still don't have enough data, wait for more chunks
                if len(buffer) < min_chunk_size:
                    continue

                # We have enough data, send the buffered chunk
                yield bytes(buffer)
                buffer = bytearray()
            else:
                # If we have data in the buffer, send it first
                if buffer:
                    buffer.extend(audio_bytes)
                    yield bytes(buffer)
                    buffer = bytearray()
                else:
                    # Send the chunk directly
                    yield audio_bytes

            # No delay between chunks - let the frontend handle buffering
            # This ensures a continuous stream of audio data

        # Send any remaining buffered data
        if buffer:
            yield bytes(buffer)

        print(f"\n🎵 Generation complete in {time.time() - start_time:.1f}s!")
        print(f"🎵 Total: {chunk_count} chunks, {total_samples} samples ({total_samples / 24000:.1f}s of audio)")

    except Exception as e:
        print(f"Error in audio stream processing: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audio")
async def get_audio_stream(
        prompt: str = Query(..., description="The prompt to generate audio for"),
        voice: str = Query("de-DE-Chirp3-HD-Charon", description="The voice to use for TTS")
):
    """
    Stream audio response for a given prompt.

    The audio is streamed as raw PCM int16 data that can be played by the frontend.
    """
    return StreamingResponse(
        audio_generator(prompt, voice),
        media_type="audio/pcm",
        headers={
            "Content-Disposition": "attachment; filename=response.pcm",
            "Sample-Rate": "24000",
            "Channels": "1",
            "Sample-Format": "int16"
        }
    )


@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {"message": "VoiceBot API is running"}
