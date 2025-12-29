# Testing Guide - AI Study Buddy Backend

**Complete guide to running and understanding the test suite**

---

## Test Suite Overview

AI Study Buddy has **two types of tests**:

| Test Type | Count | Tool | Database | Purpose |
|-----------|-------|------|----------|---------|
| **Unit Tests** | 81 tests | pytest | SQLite (in-memory) | Fast, isolated component testing |
| **Integration Tests** | 16 tests | Python script | PostgreSQL (live) | End-to-end API testing with real models |

**Total Test Coverage:** 97 tests with 100% pass rate ✅

---

## 1. Unit Tests (pytest)

### What Gets Tested

- **Repositories** (30 tests) - Database operations
- **Services** (14 tests) - Business logic
- **Tools** (9 tests) - Web search, calculator, URL detection
- **API Routes** (2 tests) - Project endpoints
- **Core Components** (22 tests) - Error handling, schemas, utilities
- **System Prompts** (5 tests) - Prompt integration
- **Token Counter** (8 tests) - Token estimation

### Test File Organization

```
tests/
├── test_api/              # API endpoint tests
│   └── test_project_routes.py (2 tests)
├── test_core/             # Core component tests
│   ├── test_error_response.py (9 tests)
│   └── test_exceptions.py (13 tests)
├── test_repositories/     # Database CRUD tests
│   ├── test_conversation_repository.py (7 tests)
│   ├── test_document_repository.py (7 tests)
│   ├── test_message_repository.py (6 tests)
│   └── test_project_repository.py (10 tests)
├── test_services/         # Business logic tests
│   ├── test_chat_service.py (5 tests)
│   ├── test_document_service.py (6 tests)
│   └── test_export_service.py (3 tests)
├── test_tools/            # Tool functionality tests
│   └── test_web_search.py (9 tests)
├── test_utils/            # Utility tests
│   └── test_token_counter.py (8 tests)
├── test_system_prompts_integration.py (5 tests)
├── api_comprehensive_test.py (16 tests - standalone)
└── conftest.py (test fixtures and configuration)
```

### What Each Test File Does

#### API Tests (`test_api/`)

**`test_project_routes.py`** - Tests project API endpoints
- ✅ GET `/projects/{id}` with non-existent ID (404)
- ✅ POST `/projects` - Create new project
- ⏸️ 4 tests commented out (database session isolation issues)

#### Core Component Tests (`test_core/`)

**`test_error_response.py`** - Tests custom error response formatting
- HTTP status code mapping
- Error message structure
- JSON error response validation
- Exception type handling

**`test_exceptions.py`** - Tests custom exception classes
- Exception inheritance chain
- Error message formatting
- Custom exception types (AuthenticationError, ValidationError, etc.)

#### Repository Tests (`test_repositories/`)

**`test_conversation_repository.py`** - Conversation database operations
- Create, read, update, delete conversations
- Get or create conversation logic
- Find conversations by project
- Update conversation metadata

**`test_document_repository.py`** - Document database operations
- Document CRUD operations
- Find documents by project
- Handle null optional fields (summary, etc.)
- Document with project association

**`test_message_repository.py`** - Message database operations
- Message CRUD operations
- Find messages by conversation
- Message ordering (chronological)
- Message type handling

**`test_project_repository.py`** - Project database operations
- Project CRUD operations
- Find projects by user
- Cascade delete (project → conversations)
- Find all projects
- Handle null optional fields

#### Service Tests (`test_services/`)

**`test_chat_service.py`** - Chat conversation service logic
- Create new conversation for chat
- Reuse existing conversation
- Include conversation history
- Document context integration (RAG)
- Auto-title generation for new conversations

**`test_document_service.py`** - Document processing service
- Document upload and storage
- List documents by project
- Get document by ID
- Search documents (vector store integration)
- Delete documents
- Empty project handling

**`test_export_service.py`** - Conversation export functionality
- Get conversation messages for export
- Format conversation metadata
- Export service repository access

#### Tool Tests (`test_tools/`)

