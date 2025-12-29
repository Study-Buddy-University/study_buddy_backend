from datetime import datetime
from typing import List

from src.core.exceptions import FileProcessingError
from src.models.database import Message
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository


class ExportService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
    ):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo

    def export_to_markdown(self, conversation_id: int) -> str:
        try:
            conversation = self.conversation_repo.find_by_id(conversation_id)
            if not conversation:
                raise FileProcessingError("Conversation not found")
            
            messages = self.message_repo.find_by_conversation(conversation_id)
            
            markdown_parts = []
            markdown_parts.append(f"# {conversation.title}")
            markdown_parts.append(f"\n**Created:** {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            markdown_parts.append(f"**Updated:** {conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            markdown_parts.append("\n---\n")
            
            for msg in messages:
                role = "🧑 **You**" if msg.role == "user" else "🤖 **AI Assistant**"
                timestamp = msg.created_at.strftime('%H:%M:%S')
                markdown_parts.append(f"### {role} ({timestamp})")
                markdown_parts.append(f"\n{msg.content}\n")
            
            return "\n".join(markdown_parts)
            
        except Exception as e:
            raise FileProcessingError(f"Failed to export to markdown: {str(e)}")

    def export_to_text(self, conversation_id: int) -> str:
        try:
            conversation = self.conversation_repo.find_by_id(conversation_id)
            if not conversation:
                raise FileProcessingError("Conversation not found")
            
            messages = self.message_repo.find_by_conversation(conversation_id)
            
            text_parts = []
            text_parts.append(f"Conversation: {conversation.title}")
            text_parts.append(f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            text_parts.append("=" * 80)
            text_parts.append("")
            
            for msg in messages:
                role = "You" if msg.role == "user" else "AI Assistant"
                timestamp = msg.created_at.strftime('%H:%M:%S')
                text_parts.append(f"[{timestamp}] {role}:")
                text_parts.append(msg.content)
                text_parts.append("")
            
            return "\n".join(text_parts)
            
        except Exception as e:
            raise FileProcessingError(f"Failed to export to text: {str(e)}")

    def export_to_json(self, conversation_id: int) -> dict:
        try:
            import json
            
            conversation = self.conversation_repo.find_by_id(conversation_id)
            if not conversation:
                raise FileProcessingError("Conversation not found")
            
            messages = self.message_repo.find_by_conversation(conversation_id)
            
            return {
                "conversation_id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "message_type": msg.message_type,
                        "created_at": msg.created_at.isoformat(),
                    }
                    for msg in messages
                ],
            }
            
        except Exception as e:
            raise FileProcessingError(f"Failed to export to JSON: {str(e)}")
