from datetime import datetime, timedelta
from typing import Optional

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.models.database import User
from src.models.schemas import UserCreate, UserLogin, UserResponse

# JWT Configuration
SECRET_KEY = "your-secret-key-here-change-in-production-use-env-variable"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Argon2 password hasher
ph = PasswordHasher(
    time_cost=2,  # Number of iterations
    memory_cost=65536,  # Memory usage in KiB (64 MB)
    parallelism=1,  # Number of parallel threads
    hash_len=32,  # Length of the hash in bytes
    salt_len=16,  # Length of random salt in bytes
    type=Type.ID  # Argon2id (hybrid of Argon2i and Argon2d)
)


class AuthService:
    """Authentication service with Argon2 password hashing and JWT tokens"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using Argon2"""
        return ph.hash(password)

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against Argon2 hash"""
        try:
            ph.verify(password_hash, password)
            return True
        except VerifyMismatchError:
            return False

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    def signup(self, db: Session, user_data: UserCreate) -> User:
        """Create new user with hashed password"""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("User with this email already exists")

        # Hash password
        password_hash = self.hash_password(user_data.password)

        # Create user
        db_user = User(
            email=user_data.email,
            name=user_data.name,
            password_hash=password_hash,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def login(self, db: Session, credentials: UserLogin) -> tuple[User, str]:
        """Authenticate user and return user + access token"""
        # Find user by email
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user:
            raise ValueError("Invalid email or password")

        # Verify password
        if not self.verify_password(credentials.password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Create access token
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )

        return user, access_token

    def get_current_user(self, db: Session, token: str) -> Optional[User]:
        """Get current user from JWT token"""
        payload = self.verify_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
