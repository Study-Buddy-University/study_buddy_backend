from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.database import Conversation


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, conversation: Conversation) -> Conversation:
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def find_by_id(self, conversation_id: int) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def find_by_project(self, project_id: int) -> List[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(Conversation.project_id == project_id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    def get_or_create(
        self, project_id: int, conversation_id: Optional[int] = None, title: Optional[str] = None
    ) -> Conversation:
        if conversation_id:
            conversation = self.find_by_id(conversation_id)
            if conversation:
                return conversation
        
        conversation = Conversation(project_id=project_id, title=title)
        return self.create(conversation)

    def update(self, conversation: Conversation) -> Conversation:
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def delete(self, conversation_id: int) -> bool:
        conversation = self.find_by_id(conversation_id)
        if conversation:
            self.db.delete(conversation)
            self.db.commit()
            return True
        return False
