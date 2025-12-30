from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql://studybuddy:studybuddy_password@localhost:5432/studybuddy"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3-groq-tool-use:8b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite frontend dev server
        "http://localhost:8000"
    ]

    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
    STREAMING_ENABLED: bool = True

    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"

    MAX_FILE_SIZE_MB: int = 10
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    UPLOAD_DIR: str = "uploads"

    @property
    def chroma_url(self) -> str:
        return f"http://{self.CHROMA_HOST}:{self.CHROMA_PORT}"


settings = Settings()
