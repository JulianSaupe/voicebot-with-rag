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
vector_db = PostgresVectorDB(llm)
rag_stage = RAGStage(embedding_calculator=llm, vector_db=vector_db)
llm_stage = LLMStage(llm=llm, prompt_builder=PromptBuilder(
    "Du bist ein KI Agent, welcher Antworten auf Fragen von den Nutzer geben kann."
    "Rege den Nutzer am Ende deiner Antwort an weitere Fragen zu stellen und mache dazu einige Vorschläge."
    "Gebe nur ganze Sätze wieder, welche mit Hilfe von TTS an den Benutzer ausgegeben werden."
    "Um die Fragen besser beantworten zu können, wird unter 'Kontext' weiterer Kontext bereitgestellt."
    "Die Frage des Nutzers ist unter 'Frage' gegeben."
))
tts_stage = TTSStage(voice_name="de-DE-Chirp3-HD-Charon", language_code="de-DE")

# Create pipeline with TTS stage
pipeline = AsyncPipeline(stages=[rag_stage, llm_stage, tts_stage])


async def audio_generator(prompt: str):
    """Generate audio chunks from the pipeline."""
    try:
        # Get audio stream from pipeline
        audio_stream = pipeline.run(RAGStageCall(prompt=prompt))

        # Process audio chunks as they come from the pipeline
        chunk_count = 0
        total_samples = 0
        start_time = time.time()

        async for audio_chunk in audio_stream:
            chunk_count += 1
            total_samples += len(audio_chunk)

            # Convert numpy array to bytes
            audio_bytes = audio_chunk.tobytes()

            # Yield the audio chunk as bytes
            yield audio_bytes

            # Small delay to prevent overwhelming the client
            await asyncio.sleep(0.01)

        print(f"\n🎵 Generation complete in {time.time() - start_time:.1f}s!")
        print(f"🎵 Total: {chunk_count} chunks, {total_samples} samples ({total_samples / 24000:.1f}s of audio)")

    except Exception as e:
        print(f"Error in audio stream processing: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audio")
async def get_audio_stream(prompt: str = Query(..., description="The prompt to generate audio for")):
    """
    Stream audio response for a given prompt.
    
    The audio is streamed as raw PCM int16 data that can be played by the frontend.
    """
    return StreamingResponse(
        audio_generator(prompt),
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
