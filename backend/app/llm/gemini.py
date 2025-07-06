from typing import Iterable

from dotenv import load_dotenv
from google import genai

from backend.app.llm.llm_provider import LLMProvider
from backend.app.rag.embedding_calculator import EmbeddingCalculator


class Gemini(LLMProvider, EmbeddingCalculator):
    def __init__(self):
        load_dotenv()
        self.client = genai.Client()

    def generate_text_stream(self, prompt: str) -> Iterable:
        stream = self.client.models.generate_content_stream(model="gemini-2.0-flash", contents=prompt)

        for chunk in stream:
            yield chunk.text

    def calculate_embeddings(self, text: str) -> list[float]:
        result = self.client.models.embed_content(model="gemini-embedding-exp-03-07", contents=text).embeddings[0]
        return result.values
