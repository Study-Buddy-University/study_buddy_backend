# AI Study Buddy - Backend API

**Author:** Alexandros Karales | **Website:** [karales.com](https://karales.com) | **Email:** karales@gmail.com

FastAPI backend with multi-LLM support, RAG, voice I/O, GPU acceleration, and comprehensive API.

## ✨ Features

### AI & LLM
- 🤖 **Multi-LLM Support** - 7+ models (Qwen, Llama, Gemma, Mistral, Phi)
- ⚡ **GPU Acceleration** - Optional GPU support for faster inference
- 🔄 **Model Switching** - Dynamic model selection per request
- 📊 **Token Analytics** - Track usage and optimize costs

### Document & RAG
- 📚 **RAG (Retrieval Augmented Generation)** - Document-aware conversations
- 📄 **Document Processing** - Upload and analyze PDFs, TXT files
- 🔍 **Semantic Search** - ChromaDB vector store for context retrieval
- 📝 **Document Summarization** - AI-powered document summaries

### Conversation Management
- 💬 **Chat History** - Persistent conversation tracking
- 🏷️ **Title Management** - PATCH endpoint for conversation titles
- 🗑️ **Conversation Deletion** - Full CRUD operations
- 📂 **Project Organization** - Group conversations by project

### Voice & Audio
- 🎤 **Speech-to-Text** - Whisper-based voice transcription
- 🔊 **Text-to-Speech** - Voice response generation
- 🎙️ **Voice Chat** - End-to-end voice conversation support

### User Management
- 👤 **User Profiles** - Complete profile management
- ⚙️ **Settings & Preferences** - Customizable user settings
- 🔐 **JWT Authentication** - Secure token-based auth
- 🖼️ **Avatar Upload** - Profile picture support

### Export & Analytics
- 📥 **Export Conversations** - Markdown, JSON, TXT formats
- 📈 **Statistics Dashboard** - Usage metrics and insights
- 🔢 **Token Counting** - Detailed token usage tracking

## 🛠️ Tech Stack

- **FastAPI 0.115+** - Modern async Python web framework
- **SQLAlchemy 2.0** - ORM with async support
- **PostgreSQL** - Relational database
- **ChromaDB** - Vector database for embeddings
- **Ollama** - Local LLM inference
- **Pydantic V2** - Data validation
- **JWT** - Authentication tokens
- **Alembic** - Database migrations (planned)

## 📋 API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Create new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/logout` - Logout user
- `GET /api/v1/auth/me` - Get current user

### Users
- `GET /api/v1/users/me` - Get user profile
- `PUT /api/v1/users/me` - Update profile
- `DELETE /api/v1/users/me` - Delete account
- `GET /api/v1/users/me/settings` - Get settings
- `PUT /api/v1/users/me/settings` - Update settings
- `POST /api/v1/users/me/avatar` - Upload avatar
- `PUT /api/v1/users/me/password` - Change password

### Projects
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Get project
- `PUT/PATCH /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project (204)

### Chat & Conversations
- `POST /api/v1/chat` - Send message (with `use_gpu` param)
- `POST /api/v1/chat/stream` - Streaming chat response
- `GET /api/v1/projects/{id}/conversations` - List conversations
- `GET /api/v1/conversations/{id}/messages` - Get messages
- `PATCH /api/v1/conversations/{id}` - Update title
- `DELETE /api/v1/conversations/{id}` - Delete conversation

### Documents
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/projects/{id}/documents` - List documents
- `POST /api/v1/documents/search` - Semantic search
- `POST /api/v1/documents/summarize` - Summarize document
- `GET /api/v1/documents/{id}` - Get document metadata
- `GET /api/v1/documents/{id}/download` - Download document
- `DELETE /api/v1/documents/{id}` - Delete document

### Voice
- `POST /api/v1/voice/transcribe` - Audio to text
- `POST /api/v1/voice/speak` - Text to speech
- `POST /api/v1/voice/chat` - Voice conversation

### Export
- `GET /api/v1/export/{id}/markdown` - Export as Markdown
- `GET /api/v1/export/{id}/json` - Export as JSON
- `GET /api/v1/export/{id}/text` - Export as plain text

### Statistics
- `GET /api/v1/stats/overview` - Dashboard statistics
- `GET /api/v1/stats/conversation/{id}` - Conversation stats

### System
- `GET /api/v1/system/gpu` - GPU information
- `GET /health` - Health check
- `GET /` - API root

## 🌐 Service URLs & Access

### Services with Web Interface

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main React application |
| **Backend API** | http://localhost:8001 | FastAPI backend |
| **Swagger Docs** | http://localhost:8001/docs | Interactive API documentation |
| **ReDoc** | http://localhost:8001/redoc | Alternative API documentation |
| **SearXNG** | http://localhost:8080 | Self-hosted search engine UI |

### API-Only Services (No Web UI)

| Service | Port | Access Method |
|---------|------|---------------|
| **ChromaDB** | 8000 | API only - used by backend for vector embeddings |
| **Ollama** | 11434 | API only - LLM inference engine |
| **PostgreSQL** | 5433 | Database - connect via client tools |

### Public Endpoints (No Authentication Required)

- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Swagger documentation
- `GET /redoc` - ReDoc documentation
- `POST /api/v1/auth/signup` - Create account
- `POST /api/v1/auth/login` - Login

### Protected Endpoints (Authentication Required)

All other endpoints require JWT token in `Authorization: Bearer <token>` header.

**How to authenticate in Swagger:**

1. **Get your token from the frontend:**
   - Login to the frontend at http://localhost:3000
   - Open browser DevTools (F12)
   - Go to Console tab
   - Run: `localStorage.getItem('auth_token')`
   - Copy the token value

2. **Authorize in Swagger:**
   - Visit http://localhost:8001/docs
   - Click the **"Authorize"** button (green button at top right with lock icon 🔓)
   - In the popup, paste your token in the **Value** field
   - The token will automatically have "Bearer " prefix applied
   - Click **"Authorize"** then **"Close"**

3. **Test endpoints:**
   - All protected endpoints will now work
   - Your token persists across page refreshes

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Ollama (for local LLM)

### Local Development

```bash
# Clone repository
git clone https://github.com/akarales/study_buddy_backend.git
cd study_buddy_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
python src/init_db.py

# Start development server
uvicorn src.app:app --reload --host 0.0.0.0 --port 8001
```

### Using UV (Recommended)

```bash
# Install dependencies with UV
uv pip install -r requirements.txt

# Run with UV
uv run uvicorn src.app:app --reload
```

### Docker Development

```bash
# Build image
docker build -t study-buddy-backend .

# Run container
docker run -p 8001:8001 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e OLLAMA_BASE_URL=http://ollama:11434 \
  study-buddy-backend
```

## 📚 API Documentation

Once the server is running, access interactive documentation:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI JSON**: http://localhost:8001/openapi.json

## 🏗️ Project Structure

```
backend/
├── src/
│   ├── app.py                 # FastAPI application & route registration
│   ├── config.py              # Configuration settings
│   ├── api/                   # API route handlers
│   │   ├── auth_routes.py     # Authentication endpoints
│   │   ├── chat_routes.py     # Chat & conversation endpoints
│   │   ├── document_routes.py # Document management
│   │   ├── export_routes.py   # Export endpoints
│   │   ├── project_routes.py  # Project CRUD
│   │   ├── stats_routes.py    # Statistics & analytics
│   │   ├── system_routes.py   # System info (GPU)
│   │   ├── user_routes.py     # User management
│   │   └── voice_routes.py    # Voice I/O
│   ├── models/                # SQLAlchemy models
│   │   ├── database.py        # DB models & engine
│   │   └── schemas.py         # Pydantic schemas
│   ├── services/              # Business logic
│   │   ├── auth_service.py    # Authentication
│   │   ├── chat_service.py    # Chat orchestration
│   │   ├── document_service.py# Document processing
│   │   ├── export_service.py  # Export generation
│   │   ├── user_service.py    # User management
│   │   └── voice_service.py   # Voice processing
│   ├── repositories/          # Data access layer
│   │   ├── conversation_repository.py
│   │   ├── document_repository.py
│   │   ├── message_repository.py
│   │   └── project_repository.py
│   ├── providers/             # External service integrations
│   │   ├── chroma_provider.py # Vector store
│   │   └── ollama_provider.py # LLM inference
│   ├── core/                  # Core utilities
│   │   ├── exceptions.py      # Custom exceptions
│   │   └── logging_config.py  # Structured logging
│   └── middleware/            # Middleware
│       └── error_handler.py   # Global error handling
├── tests/                     # Test suite
│   ├── api_comprehensive_test.py  # Full API test (16/16 passing)
│   └── ...
├── migrations/                # Database migrations
├── uploads/                   # User uploads
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker build
└── pyproject.toml            # Project metadata

```

## 🧪 Testing

Run comprehensive API tests:

```bash
# Run all tests
uv run tests/api_comprehensive_test.py

# Output: 16/16 tests passing (100%)
# - Authentication (signup, login, profile)
# - Projects (CRUD operations)
# - Conversations (2 CPU models, 2 GPU models)
# - Messages retrieval
# - Statistics & cleanup
```

## ⚙️ Configuration

Key environment variables (`.env`):

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/studybuddy

# Ollama LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3-groq-tool-use:8b

# ChromaDB
CHROMA_URL=http://localhost:8000

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# GPU (optional)
GPU_TYPE=nvidia  # or amd, none
GPU_COUNT=1
```

## 🔧 Available AI Models

**Fast CPU Models** (< 2GB):
- `qwen2.5:0.5b` - 397MB - Fastest
- `gemma2:2b` - 1.6GB - Very fast
- `phi3:mini` - 2.2GB - Fast

**Quality GPU Models** (> 4GB):
- `llama3-groq-tool-use:8b` - Tool calling (default)
- `llama3:8b` - General purpose
- `qwen2.5:7b` - Multilingual
- `mistral:7b` - Strong reasoning

Download models:
```bash
docker compose exec ollama ollama pull qwen2.5:0.5b
docker compose exec ollama ollama pull llama3:8b
```

## 🧪 Testing

**Complete Test Suite:** 97 tests with 100% pass rate

### Quick Test Commands

```bash
# Run all unit tests (81 tests)
docker compose exec backend pytest -v

# Run integration tests (16 tests)
cd backend && uv run python tests/api_comprehensive_test.py
```

### Test Coverage

- **Unit Tests** - pytest with SQLite (fast, isolated)
- **Integration Tests** - Real API with PostgreSQL + AI models
- **URL Detection Tests** - 9 tests for web search functionality
- **All Components** - Repositories, services, tools, API routes

**For complete testing documentation:** See [TESTING.md](./TESTING.md)

---

## 📖 Related Documentation

- [Testing Guide](./TESTING.md) - Complete test suite documentation
- [API Audit Report](../docs/API_AUDIT_REPORT.md)
- [Future Upgrades Roadmap](../docs/FUTURE_UPGRADES_ROADMAP.md)
- [PWA Implementation Guide](../docs/PWA_IMPLEMENTATION_GUIDE.md)
- [Windows Setup Guide](../docs/WINDOWS_SETUP_GUIDE.md)

## 🔗 Related Repositories

- **Frontend**: https://github.com/akarales/study_buddy_frontend
- **Infrastructure**: https://github.com/akarales/study_buddy_Infra

## 📝 License

MIT License - Copyright © 2025 Alexandros Karales

## 👨‍💻 Author

**Alexandros Karales**
- Website: [karales.com](https://karales.com)
- Email: karales@gmail.com
- GitHub: [@akarales](https://github.com/akarales)
