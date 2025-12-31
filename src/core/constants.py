from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    DOCUMENT = "document"


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"
    TEXT = "text"


class ProjectColor(str, Enum):
    BLUE = "#3b82f6"
    GREEN = "#10b981"
    YELLOW = "#f59e0b"
    RED = "#ef4444"
    PURPLE = "#8b5cf6"
    PINK = "#ec4899"
    INDIGO = "#6366f1"
    TEAL = "#14b8a6"


class ExportFormat(str, Enum):
    MARKDOWN = "markdown"
    PDF = "pdf"
    JSON = "json"


MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

CONVERSATION_HISTORY_LIMIT = 10
"""Number of recent messages to include in LLM context window"""

AUTO_TITLE_MAX_LENGTH = 50
"""Maximum characters for auto-generated conversation titles"""

MAX_MESSAGES_PER_CONVERSATION = 1000
"""Prevent unbounded conversation growth"""

DEFAULT_LLM_TEMPERATURE = 0.7
"""
Balance between creativity (1.0) and consistency (0.0).
0.7 provides good reasoning with some variation.
"""

DEFAULT_MAX_TOKENS = 4096
"""Maximum tokens for LLM response generation - increased for complete responses (resumes, reports)"""

MAX_TOOL_ITERATIONS = 5
"""Maximum tool calling iterations to prevent infinite loops"""

TOOL_EXECUTION_TIMEOUT = 30
"""Timeout in seconds for tool execution"""

RAG_TOP_K_DOCUMENTS = 5
"""Number of relevant documents to retrieve for RAG context"""

RAG_SIMILARITY_THRESHOLD = 0.7
"""Minimum similarity score for document relevance (0.0-1.0)"""

MAX_PROJECTS_PER_USER = 100
"""Maximum number of projects a user can create"""

MAX_DOCUMENTS_PER_PROJECT = 500
"""Maximum number of documents per project"""

MAX_CONTEXT_MESSAGES = 10
