from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from src.models.database import Message, Conversation


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, message: Message) -> Message:
        self.db.add(message)
        
        # Update conversation's updated_at timestamp when a new message is added
        conversation = self.db.query(Conversation).filter(
            Conversation.id == message.conversation_id
        ).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        return message

    def find_by_id(self, message_id: int) -> Optional[Message]:
        return self.db.query(Message).filter(Message.id == message_id).first()

    def find_by_conversation(self, conversation_id: int, limit: Optional[int] = None) -> List[Message]:
        query = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        
        if limit:
            query = query.limit(limit)
        
        return query.all()

    def get_recent_messages(self, conversation_id: int, limit: int = 10) -> List[Message]:
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )[::-1]

    def delete(self, message_id: int) -> bool:
        message = self.find_by_id(message_id)
        if message:
            self.db.delete(message)
            self.db.commit()
            return True
        return False
