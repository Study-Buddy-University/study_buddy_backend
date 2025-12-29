"""User service for profile and settings management"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import logging

from src.models.database import User
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError

logger = logging.getLogger(__name__)

ph = PasswordHasher()


class UserService:
    """Service for user profile and settings operations"""

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """
        Get user by ID
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User object
            
        Raises:
            NotFoundError: If user not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise NotFoundError(f"User with ID {user_id} not found")
        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Get user by email
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            User object or None
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def update_user_profile(
        db: Session,
        user_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        bio: Optional[str] = None,
        organization: Optional[str] = None,
        timezone: Optional[str] = None,
        language: Optional[str] = None
    ) -> User:
        """
        Update user profile information
        
        Args:
            db: Database session
            user_id: User ID
            name: New name (optional)
            email: New email (optional)
            bio: New bio (optional)
            organization: New organization (optional)
            timezone: New timezone (optional)
            language: New language (optional)
            
        Returns:
            Updated User object
            
        Raises:
            NotFoundError: If user not found
            ValidationError: If email already in use
        """
        user = UserService.get_user_by_id(db, user_id)
        
        try:
            if name is not None:
                user.name = name
            if email is not None:
                # Check if email is already in use by another user
                existing_user = db.query(User).filter(
                    User.email == email, 
                    User.id != user_id
                ).first()
                if existing_user:
                    raise ValidationError("Email already in use")
                user.email = email
            if bio is not None:
                user.bio = bio
            if organization is not None:
                user.organization = organization
            if timezone is not None:
                user.timezone = timezone
            if language is not None:
                user.language = language
            
            db.commit()
            db.refresh(user)
            logger.info(f"Updated profile for user {user_id}")
            return user
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error updating user {user_id}: {e}")
            raise ValidationError("Email already in use")

    @staticmethod
    def get_user_settings(db: Session, user_id: int) -> dict:
        """
        Get user settings
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Settings dictionary
            
        Raises:
            NotFoundError: If user not found
        """
        user = UserService.get_user_by_id(db, user_id)
        return user.settings or {}

    @staticmethod
    def update_user_settings(db: Session, user_id: int, settings: dict) -> dict:
        """
        Update user settings
        
        Args:
            db: Database session
            user_id: User ID
            settings: New settings dictionary
            
        Returns:
            Updated settings dictionary
            
        Raises:
            NotFoundError: If user not found
        """
        user = UserService.get_user_by_id(db, user_id)
        
        # Merge with existing settings
        current_settings = user.settings or {}
        current_settings.update(settings)
        user.settings = current_settings
        
        db.commit()
        db.refresh(user)
        logger.info(f"Updated settings for user {user_id}")
        return user.settings

    @staticmethod
    def get_user_preferences(db: Session, user_id: int) -> dict:
        """
        Get user preferences
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Preferences dictionary
            
        Raises:
            NotFoundError: If user not found
        """
        user = UserService.get_user_by_id(db, user_id)
        return user.preferences or {}

    @staticmethod
    def update_user_preferences(db: Session, user_id: int, preferences: dict) -> dict:
        """
        Update user preferences
        
        Args:
            db: Database session
            user_id: User ID
            preferences: New preferences dictionary
            
        Returns:
            Updated preferences dictionary
            
        Raises:
            NotFoundError: If user not found
        """
        user = UserService.get_user_by_id(db, user_id)
        
        # Merge with existing preferences
        current_prefs = user.preferences or {}
        current_prefs.update(preferences)
        user.preferences = current_prefs
        
        db.commit()
        db.refresh(user)
        logger.info(f"Updated preferences for user {user_id}")
        return user.preferences

    @staticmethod
    def change_password(
        db: Session,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password
        
        Args:
            db: Database session
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            True if successful
            
        Raises:
            NotFoundError: If user not found
            AuthenticationError: If current password is incorrect
            ValidationError: If new password is invalid
        """
        user = UserService.get_user_by_id(db, user_id)
        
        # Verify current password
        try:
            ph.verify(user.password_hash, current_password)
        except VerifyMismatchError:
            logger.warning(f"Failed password change attempt for user {user_id}")
            raise AuthenticationError("Current password is incorrect")
        
        # Validate new password
        if len(new_password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        # Hash and update password
        user.password_hash = ph.hash(new_password)
        db.commit()
        logger.info(f"Password changed for user {user_id}")
        return True

    @staticmethod
    def update_avatar(db: Session, user_id: int, avatar_url: str) -> User:
        """
        Update user avatar URL
        
        Args:
            db: Database session
            user_id: User ID
            avatar_url: New avatar URL
            
        Returns:
            Updated User object
            
        Raises:
            NotFoundError: If user not found
        """
        user = UserService.get_user_by_id(db, user_id)
        user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
        logger.info(f"Updated avatar for user {user_id}")
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """
        Soft delete user (mark as inactive or actually delete)
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            True if successful
            
        Raises:
            NotFoundError: If user not found
        """
        user = UserService.get_user_by_id(db, user_id)
        
        # For now, actually delete. In production, consider soft delete
        db.delete(user)
        db.commit()
        logger.info(f"Deleted user {user_id}")
        return True
