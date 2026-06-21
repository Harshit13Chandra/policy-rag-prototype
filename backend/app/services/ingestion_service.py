import uuid
import logging
from app.repositories.document_repo import DocumentRepository
from app.repositories.chunk_repo import ChunkRepository
from app.services.embedding_client import EmbeddingClient
from app.services.vectordb_client import QdrantClientWrapper
from app.utils.text_extraction import extract_text_from_file
from app.utils.chunking import chunk_pages

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        embedding_client: EmbeddingClient,
        qdrant_client: QdrantClientWrapper
    ):
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self.embedding_client = embedding_client
        self.qdrant_client = qdrant_client

    def ingest_document(self, document_id: str, file_path: str, mime_type: str) -> None:
        try:
            # 1. Update status to PROCESSING
            self.document_repo.update_status(document_id, "PROCESSING")
            
            # 2. Extract text from file
            pages = extract_text_from_file(file_path, mime_type)
            
            # 3. Chunk pages
            chunks = chunk_pages(pages)
            
            # 4. Check for empty chunks
            if not chunks:
                raise ValueError("No text content extracted from document")
                
            # 5. Batch into groups of 32
            batch_size = 32
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                # 6a. Get embeddings for batch
                vectors = self.embedding_client.embed_batch([c["text"] for c in batch])
                
                # 6b. Process each chunk in the batch
                for chunk_dict, vector in zip(batch, vectors):
                    vector_id = uuid.uuid4()
                    
                    # Upsert to Qdrant
                    self.qdrant_client.upsert_chunk(
                        vector_id=str(vector_id),
                        vector=vector,
                        payload={
                            "document_id": document_id,
                            "chunk_index": chunk_dict["chunk_index"],
                            "text": chunk_dict["text"],
                            "page_number": chunk_dict["page_number"],
                            "is_active": True
                        }
                    )
                    
                    # Store chunk metadata in relational DB
                    self.chunk_repo.create(
                        document_id=document_id,
                        chunk_index=chunk_dict["chunk_index"],
                        text=chunk_dict["text"],
                        page_number=chunk_dict["page_number"],
                        token_count=chunk_dict["token_count"],
                        vector_id=str(vector_id)
                    )
                    
            # 7. Update status to READY
            self.document_repo.update_status(document_id, "READY", page_count=len(pages))
            
            # 8. Print summary
            print(f"Document {document_id} ingested: {len(chunks)} chunks created")
            
        except Exception as e:
            # Update status to FAILED and re-raise
            logger.error(f"Failed to ingest document {document_id}: {str(e)}")
            self.document_repo.update_status(document_id, "FAILED", error_message=str(e))
            raise e
