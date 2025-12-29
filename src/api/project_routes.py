from typing import Callable, List
import logging

from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.core.exceptions import NotFoundException
from src.models.database import Project, Conversation, Message, Document, get_db

logger = logging.getLogger(__name__)
from src.models.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from src.repositories.project_repository import ProjectRepository


def create_project_routes(get_repo: Callable[[], ProjectRepository]) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/projects",
        response_model=ProjectResponse,
        status_code=201,
        summary="Create a new project",
        description="""
        Create a new AI Study Buddy project.
        
        Projects contain conversations, documents, and agent configuration.
        Each project can have custom agent settings, system prompts, and enabled tools.
        """,
        responses={
            201: {"description": "Project created successfully"},
            400: {"description": "Invalid project data"},
            500: {"description": "Server error"},
        },
        tags=["Projects"],
    )
    async def create_project(
        project_data: ProjectCreate = Body(
            ...,
            examples=[{
                "name": "Calculus Study",
                "description": "Help with calculus homework and test prep",
                "color": "#3b82f6",
                "agent_name": "Math Tutor",
                "system_prompt": "You are a patient math tutor specializing in calculus. Ask guiding questions before giving answers, show step-by-step solutions, and encourage students to work through problems themselves.",
                "tools": ["calculator"]
            }]
        )
    ):
        """Create a new project with AI agent configuration."""
        try:
            repo = get_repo()
            project = Project(
                user_id=1,
                name=project_data.name,
                description=project_data.description,
                color=project_data.color,
                agent_name=project_data.agent_name,
                system_prompt=project_data.system_prompt,
                tools=project_data.tools,
            )
            created = repo.create(project)
            return ProjectResponse.model_validate(created)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get(
        "/projects",
        response_model=List[ProjectResponse],
        summary="List all projects",
        description="Retrieve all projects for the current user.",
        responses={
            200: {"description": "List of projects"},
            500: {"description": "Server error"},
        },
        tags=["Projects"],
    )
    async def list_projects(db: Session = Depends(get_db)):
        """Get all projects for the current user."""
        try:
            logger.info("Fetching all projects for user 1")
            repo = get_repo()
            projects = repo.find_by_user(1)
            logger.info(f"Found {len(projects)} projects")
            
            # Compute stats for each project
            project_responses = []
            for p in projects:
                # Count conversations for this project
                conv_count = db.query(func.count(Conversation.id)).filter(
                    Conversation.project_id == p.id
                ).scalar() or 0
                
                # Count messages across all conversations in this project
                msg_count = db.query(func.count(Message.id)).join(Conversation).filter(
                    Conversation.project_id == p.id
                ).scalar() or 0
                
                # Count documents for this project
                doc_count = db.query(func.count(Document.id)).filter(
                    Document.project_id == p.id
                ).scalar() or 0
                
                # Create response with stats
                project_dict = {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "color": p.color,
                    "agent_name": p.agent_name,
                    "system_prompt": p.system_prompt,
                    "tools": p.tools,
                    "user_id": p.user_id,
                    "conversation_count": conv_count,
                    "message_count": msg_count,
                    "document_count": doc_count,
                    "created_at": p.created_at,
                    "updated_at": p.updated_at,
                }
                project_responses.append(ProjectResponse(**project_dict))
            
            return project_responses
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to fetch projects")

    @router.get(
        "/projects/{project_id}",
        response_model=ProjectResponse,
        summary="Get project by ID",
        description="Retrieve details for a specific project.",
        responses={
            200: {"description": "Project details"},
            404: {"description": "Project not found"},
            500: {"description": "Server error"},
        },
        tags=["Projects"],
    )
    async def get_project(project_id: int):
        """Get project by ID."""
        try:
            repo = get_repo()
            project = repo.find_by_id(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            return ProjectResponse.model_validate(project)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.put(
        "/projects/{project_id}",
        response_model=ProjectResponse,
        summary="Update project",
        description="Update project details (full or partial update).",
        responses={
            200: {"description": "Project updated successfully"},
            404: {"description": "Project not found"},
            500: {"description": "Server error"},
        },
        tags=["Projects"],
    )
    @router.patch(
        "/projects/{project_id}",
        response_model=ProjectResponse,
        tags=["Projects"],
    )
    async def update_project(project_id: int, update_data: ProjectUpdate):
        """Update project details (PUT for full update, PATCH for partial)."""
        try:
            repo = get_repo()
            project = repo.find_by_id(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            if update_data.name is not None:
                project.name = update_data.name
            if update_data.description is not None:
                project.description = update_data.description
            if update_data.color is not None:
                project.color = update_data.color
            if update_data.agent_name is not None:
                project.agent_name = update_data.agent_name
            if update_data.system_prompt is not None:
                project.system_prompt = update_data.system_prompt
            if update_data.tools is not None:
                project.tools = update_data.tools

            updated = repo.update(project)
            return ProjectResponse.model_validate(updated)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete(
        "/projects/{project_id}",
        status_code=204,
        summary="Delete project",
        description="""
        Delete a project and all associated data.
        
        **Warning:** This cascades to delete all conversations, messages, and documents.
        """,
        responses={
            204: {"description": "Project deleted successfully"},
            404: {"description": "Project not found"},
            500: {"description": "Server error"},
        },
        tags=["Projects"],
    )
    async def delete_project(project_id: int):
        """Delete project and all associated data."""
        try:
            repo = get_repo()
            success = repo.delete(project_id)
            if not success:
                raise HTTPException(status_code=404, detail="Project not found")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
