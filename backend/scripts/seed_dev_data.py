import sys
import os

# Add the backend root directory to the Python path to allow running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.dependencies import SessionLocal
from app.repositories.user_repo import UserRepository
from app.models.conversation import Conversation
from app.models.message import Message

def main():
    print("Connecting to database...")
    db = SessionLocal()
    
    try:
        user_repo = UserRepository(db)
        email = "test@example.com"
        user = user_repo.get_by_email(email)
        
        if not user:
            print(f"Error: User with email '{email}' not found. Please register this user first.")
            sys.exit(1)
            
        print(f"Found test user: {user.id} ({user.email})")
        
        # Create Conversation
        conversation = Conversation(
            user_id=user.id,
            title="Seed Test Chat"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        print(f"Created Conversation ID: {conversation.id}")
        
        # Create Messages
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content="What is the leave policy?"
        )
        
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content="This is a placeholder answer for seed testing."
        )
        
        db.add_all([user_message, assistant_message])
        db.commit()
        db.refresh(user_message)
        db.refresh(assistant_message)
        
        print(f"Created User Message ID: {user_message.id}")
        print(f"Created Assistant Message ID: {assistant_message.id}")
        print("\nSeed data successfully injected!")

    finally:
        db.close()

if __name__ == "__main__":
    main()
