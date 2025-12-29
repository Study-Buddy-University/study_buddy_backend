from typing import Callable

from fastapi import APIRouter, HTTPException
from sqlalchemy import func

from src.models.database import Project, Conversation, Message, Document
from src.models.schemas import ConversationStatsResponse
from src.repositories.project_repository import ProjectRepository
from src.repositories.conversation_repository import ConversationRepository
from src.utils.token_counter import calculate_context_usage, estimate_tokens


def create_stats_routes(
    get_project_repo: Callable[[], ProjectRepository],
    get_conversation_repo: Callable[[], ConversationRepository] = None
) -> APIRouter:
    router = APIRouter()

    @router.get(
        "/stats/overview",
        summary="Get dashboard statistics overview",
        description="""
        Retrieve comprehensive statistics for the current user's dashboard.
        
        **Includes:**
        - Total counts (projects, conversations, messages, documents)
        - Recent projects (last 5)
        - Recent conversations (last 5)
        """,
        responses={
            200: {"description": "Dashboard statistics"},
            500: {"description": "Server error"},
        },
        tags=["Statistics"],
    )
    async def get_overview_stats():
        """Get comprehensive dashboard statistics for user."""
        try:
            repo = get_project_repo()
            db = repo.db
            
            # Count totals (hardcoded user_id=1 for now)
            total_projects = db.query(func.count(Project.id)).filter(Project.user_id == 1).scalar()
            total_conversations = db.query(func.count(Conversation.id)).join(Project).filter(Project.user_id == 1).scalar()
            total_messages = db.query(func.count(Message.id)).join(Conversation).join(Project).filter(Project.user_id == 1).scalar()
            total_documents = db.query(func.count(Document.id)).join(Project).filter(Project.user_id == 1).scalar()
            
            # Get recent projects
            recent_projects = db.query(Project).filter(Project.user_id == 1).order_by(Project.updated_at.desc()).limit(5).all()
            
            # Get recent conversations with titles
            recent_conversations = (
                db.query(Conversation)
                .join(Project)
                .filter(Project.user_id == 1)
                .order_by(Conversation.updated_at.desc())
                .limit(5)
                .all()
            )
            
            return {
                "totals": {
                    "projects": total_projects or 0,
                    "conversations": total_conversations or 0,
                    "messages": total_messages or 0,
                    "documents": total_documents or 0
                },
                "recent_projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "color": p.color,
                        "updated_at": p.updated_at.isoformat()
                    } for p in recent_projects
                ],
                "recent_conversations": [
                    {
                        "id": c.id,
                        "title": c.title or "Untitled Chat",
                        "project_id": c.project_id,
                        "updated_at": c.updated_at.isoformat()
                    } for c in recent_conversations
                ]
            }
        except Exception as e:
            return {
                "totals": {
                    "projects": 0,
                    "conversations": 0,
                    "messages": 0,
                    "documents": 0
                },
                "recent_projects": [],
                "recent_conversations": []
            }

    @router.get(
        "/stats/conversation/{conversation_id}",
        response_model=ConversationStatsResponse,
        summary="Get conversation token usage statistics",
        description="""
        Retrieve detailed token usage and context window statistics for a conversation.
        
        **Includes:**
        - Message count and total tokens
        - Context window usage percentage
        - Remaining tokens available
        - Warning if near context limit
        """,
        responses={
            200: {"description": "Conversation statistics"},
            404: {"description": "Conversation not found"},
            500: {"description": "Server error"},
        },
        tags=["Statistics"],
    )
    async def get_conversation_stats(conversation_id: int):
        """Get detailed token usage statistics for a conversation."""
        from src.models.database import get_db
        
        db = next(get_db())
        try:
            # Use single DB session for all operations
            conv_repo = ConversationRepository(db)
            conversation = conv_repo.find_by_id(conversation_id)
            
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Get all messages for this conversation
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).all()
            
            # Count documents in project
            project_repo = ProjectRepository(db)
            project = project_repo.find_by_id(conversation.project_id)
            document_count = len(project.documents) if project else 0
            
            # Calculate token usage
            messages_tokens = sum(msg.token_count or 0 for msg in messages)
            system_prompt_tokens = estimate_tokens(project.system_prompt) if project and project.system_prompt else 0
            
            # Estimate document context tokens (assume average of 500 tokens per document in context)
            document_context_tokens = min(document_count * 500, 2000) if document_count > 0 else 0
            
            stats = calculate_context_usage(
                messages_tokens=messages_tokens,
                system_prompt_tokens=system_prompt_tokens,
                document_context_tokens=document_context_tokens,
                model_name="default"
            )
            
            return ConversationStatsResponse(
                conversation_id=conversation_id,
                message_count=len(messages),
                total_tokens=stats["total_tokens"],
                max_tokens=stats["max_tokens"],
                usage_percentage=stats["usage_percentage"],
                remaining_tokens=stats["remaining_tokens"],
                is_near_limit=stats["is_near_limit"],
                document_count=document_count
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            db.close()

    return router
