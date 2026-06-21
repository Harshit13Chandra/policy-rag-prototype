from sqlalchemy.orm import Session
from app.models.message import Message, MessageCitation
from app.models.chunk import Chunk

class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, conversation_id: str, role: str, content: str) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_by_conversation(self, conversation_id: str) -> list[Message]:
        return self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()

    def get_recent_by_conversation(self, conversation_id: str, limit: int = 10) -> list[Message]:
        # Fetch the most recent N messages in DESC order, then reverse to return them in ASC order
        messages = self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(limit).all()
        messages.reverse()
        return messages

    def create_citations(self, message_id: str, citations: list[dict]) -> None:
        for cit in citations:
            vector_id = cit.get("vector_id")
            score = cit.get("score")
            rank = cit.get("rank")
            
            if not vector_id:
                continue
                
            # Look up the chunk's actual DB ID using the Qdrant vector_id
            chunk = self.db.query(Chunk).filter(Chunk.vector_id == vector_id).first()
            if chunk:
                message_citation = MessageCitation(
                    message_id=message_id,
                    chunk_id=chunk.id,
                    similarity_score=score,
                    rank=rank
                )
                self.db.add(message_citation)
                
        self.db.commit()
