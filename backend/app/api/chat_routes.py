import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.schemas.chat_schema import (
    ConversationCreateResponse,
    ConversationResponse,
    ConversationListResponse,
    MessageResponse,
    MessageListResponse,
    QueryRequest,
    ConversationUpdate
)
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.chunk_repo import ChunkRepository
from app.services.embedding_client import EmbeddingClient
from app.services.vectordb_client import QdrantClientWrapper
from app.services.gemini_client import GeminiClient
from app.services.rag_service import RAGService
from app.services.title_service import TitleService
from app.models.message import MessageCitation
from app.models.chunk import Chunk

router = APIRouter(prefix="/api/v1", tags=["chat"])

@router.post("/conversations", response_model=ConversationCreateResponse, status_code=201)
def create_conversation(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    repo = ConversationRepository(db)
    conv = repo.create(user_id=str(current_user.id))
    return ConversationCreateResponse(id=str(conv.id), title=conv.title)

@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    repo = ConversationRepository(db)
    convs = repo.get_by_user(user_id=str(current_user.id))
    items = [
        ConversationResponse(
            id=str(c.id),
            title=c.title,
            updated_at=c.updated_at,
            is_archived=c.is_archived
        ) for c in convs
    ]
    return ConversationListResponse(items=items)

@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
def list_messages(conversation_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    conv_repo = ConversationRepository(db)
    conv = conv_repo.get_by_id(conversation_id)
    if not conv or str(conv.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    msg_repo = MessageRepository(db)
    messages = msg_repo.get_by_conversation(conversation_id)
    
    response_items = []
    for m in messages:
        citations = []
        if m.role == "assistant":
            # query MessageCitation joined with Chunk
            cits = db.query(MessageCitation, Chunk).join(Chunk, MessageCitation.chunk_id == Chunk.id).filter(MessageCitation.message_id == m.id).all()
            for mc, chunk in cits:
                citations.append({
                    "document_id": str(chunk.document_id),
                    "page_number": chunk.page_number,
                    "score": mc.similarity_score,
                    "rank": mc.rank
                })
                
        response_items.append(MessageResponse(
            id=str(m.id),
            role=m.role,
            content=m.content,
            created_at=m.created_at,
            citations=citations
        ))
        
    return MessageListResponse(items=response_items)

@router.post("/chat/query")
def chat_query(request: QueryRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    conv_repo = ConversationRepository(db)
    conv = conv_repo.get_by_id(request.conversation_id)
    if not conv or str(conv.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    msg_repo = MessageRepository(db)
    
    # Save user message before generating
    msg_repo.create(request.conversation_id, "user", request.question)
    
    # Fetch recent history excluding the current question
    recent_messages = msg_repo.get_recent_by_conversation(request.conversation_id, limit=11)
    
    if recent_messages and recent_messages[-1].role == "user" and recent_messages[-1].content == request.question:
        history_msgs = recent_messages[:-1]
    else:
        history_msgs = recent_messages[:10]
        
    history = [{"role": hm.role, "content": hm.content} for hm in history_msgs]
    
    def generate_response():
        embedding_client = EmbeddingClient()
        qdrant_client = QdrantClientWrapper()
        gemini_client = GeminiClient()
        chunk_repo = ChunkRepository(db)
        
        rag_service = RAGService(
            embedding_client=embedding_client,
            qdrant_client=qdrant_client,
            gemini_client=gemini_client,
            chunk_repo=chunk_repo
        )
        
        full_text = ""
        assistant_message = None
        
        for item in rag_service.answer_query(request.question, history):
            if item["type"] == "token":
                full_text += item["content"]
                yield f"data: {json.dumps({'type': 'token', 'content': item['content']})}\n\n"
            elif item["type"] == "done":
                # Save the assistant message
                assistant_message = msg_repo.create(request.conversation_id, "assistant", full_text)
                msg_repo.create_citations(str(assistant_message.id), item["citations"])
                conv_repo.touch_updated_at(request.conversation_id)
                
                total_messages = len(msg_repo.get_by_conversation(request.conversation_id))
                if total_messages == 2:
                    # Note: this adds a small delay to the final SSE event for first messages only 
                    # (one extra blocking Gemini call), which is an acceptable tradeoff for the prototype; 
                    # a true non-blocking background task is a future improvement.
                    title_service = TitleService(gemini_client)
                    new_title = title_service.generate_title(request.question, full_text)
                    conv_repo.update_title(request.conversation_id, new_title)
                
                yield f"data: {json.dumps({'type': 'done', 'citations': item['citations'], 'message_id': str(assistant_message.id)})}\n\n"
                
    return StreamingResponse(generate_response(), media_type="text/event-stream")

@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
def update_conversation(conversation_id: str, update_data: ConversationUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    conv_repo = ConversationRepository(db)
    conv = conv_repo.get_by_id(conversation_id)
    if not conv or str(conv.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    conv_repo.update_title(conversation_id, update_data.title)
    db.refresh(conv)
    
    return ConversationResponse(
        id=str(conv.id),
        title=conv.title,
        updated_at=conv.updated_at,
        is_archived=conv.is_archived
    )

@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    conv_repo = ConversationRepository(db)
    conv = conv_repo.get_by_id(conversation_id)
    if not conv or str(conv.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    conv_repo.delete(conversation_id)
    return None
