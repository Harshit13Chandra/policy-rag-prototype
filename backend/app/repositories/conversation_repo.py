from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.models.conversation import Conversation

class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, title: str = "New Chat") -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            title=title
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_by_id(self, conversation_id: str) -> Conversation | None:
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def get_by_user(self, user_id: str) -> list[Conversation]:
        return self.db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc()).all()

    def update_title(self, conversation_id: str, title: str) -> None:
        conversation = self.get_by_id(conversation_id)
        if conversation:
            conversation.title = title
            self.db.commit()

    def delete(self, conversation_id: str) -> None:
        conversation = self.get_by_id(conversation_id)
        if conversation:
            self.db.delete(conversation)
            self.db.commit()

    def touch_updated_at(self, conversation_id: str) -> None:
        conversation = self.get_by_id(conversation_id)
        if conversation:
            conversation.updated_at = func.now()
            self.db.commit()
