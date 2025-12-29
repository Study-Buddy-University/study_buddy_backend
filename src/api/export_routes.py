from typing import Callable

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response

from src.services.export_service import ExportService


def create_export_routes(get_service: Callable[[], ExportService]) -> APIRouter:
    router = APIRouter()

    @router.get(
        "/export/{conversation_id}/markdown",
        summary="Export conversation as Markdown",
        description="""
        Export a conversation with all messages as a formatted Markdown file.
        
        **Format:** Includes timestamps, roles, and proper markdown formatting.
        """,
        responses={
            200: {
                "description": "Markdown file download",
                "content": {"text/markdown": {}}
            },
            404: {"description": "Conversation not found"},
            500: {"description": "Server error"},
        },
        tags=["Export"],
    )
    async def export_markdown(conversation_id: int):
        """Export conversation as downloadable Markdown file."""
        try:
            service = get_service()
            markdown = service.export_to_markdown(conversation_id)
            
            return Response(
                content=markdown,
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename=conversation_{conversation_id}.md"
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get(
        "/export/{conversation_id}/text",
        summary="Export conversation as plain text",
        description="""
        Export a conversation as a plain text file.
        
        **Format:** Simple text format with timestamps and roles.
        """,
        responses={
            200: {
                "description": "Text file download",
                "content": {"text/plain": {}}
            },
            404: {"description": "Conversation not found"},
            500: {"description": "Server error"},
        },
        tags=["Export"],
    )
    async def export_text(conversation_id: int):
        """Export conversation as downloadable text file."""
        try:
            service = get_service()
            text = service.export_to_text(conversation_id)
            
            return PlainTextResponse(
                content=text,
                headers={
                    "Content-Disposition": f"attachment; filename=conversation_{conversation_id}.txt"
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get(
        "/export/{conversation_id}/json",
        summary="Export conversation as JSON",
        description="""
        Export a conversation with full message metadata as JSON.
        
        **Includes:** Message IDs, timestamps, roles, content, and token counts.
        """,
        responses={
            200: {
                "description": "JSON data",
                "content": {"application/json": {}}
            },
            404: {"description": "Conversation not found"},
            500: {"description": "Server error"},
        },
        tags=["Export"],
    )
    async def export_json(conversation_id: int):
        """Export conversation as structured JSON data."""
        try:
            service = get_service()
            data = service.export_to_json(conversation_id)
            return data
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
