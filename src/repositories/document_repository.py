from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.database import Document


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def find_by_id(self, document_id: int) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def find_by_project(self, project_id: int) -> List[Document]:
        return self.db.query(Document).filter(Document.project_id == project_id).all()

    def update(self, document: Document) -> Document:
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete(self, document_id: int) -> bool:
        document = self.find_by_id(document_id)
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False
