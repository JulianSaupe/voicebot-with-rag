from typing import AsyncGenerator

from dotenv import load_dotenv
from google import genai

from backend.internal.ports.output.llm_port import LLMPort


class GeminiLLMAdapter(LLMPort):
    """Adapter for Google Gemini LLM service."""

    def __init__(self):
        load_dotenv()
        self.client = genai.Client()

    async def generate_response_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Generate a streaming text response using Gemini LLM."""
        try:
            stream = self.client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=prompt
            )

            for chunk in stream:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            print(f"❌ Error in Gemini streaming text generation: {e}")
            raise RuntimeError(f"LLM streaming text generation failed: {str(e)}")
