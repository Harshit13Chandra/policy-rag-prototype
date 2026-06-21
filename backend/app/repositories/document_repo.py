from sqlalchemy.orm import Session
from app.models.document import Document

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, title: str, filename: str, file_hash: str, mime_type: str, storage_path: str, uploaded_by: str) -> Document:
        document = Document(
            title=title,
            filename=filename,
            file_hash=file_hash,
            mime_type=mime_type,
            storage_path=storage_path,
            uploaded_by=uploaded_by
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update_status(self, document_id: str, status: str, error_message: str | None = None, page_count: int | None = None) -> None:
        document = self.get_by_id(document_id)
        if document:
            document.status = status
            if error_message is not None:
                document.error_message = error_message
            if page_count is not None:
                document.page_count = page_count
            self.db.commit()

    def get_by_id(self, document_id: str) -> Document | None:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def list_all(self) -> list[Document]:
        return self.db.query(Document).all()

    def get_by_hash(self, file_hash: str) -> Document | None:
        return self.db.query(Document).filter(Document.file_hash == file_hash).first()