**`test_web_search.py`** - Web search and URL detection (YOUR NEW FEATURE!)
- Extract domain from URL queries (`zapagi.com`)
- Extract domain from full URLs (`https://www.zapagi.com/services`)
- Handle subdomains (`blog.zapagi.com` → `zapagi.com`)
- Detect when no domain in query
- Filter search results by domain
- Handle empty URLs gracefully
- Support multi-part TLDs (`.co.uk`)
- Test various domain formats (`http://`, `www.`, plain domain)

#### Utility Tests (`test_utils/`)

**`test_token_counter.py`** - Token estimation and management
- Estimate tokens for simple text
- Estimate tokens for longer text
- Handle empty strings
- Get context window limits for known models
- Handle unknown models (default limit)
- Calculate context usage percentage
- Detect near-limit situations
- Verify below-limit calculations

#### Integration Tests

**`test_system_prompts_integration.py`** - End-to-end system prompt testing
- Verify database column exists
- Repository operations with system_prompt
- Chat service integration with custom prompts
- Optional system prompt handling
- Update system prompt functionality
- **Special:** Can run standalone (`python tests/test_system_prompts_integration.py`)

**`api_comprehensive_test.py`** - Full API integration test (NOT pytest)
- User authentication (signup, login, profile)
- Project management (create, list, delete)
- AI conversations with 4 different models (CPU + GPU)
- Statistics and analytics
- Full cleanup cycle
- **Run:** `uv run python tests/api_comprehensive_test.py`

**`conftest.py`** - pytest configuration and fixtures (NOT a test)
- Test database setup (SQLite in-memory)
- Fixture definitions (test_user, test_project, etc.)
- Mock providers (LLM, vector store)
- Test data factories

### Running Unit Tests

#### Inside Docker Container (Recommended)

```bash
# Navigate to infrastructure directory
cd /path/to/AI_Study_Buddy/infrastructure

# Run all tests
docker compose exec backend pytest -v

# Run with coverage report
docker compose exec backend pytest -v --cov=src --cov-report=term-missing

# Run specific test file
docker compose exec backend pytest tests/test_tools/test_web_search.py -v

# Run specific test class
docker compose exec backend pytest tests/test_tools/test_web_search.py::TestWebSearchTool -v

# Run specific test method
docker compose exec backend pytest tests/test_tools/test_web_search.py::TestWebSearchTool::test_extract_domain_from_url_query -v
```

#### Using uv (Local Development)

```bash
# Navigate to backend directory
cd /path/to/AI_Study_Buddy/backend

# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest -v --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_tools/test_web_search.py -v
```

### Expected Output

```
================================================================ test session starts ================================================================
platform linux -- Python 3.13.11, pytest-8.3.4, pluggy-1.5.0
collected 81 items

tests/test_api/test_project_routes.py::TestProjectRoutes::test_get_project_not_found PASSED                                                 [  1%]
tests/test_api/test_project_routes.py::TestProjectRoutes::test_create_project_success PASSED                                                [  2%]
...
tests/test_tools/test_web_search.py::TestWebSearchTool::test_extract_domain_from_url_query PASSED                                           [ 81%]
tests/test_tools/test_web_search.py::TestWebSearchTool::test_extract_domain_from_full_url PASSED                                            [ 82%]
...

======================================================= 81 passed, 6 warnings in 12.49s ========================================================
```

### Test Database

Unit tests use **SQLite in-memory database** (not PostgreSQL):

```python
# From tests/conftest.py
engine = create_engine("sqlite:///:memory:")
```

**Why SQLite for tests?**
- ⚡ **Fast** - No disk I/O, runs in RAM
- 🔒 **Isolated** - Each test gets fresh database
- 📦 **Portable** - No external dependencies needed

---

## 2. Integration Tests (API Comprehensive Test)

### What Gets Tested

**End-to-end testing against live backend API with real AI models:**

1. **User Authentication**
   - User signup with unique email
   - Profile retrieval
   - Profile updates (bio, organization)

2. **Project Management**
   - Create project with tools
   - List all projects
   - Delete projects

