from typing import Iterable

from app.llm.llm_provider import LLMProvider
from dotenv import load_dotenv
from google import genai

from app.rag.embedding_calculator import EmbeddingCalculator


class Gemini(LLMProvider, EmbeddingCalculator):
    def __init__(self):
        load_dotenv()
        self.client = genai.Client()

    def generate_stream(self, prompt: str) -> Iterable:
        return self.client.models.generate_content_stream(model="gemini-2.0-flash", contents=prompt)

    def calculate_embeddings(self, text: str):
        return self.client.models.embed_content(model="gemini-2.0-flash", contents=text).embeddings[0]
