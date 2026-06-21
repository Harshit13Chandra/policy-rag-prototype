from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
from app.config import get_settings

class QdrantClientWrapper:
    def __init__(self):
        settings = get_settings()
        # Default to commonly used qdrant properties if they are not yet in settings, but we rely on settings
        self.client = QdrantClient(
            host=getattr(settings, "qdrant_host", "localhost"),
            port=getattr(settings, "qdrant_port", 6333)
        )
        self.collection_name = "policy_chunks"

    def upsert_chunk(self, vector_id: str, vector: list[float], payload: dict) -> None:
        point = PointStruct(
            id=vector_id,
            vector=vector,
            payload=payload
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    def search(self, query_vector: list[float], top_k: int = 20, active_only: bool = True) -> list[dict]:
        query_filter = None
        if active_only:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="is_active",
                        match=MatchValue(value=True)
                    )
                ]
            )
            
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter
        )
        
        return [
            {
                "vector_id": str(res.id),
                "score": res.score,
                "payload": res.payload
            }
            for res in results
        ]

    def mark_inactive(self, vector_id: str) -> None:
        self.client.set_payload(
            collection_name=self.collection_name,
            payload={"is_active": False},
            points=[vector_id]
        )
