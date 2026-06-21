import logging
from google import genai
from app.config import get_settings

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model

    def generate_streaming(self, system_instruction: str, user_prompt: str):
        try:
            response_stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=user_prompt,
                config={
                    "system_instruction": system_instruction,
                    "temperature": 0.2
                }
            )
            
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Error during Gemini streaming: {str(e)}")
            yield f"[ERROR: {str(e)}]"

    def generate_once(self, contents: str, config: dict | None = None) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            return response.text
        except Exception as e:
            logger.error(f"Error during Gemini generate_once: {str(e)}")
            raise e
