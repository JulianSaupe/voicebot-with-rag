from dotenv import load_dotenv
import asyncio
import numpy as np
import sounddevice as sd
import threading
import time

from app.llm.gemini import Gemini
from app.llm.prompt_builder import PromptBuilder
from app.pipeline.async_pipeline import AsyncPipeline
from app.pipeline.pipeline_calls import RAGStageCall, LLMStageCall, TTSStageCall
from app.pipeline.stages.llm_stage import LLMStage
from app.pipeline.stages.rag_stage import RAGStage
from app.pipeline.stages.tts_stage import TTSStage
from app.rag.postgres_db import PostgresVectorDB


class ContinuousAudioPlayer:
    def __init__(self, samplerate=24000, chunk_size=1024):
        self.samplerate = samplerate
        self.chunk_size = chunk_size
        self.audio_queue = asyncio.Queue()
        self.is_playing = False
        self.stream = None
        self.audio_buffer = np.array([], dtype=np.float32)
        self.buffer_lock = threading.Lock()
        self.is_finished_adding = False
        self.callback_count = 0
        self.first_audio_played = False

    async def start_playing(self):
        """Start continuous audio stream."""
        self.is_playing = True

        # Start the audio stream
        try:
            self.stream = sd.OutputStream(
                samplerate=self.samplerate,
                channels=1,
                dtype=np.float32,
                callback=self._audio_callback,
                blocksize=self.chunk_size,
                latency='low'
            )
            self.stream.start()
            print(f"🔊 Audio stream started: {self.samplerate}Hz, {self.chunk_size} samples per block")
            
        except Exception as e:
            print(f"Failed to start audio stream: {e}")
            raise

        return asyncio.create_task(self._feed_audio())

    async def add_audio(self, audio_data):
        """Add audio data to the queue."""
        await self.audio_queue.put(audio_data)

    async def finish_adding(self):
        """Signal that no more audio will be added."""
        self.is_finished_adding = True
        await self.audio_queue.put(None)

    async def stop(self):
        """Stop the audio player."""
        self.is_playing = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            print(f"🔊 Audio stream stopped. Total callbacks: {self.callback_count}")

    def get_buffer_duration(self):
        """Get the duration of audio remaining in buffer."""
        with self.buffer_lock:
            return len(self.audio_buffer) / self.samplerate

    def _audio_callback(self, outdata, frames, time, status):
        """Audio callback for continuous playback."""
        self.callback_count += 1
        
        if status:
            print(f"⚠️  Audio callback status: {status}")

        with self.buffer_lock:
            buffer_size = len(self.audio_buffer)
            if buffer_size >= frames:
                # We have enough data
                outdata[:, 0] = self.audio_buffer[:frames]
                self.audio_buffer = self.audio_buffer[frames:]
                
                # Mark first audio as played
                if not self.first_audio_played:
                    self.first_audio_played = True
                    print("🎵 First audio chunk is now playing!")
                    
            else:
                # Not enough data, fill with zeros (silence)
                if buffer_size > 0:
                    outdata[:buffer_size, 0] = self.audio_buffer
                    outdata[buffer_size:, 0] = 0
                    self.audio_buffer = np.array([], dtype=np.float32)
                else:
                    outdata[:, 0] = 0

    async def _feed_audio(self):
        """Feed audio data to the buffer."""
        while self.is_playing:
            try:
                audio_data = await self.audio_queue.get()
                if audio_data is None:
                    print("🔊 No more audio data, feed_audio stopping")
                    break

                # Convert to float32 and add to buffer
                audio_float = audio_data.astype(np.float32) / 32768.0

                with self.buffer_lock:
                    old_buffer_size = len(self.audio_buffer)
                    self.audio_buffer = np.concatenate([self.audio_buffer, audio_float])
                    
                    # Show when we get the first audio
                    if old_buffer_size == 0 and len(audio_float) > 0:
                        print(f"🎵 First audio chunk received! Buffer: {len(self.audio_buffer)} samples ({len(self.audio_buffer) / self.samplerate:.1f}s)")

                # Show buffer status occasionally
                if len(self.audio_buffer) % 50000 < len(audio_float):
                    print(f"🔊 Buffer: {len(self.audio_buffer)} samples ({len(self.audio_buffer) / self.samplerate:.1f}s)")

            except Exception as e:
                print(f"Audio feed error: {e}")
                break


