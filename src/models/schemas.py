from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from src.core.constants import DocumentType, ExportFormat, MessageRole, MessageType, ProjectColor


class UserBase(BaseModel):
    email: str = Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    name: str = Field(min_length=2, max_length=100)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=100)


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(UserBase):
    id: int
    bio: Optional[str] = None
    organization: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    bio: Optional[str] = Field(None, max_length=500)
    organization: Optional[str] = Field(None, max_length=200)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, min_length=2, max_length=10)


class UserSettings(BaseModel):
    """Schema for user settings"""
    theme: str = Field(default="system", pattern="^(light|dark|system)$")


class UserPreferences(BaseModel):
    """Schema for user preferences"""
    default_model: Optional[str] = Field(None, max_length=100)
    default_temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=100)
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password meets minimum requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    color: str = "#3b82f6"
    agent_name: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[List[str]] = Field(default_factory=list)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    color: Optional[str] = None
    agent_name: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[List[str]] = None


class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    total_tokens: Optional[int] = None
    conversation_count: Optional[int] = 0
    message_count: Optional[int] = 0
    document_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    title: Optional[str] = Field(None, max_length=200)


class ConversationCreate(ConversationBase):
    project_id: int


class ConversationResponse(ConversationBase):
    id: int
    project_id: int
    total_tokens: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    content: str
    role: MessageRole = MessageRole.USER
    message_type: MessageType = MessageType.TEXT
    extra_data: Optional[str] = None


class MessageCreate(MessageBase):
    conversation_id: int


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    token_count: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    project_id: int
    conversation_id: Optional[int] = None
    message: str = Field(min_length=1, max_length=10000)
    model: Optional[str] = None
    use_gpu: bool = True
    document_ids: Optional[List[int]] = None
    stream: bool = False

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class ChatResponse(BaseModel):
    conversation_id: int
    message: MessageResponse
    response: MessageResponse


class DocumentBase(BaseModel):
    filename: str
    file_type: str


class DocumentCreate(DocumentBase):
    project_id: int
    file_path: str
    file_size: int


class DocumentResponse(DocumentBase):
    id: int
    project_id: int
    file_path: str
    file_size: int
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    chunks_created: int
    message: str


class DocumentSearchRequest(BaseModel):
    project_id: int
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class DocumentSearchResponse(BaseModel):
    results: List[dict]


class RAGQueryRequest(BaseModel):
    project_id: int
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[dict]


class ExportRequest(BaseModel):
    conversation_id: int
    format: ExportFormat = ExportFormat.MARKDOWN


class VoiceTranscribeRequest(BaseModel):
    project_id: int
    conversation_id: Optional[int] = None


class VoiceTranscribeResponse(BaseModel):
    transcription: str
    conversation_id: Optional[int] = None


class ConversationStatsResponse(BaseModel):
    conversation_id: int
    message_count: int
    total_tokens: int
    max_tokens: int
    usage_percentage: float
    remaining_tokens: int
    is_near_limit: bool
    document_count: int
    
    
class ChatStatsResponse(BaseModel):
    messages_tokens: int
    system_prompt_tokens: int
    document_context_tokens: int
    total_tokens: int
    max_tokens: int
    usage_percentage: float
    remaining_tokens: int
    is_near_limit: bool
