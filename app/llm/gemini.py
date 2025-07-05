from app.llm.llm_provider import LLMProvider
from dotenv import load_dotenv
from google import genai


class Gemini(LLMProvider):
    def __init__(self):
        load_dotenv()
        self.client = genai.Client()

    def generate_stream(self, prompt: str):
        return self.client.models.generate_content_stream(model="gemini-2.0-flash", contents=prompt)