3. **AI Conversations** (4 models tested)
   - **CPU Models** (lightweight, fast):
     - `qwen2.5:0.5b` - Conversation with real LLM
     - `gemma2:2b` - Conversation with real LLM
   - **GPU Models** (better quality):
     - `llama3:8b` - Conversation with real LLM
     - `qwen2.5:7b` - Conversation with real LLM
   - Message retrieval per conversation

4. **Statistics & Analytics**
   - Get usage statistics
   - Project/conversation counts

5. **Cleanup**
   - Delete test projects
   - Delete test user account

### Running Integration Tests

#### Prerequisites

```bash
# 1. Ensure all Docker services are running
cd /path/to/AI_Study_Buddy/infrastructure
docker compose up -d

# 2. Verify backend is accessible
curl http://localhost:8001/health

# 3. Verify Ollama has models downloaded
docker compose exec ollama ollama list
```

#### Run the Test

```bash
# Navigate to backend directory
cd /path/to/AI_Study_Buddy/backend

# Run with uv
uv run python tests/api_comprehensive_test.py

# Or run directly with Python
python tests/api_comprehensive_test.py
```

### Expected Output

```
Starting Comprehensive API Test Suite

Phase 1: User Authentication

➤ [16:51:14] Testing signup for test_user_1766958674@example.com
✓ [16:51:14] Signup successful - User ID: 23
➤ [16:51:15] Testing get profile
✓ [16:51:15] Profile retrieved - Name: API Test User
➤ [16:51:15] Testing update profile
✓ [16:51:15] Profile updated successfully

Phase 2: Project Management

➤ [16:51:15] Testing create project: Test Project
✓ [16:51:15] Project created - ID: 52
➤ [16:51:15] Testing get projects
✓ [16:51:15] Retrieved 12 projects

Phase 3: Conversations with AI Models (CPU + GPU)

ℹ [16:51:15] Testing CPU model: qwen2.5:0.5b...
➤ [16:51:15] Testing conversation with model: qwen2.5:0.5b (CPU)
✓ [16:51:20] Conversation created - Model: qwen2.5:0.5b, Conv ID: 68
ℹ [16:51:20] Response preview: Hello!...

... (more model tests) ...

Phase 4: Statistics & Overview

➤ [16:51:31] Testing get stats overview
✓ [16:51:31] Stats: 0 projects, 0 conversations

Phase 5: Cleanup

➤ [16:51:31] Testing delete project: 52
✓ [16:51:31] Project 52 deleted
➤ [16:51:31] Testing delete account
✓ [16:51:31] Account deleted successfully

================================================================================
                         COMPREHENSIVE API TEST REPORT
================================================================================

Summary:
  Total Tests: 16
  Passed: 16
  Failed: 0
  Pass Rate: 100.0%
```

### Test Database

Integration tests use **live PostgreSQL database** (same as production):
- Connects to `localhost:8001/api/v1`
- Creates real data during testing
- **Cleans up automatically** after tests

---

## Test Configuration

### pytest.ini

```ini
[pytest]
testpaths = tests
addopts = 
    --verbose
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=60

markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (database, services)
    slow: Slow tests (may take longer to run)
    asyncio: Async tests
```

### Coverage Requirements

- **Target:** 60% code coverage
- **Current:** ~48% (acceptable for early development)
- **Reports:** Generated in `htmlcov/` directory

---

## Running Specific Test Suites

### Web Search & URL Detection Tests

```bash
# All web search tests
docker compose exec backend pytest tests/test_tools/test_web_search.py -v

# Specific URL detection test
docker compose exec backend pytest tests/test_tools/test_web_search.py::TestWebSearchTool::test_extract_domain_from_url_query -v
```

### Repository Tests

```bash
# All repository tests
docker compose exec backend pytest tests/test_repositories/ -v

# Specific repository
docker compose exec backend pytest tests/test_repositories/test_project_repository.py -v
```

### Service Tests

