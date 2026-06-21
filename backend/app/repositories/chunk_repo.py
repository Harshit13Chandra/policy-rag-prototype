from sqlalchemy.orm import Session
from app.models.chunk import Chunk

class ChunkRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, document_id: str, chunk_index: int, text: str, page_number: int, token_count: int, vector_id: str) -> Chunk:
        chunk = Chunk(
            document_id=document_id,
            chunk_index=chunk_index,
            text=text,
            page_number=page_number,
            token_count=token_count,
            vector_id=vector_id
        )
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def bulk_create(self, chunks_data: list[dict]) -> list[Chunk]:
        chunks = [
            Chunk(
                document_id=data["document_id"],
                chunk_index=data["chunk_index"],
                text=data["text"],
                page_number=data["page_number"],
                token_count=data["token_count"],
                vector_id=data["vector_id"]
            )
            for data in chunks_data
        ]
        self.db.add_all(chunks)
        self.db.commit()
        return chunks

    def get_by_document_id(self, document_id: str) -> list[Chunk]:
        return self.db.query(Chunk).filter(Chunk.document_id == document_id).all()