async def main():
    load_dotenv()

    prompt = "Erkläre was AI ist und gebe einige Beispiele wann uns KI im Alltag begegnet"
    task_description = ("Du bist ein KI Agent, welcher kurze Antworten auf Fragen von den Nutzer geben kann."
                        "Gebe nur ganze Sätze wieder, welche mit Hilfe von TTS an den Benutzer ausgegeben werden."
                        "Um die Fragen besser beantworten zu können, wird unter 'Kontext' weiterer Kontext bereitgestellt."
                        "Die Frage des Nutzers ist unter 'Frage' gegeben.")

    # Initialize components
    llm = Gemini()
    vector_db = PostgresVectorDB(llm)
    rag_stage = RAGStage(embedding_calculator=llm, vector_db=vector_db)
    llm_stage = LLMStage(llm=llm, prompt_builder=PromptBuilder(task_description))
    tts_stage = TTSStage(voice_name="de-DE-Chirp3-HD-Charon", language_code="de-DE")

    # Create pipeline with TTS stage
    pipeline = AsyncPipeline(stages=[rag_stage, llm_stage, tts_stage])

    # Start audio player BEFORE starting the pipeline
    audio_player = ContinuousAudioPlayer(samplerate=24000, chunk_size=512)
    player_task = await audio_player.start_playing()

    try:
        print("🤖 Starting AI Response with real-time streaming...")
        print("=" * 50)

        # Get audio stream from pipeline
        audio_stream = pipeline.run(RAGStageCall(prompt=prompt))

        # Process audio chunks as they come from the pipeline - this starts immediately!
        chunk_count = 0
        total_samples = 0
        start_time = time.time()
        
        try:
            async for audio_chunk in audio_stream:
                chunk_count += 1
                total_samples += len(audio_chunk)
                
                # Add audio immediately to the player
                await audio_player.add_audio(audio_chunk)
                
                # Show timing info for first few chunks
                if chunk_count <= 5:
                    elapsed = time.time() - start_time
                    print(f"📥 Chunk {chunk_count} after {elapsed:.1f}s: {len(audio_chunk)} samples")
                elif chunk_count % 20 == 0:
                    elapsed = time.time() - start_time
                    print(f"📥 Received {chunk_count} chunks after {elapsed:.1f}s...")
                    
        except Exception as e:
            print(f"Error in audio stream processing: {e}")
            import traceback
            traceback.print_exc()

        generation_time = time.time() - start_time
        print(f"\n🎵 Generation complete in {generation_time:.1f}s!")
        print(f"🎵 Total: {chunk_count} chunks, {total_samples} samples ({total_samples/24000:.1f}s of audio)")
        print("=" * 50)

        # Signal that we're done adding audio
        await audio_player.finish_adding()

        # Wait for the feed_audio task to complete
        print("⏳ Waiting for audio feed to complete...")
        await player_task
        
        # Now wait for the audio buffer to drain completely
        print("⏳ Waiting for remaining audio to play...")
        while True:
            remaining = audio_player.get_buffer_duration()
            if remaining <= 0.0:
                break
            print(f"⏳ Buffer remaining: {remaining:.1f}s")
            await asyncio.sleep(1.0)

        # Give a little extra time for the audio system
        await asyncio.sleep(1.0)
        
        total_time = time.time() - start_time
        print(f"🔊 Complete! Total time: {total_time:.1f}s")

    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await audio_player.stop()
        print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())