import logging
from app.services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class TitleService:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client

    def generate_title(self, first_question: str, first_answer: str) -> str:
        prompt = (
            f"Summarize the following exchange into a concise chat title of 4 to 6 words, no punctuation at the end, "
            f"no quotation marks around it. Just output the title text and nothing else.\n\n"
            f"User question: {first_question}\n\n"
            f"Assistant answer: {first_answer[:300]}"
        )
        
        try:
            result = self.gemini_client.generate_once(
                contents=prompt,
                config={"temperature": 0.3}
            )
            
            if result:
                # Strip whitespace and any surrounding quotes
                title = result.strip().strip('"').strip("'")
            else:
                title = ""
                
            # Fallback if result is empty
            if not title:
                title = first_question[:50] + "..." if len(first_question) > 50 else first_question
                
        except Exception as e:
            logger.error(f"Failed to generate title from Gemini: {str(e)}")
            # Fallback on exception
            title = first_question[:50] + "..." if len(first_question) > 50 else first_question
            
        # Ensure it fits the database column limit (varchar 255)
        return title[:255]
