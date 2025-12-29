"""User profile and settings API endpoints"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Header, status, UploadFile, File
from sqlalchemy.orm import Session
import logging
import os
from pathlib import Path

from src.models.database import get_db, User
from src.models.schemas import (
    UserResponse,
    UserProfileUpdate,
    UserSettings,
    UserPreferences,
    PasswordChange
)
from src.services.user_service import UserService
from src.services.auth_service import AuthService
from src.core.exceptions import NotFoundError, ValidationError, AuthenticationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])
auth_service = AuthService()


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_service.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile
    
    Returns:
        UserResponse: User profile data
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile
    
    Args:
        profile_update: Profile update data
        
    Returns:
        UserResponse: Updated user profile
        
    Raises:
        400: Validation error (e.g., email already in use)
        404: User not found
    """
    try:
        updated_user = UserService.update_user_profile(
            db=db,
            user_id=current_user.id,
            name=profile_update.name,
            email=profile_update.email,
            bio=profile_update.bio,
            organization=profile_update.organization,
            timezone=profile_update.timezone,
            language=profile_update.language
        )
        return updated_user
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/me/settings", response_model=UserSettings)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's settings
    
    Returns:
        UserSettings: User settings data
    """
    try:
        settings = UserService.get_user_settings(db, current_user.id)
        
        # Convert dict to UserSettings schema with defaults
        return UserSettings(
            theme=settings.get("theme", "system")
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/me/settings", response_model=UserSettings)
async def update_user_settings(
    settings: UserSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's settings
    
    Args:
        settings: New settings data
        
    Returns:
        UserSettings: Updated settings
    """
    try:
        # Convert Pydantic model to dict for storage
        settings_dict = settings.model_dump()
        
        updated_settings = UserService.update_user_settings(
            db=db,
            user_id=current_user.id,
            settings=settings_dict
        )
        
        return UserSettings(**updated_settings)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/me/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's preferences
    
    Returns:
        UserPreferences: User preferences data
    """
    try:
        preferences = UserService.get_user_preferences(db, current_user.id)
        
        # Convert dict to UserPreferences schema with defaults
        return UserPreferences(
            default_model=preferences.get("default_model"),
            default_temperature=preferences.get("default_temperature", 0.7)
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/me/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's preferences
    
    Args:
        preferences: New preferences data
        
    Returns:
        UserPreferences: Updated preferences
    """
    try:
        # Convert Pydantic model to dict for storage
        prefs_dict = preferences.model_dump()
        
        updated_prefs = UserService.update_user_preferences(
            db=db,
            user_id=current_user.id,
            preferences=prefs_dict
        )
        
        return UserPreferences(**updated_prefs)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/me/password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password
    
    Args:
        password_data: Current and new password
        
    Returns:
        Success message
        
    Raises:
        400: Validation error (password too short)
        401: Current password incorrect
    """
    try:
        UserService.change_password(
            db=db,
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        return {"message": "Password changed successfully"}
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload user avatar image
    
    Args:
        file: Image file (JPG, PNG, or GIF, max 5MB)
        
    Returns:
        UserResponse: Updated user profile with new avatar URL
        
    Raises:
        400: Invalid file type or size
    """
    # Validate file type
    valid_types = ["image/jpeg", "image/png", "image/gif"]
    if file.content_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPG, PNG, and GIF are allowed"
        )
    
    # Read file content to check size
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit"
        )
    
    # Reset file pointer
    await file.seek(0)
    
    try:
        logger.info(f"Starting avatar upload for user {current_user.id}")
        logger.debug(f"File: {file.filename}, Type: {file.content_type}, Size: {len(content)} bytes")
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads/avatars")
        upload_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Upload directory ready: {upload_dir.absolute()}")
        
        # Delete old avatar file if exists
        if current_user.avatar_url:
            old_filename = current_user.avatar_url.split("/")[-1]
            old_file_path = upload_dir / old_filename
            if old_file_path.exists():
                old_file_path.unlink()
                logger.info(f"Deleted old avatar: {old_filename}")
        
        # Generate unique filename
        import uuid
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{current_user.id}_{uuid.uuid4().hex}.{file_extension}"
        file_path = upload_dir / unique_filename
        logger.debug(f"Saving file to: {file_path.absolute()}")
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"File saved successfully: {file_path.name}")
        
        # Update user avatar URL (relative path for serving)
        avatar_url = f"/uploads/avatars/{unique_filename}"
        logger.debug(f"Updating database with avatar_url: {avatar_url}")
        updated_user = UserService.update_avatar(db, current_user.id, avatar_url)
        
        logger.info(f"✅ Avatar upload complete for user {current_user.id}: {avatar_url}")
        return updated_user
        
    except Exception as e:
        logger.error(f"Error uploading avatar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar"
        )


@router.delete("/me")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user's account
    
    Returns:
        Success message
        
    Note:
        This permanently deletes the user and all associated data
    """
    try:
        UserService.delete_user(db, current_user.id)
        return {"message": "Account deleted successfully"}
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
