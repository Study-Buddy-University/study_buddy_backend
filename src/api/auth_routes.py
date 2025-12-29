from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, Body
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas import AuthResponse, UserCreate, UserLogin, UserResponse
from src.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=201,
    summary="Create new user account",
    description="""
    Register a new user with email, name, and password.
    
    **Returns:** Access token and user details for immediate login.
    """,
    responses={
        201: {"description": "User created successfully with access token"},
        400: {"description": "Invalid data or email already exists"},
        500: {"description": "Server error"},
    },
    tags=["Authentication"],
)
async def signup(
    user_data: UserCreate = Body(
        ...,
        examples=[{
            "email": "student@example.com",
            "name": "John Doe",
            "password": "SecurePass123!"
        }]
    ),
    db: Session = Depends(get_db)
):
    """Create new user account and return access token."""
    try:
        user = auth_service.signup(db, user_data)
        
        # Generate access token
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                bio=user.bio,
                organization=user.organization,
                avatar_url=user.avatar_url,
                timezone=user.timezone,
                language=user.language,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Signup error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email and password",
    description="""
    Authenticate user and receive access token.
    
    **Token Usage:** Include in subsequent requests as `Authorization: Bearer <token>`
    """,
    responses={
        200: {"description": "Login successful with access token"},
        401: {"description": "Invalid credentials"},
        500: {"description": "Server error"},
    },
    tags=["Authentication"],
)
async def login(
    credentials: UserLogin = Body(
        ...,
        examples=[{
            "email": "student@example.com",
            "password": "SecurePass123!"
        }]
    ),
    db: Session = Depends(get_db)
):
    """Authenticate user with email/password and return JWT token."""
    try:
        user, access_token = auth_service.login(db, credentials)
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                bio=user.bio,
                organization=user.organization,
                avatar_url=user.avatar_url,
                timezone=user.timezone,
                language=user.language,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/logout",
    summary="Logout current user",
    description="""
    Logout endpoint for client-side token removal.
    
    **Note:** JWT tokens are stateless, so logout is handled client-side by removing the token.
    """,
    responses={
        200: {"description": "Logout successful"},
    },
    tags=["Authentication"],
)
async def logout():
    """Logout user (client removes token)."""
    return {"message": "Logged out successfully"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="""
    Retrieve the authenticated user's profile information.
    
    **Requires:** Valid JWT token in Authorization header.
    **Returns:** User profile with preferences and settings.
    """,
    responses={
        200: {"description": "User profile"},
        401: {"description": "Invalid or missing token"},
        500: {"description": "Server error"},
    },
    tags=["Authentication"],
)
async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    user = auth_service.get_current_user(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        bio=user.bio,
        organization=user.organization,
        avatar_url=user.avatar_url,
        timezone=user.timezone,
        language=user.language,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


def create_auth_routes() -> APIRouter:
    """Create and return auth router"""
    return router
