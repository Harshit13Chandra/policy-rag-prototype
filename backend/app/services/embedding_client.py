import httpx
from app.config import get_settings

class EmbeddingClient:
    def __init__(self):
        settings = get_settings()
        # Default to localhost if not explicitly set in settings
        self.embedding_service_url = getattr(settings, "embedding_service_url", "http://127.0.0.1:8001")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Sends a batch of texts to the embedding service and returns the resulting vector embeddings.
        """
        with httpx.Client(timeout=30.0) as client:
            try:
                response = client.post(
                    f"{self.embedding_service_url}/embed",
                    json={"texts": texts}
                )
                response.raise_for_status()
                return response.json()["embeddings"]
            except httpx.HTTPStatusError as e:
                raise Exception(
                    f"Embedding service returned status {e.response.status_code}: {e.response.text}"
                ) from e
            except httpx.RequestError as e:
                raise Exception(
                    f"Failed to communicate with embedding service: {str(e)}"
                ) from e