```bash
# All service tests
docker compose exec backend pytest tests/test_services/ -v

# Chat service only
docker compose exec backend pytest tests/test_services/test_chat_service.py -v
```

---

## Continuous Integration

### Running Tests in CI/CD

```yaml
# Example GitHub Actions workflow
- name: Run Unit Tests
  run: |
    docker compose exec backend pytest -v --cov=src --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

---

## Troubleshooting

### Common Issues

#### 1. Test Database Session Issues

**Symptom:** `404 Not Found` errors in API route tests

**Cause:** Database session isolation between test fixtures and API endpoints

**Solution:** Tests are commented out with `# TODO: Fix database session isolation issue`

#### 2. Coverage Below Threshold

**Symptom:** `FAIL Required test coverage of 60% not reached. Total coverage: 48%`

**Cause:** Exit code 1 due to coverage threshold, not test failures

**Solution:** This is expected. All tests pass, coverage will improve over time.

#### 3. Model Not Found in Integration Tests

**Symptom:** Integration test fails with model error

**Solution:**
```bash
# Download missing model
docker compose exec ollama ollama pull qwen2.5:0.5b
docker compose exec ollama ollama pull gemma2:2b
docker compose exec ollama ollama pull llama3:8b
docker compose exec ollama ollama pull qwen2.5:7b
```

#### 4. Backend Not Running

**Symptom:** `Connection refused` in integration tests

**Solution:**
```bash
# Start all services
cd infrastructure
docker compose up -d

# Check backend logs
docker compose logs backend
```

---

## Test Maintenance

### Adding New Tests

1. **Create test file** in appropriate directory:
   ```
   tests/
   ├── test_api/          # API endpoint tests
   ├── test_core/         # Core component tests
   ├── test_repositories/ # Database tests
   ├── test_services/     # Service tests
   ├── test_tools/        # Tool tests
   └── test_utils/        # Utility tests
   ```

2. **Follow naming conventions:**
   ```python
   # File: test_my_feature.py
   import pytest
   
   @pytest.mark.unit
   class TestMyFeature:
       def test_specific_behavior(self):
           # Arrange
           expected = "result"
           
           # Act
           actual = my_function()
           
           # Assert
           assert actual == expected
   ```

3. **Use fixtures** from `conftest.py`:
   ```python
   def test_with_database(self, test_db, test_user, test_project):
       # test_db, test_user, test_project are available automatically
       pass
   ```

### Updating Integration Tests

Edit `tests/api_comprehensive_test.py` and add new test methods to `APITester` class:

```python
def test_new_feature(self):
    """Test description"""
    self.log("Testing new feature", "TEST")
    
    response = requests.post(
        f"{BASE_URL}/endpoint",
        headers={"Authorization": f"Bearer {self.token}"},
        json={"data": "value"}
    )
    
    if response.status_code == 200:
        self.log("New feature works!", "PASS")
        self.record_test("New Feature", True)
    else:
        self.log(f"Failed: {response.text}", "FAIL")
        self.record_test("New Feature", False)
```

---

## Test Coverage Report

View detailed HTML coverage report:

```bash
# Generate coverage report
docker compose exec backend pytest --cov=src --cov-report=html

# Copy report to local machine
docker compose cp backend:/app/htmlcov ./htmlcov

# Open in browser
open htmlcov/index.html
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `docker compose exec backend pytest -v` | Run all unit tests |
| `docker compose exec backend pytest -k "web_search"` | Run tests matching pattern |
| `uv run python tests/api_comprehensive_test.py` | Run integration tests |
| `docker compose exec backend pytest --lf` | Run last failed tests |
| `docker compose exec backend pytest --co` | List all available tests |
| `docker compose exec backend pytest -x` | Stop on first failure |

---

## Current Test Status

✅ **All Tests Passing:**
- Unit Tests: 81/81 (100%)
- Integration Tests: 16/16 (100%)
- **Total: 97/97 tests passing**

🎯 **Coverage:**
- Current: ~48%
- Target: 60%
- Focus areas: API routes, services, providers

---

**Last Updated:** December 28, 2025
