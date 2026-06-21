import hashlib
import pathlib
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.config import get_settings
from app.schemas.document_schema import DocumentResponse, DocumentListResponse
from app.repositories.document_repo import DocumentRepository
from app.repositories.chunk_repo import ChunkRepository
from app.services.embedding_client import EmbeddingClient
from app.services.vectordb_client import QdrantClientWrapper
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Note: For this prototype, any authenticated user can upload. 
    # Role-based admin restriction is a known simplification to revisit later.
    
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    
    mime_type = file.content_type
    if not mime_type or mime_type == "application/octet-stream":
        ext = pathlib.Path(file.filename).suffix.lower() if file.filename else ""
        if ext == ".pdf":
            mime_type = "application/pdf"
        elif ext == ".docx":
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
    valid_mimes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if mime_type not in valid_mimes:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
    repo = DocumentRepository(db)
    existing = repo.get_by_hash(file_hash)
    if existing and existing.status == "READY":
        raise HTTPException(status_code=409, detail="This exact file has already been uploaded")
        
    settings = get_settings()
    upload_dir = pathlib.Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    ext = pathlib.Path(file.filename).suffix if file.filename else ""
    storage_path = str(upload_dir / f"{uuid.uuid4()}{ext}")
    
    with open(storage_path, "wb") as f:
        f.write(content)
        
    document = repo.create(
        title=title,
        filename=file.filename or "unknown",
        file_hash=file_hash,
        mime_type=mime_type,
        storage_path=storage_path,
        uploaded_by=str(current_user.id)
    )
    
    chunk_repo = ChunkRepository(db)
    embedding_client = EmbeddingClient()
    qdrant_client = QdrantClientWrapper()
    
    ingestion_service = IngestionService(
        document_repo=repo,
        chunk_repo=chunk_repo,
        embedding_client=embedding_client,
        qdrant_client=qdrant_client
    )
    
    # Run synchronously. Will take time for large docs, but okay for prototype.
    ingestion_service.ingest_document(
        document_id=str(document.id),
        file_path=storage_path,
        mime_type=mime_type
    )
    
    db.refresh(document)
    
    return DocumentResponse(
        id=str(document.id),
        title=document.title,
        filename=document.filename,
        status=document.status,
        page_count=document.page_count,
        created_at=document.created_at
    )

@router.get("/", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    repo = DocumentRepository(db)
    docs = repo.list_all()
    items = [
        DocumentResponse(
            id=str(d.id),
            title=d.title,
            filename=d.filename,
            status=d.status,
            page_count=d.page_count,
            created_at=d.created_at
        ) for d in docs
    ]
    return DocumentListResponse(items=items)
