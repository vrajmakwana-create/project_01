# 01 Project Backend API

A production-ready, clean architecture FastAPI backend built with SQLAlchemy 2.0 (ORM), PostgreSQL, Alembic migrations, Pydantic V2, and automated test coverage.

## 🚀 Key Features
- **FastAPI**: High performance Python asynchronous web framework with OpenAPI / Swagger UI.
- **SQLAlchemy 2.0 & Alembic**: Fully typed declarative models, connection pooling (`pool_pre_ping=True`), and database migrations.
- **Clean Architecture**: Clear separation of concerns:
  - `app/api/`: Routing, validation, and Swagger documentation.
  - `app/services/`: Pure business logic orchestration.
  - `app/repository/`: Generic `BaseRepository` with support for soft-deletes and active filters.
  - `app/db/models/`: SQLAlchemy models with indexed foreign keys and unique constraints.
- **Security & Authentication**:
  - Argon2 password hashing via `pwdlib`.
  - JWT token lifecycle (access tokens, refresh tokens, active session management).
  - Cryptographically secure OTP generation (`secrets` module).
  - Session revocation on password changes.
  - Swagger UI `/docs` integration via `HTTPBearer`.
- **Asynchronous & Non-Blocking Design**:
  - Non-blocking thread-pooled email dispatch with automatic exponential retries.
  - Robust file upload handling with size checks and safe UUID naming.
- **Automated Testing Suite**: Full test coverage with `pytest` and `httpx`.

---

## ⚙️ Setup & Local Development

### 1. Environment Setup
```bash
python -m venv venv
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Database Migrations
```bash
alembic upgrade head
```

### 4. Run Automated Tests
```bash
pytest -v
```

### 5. Start Server
```bash
uvicorn app.main:app --reload
```
Interactive API documentation will be available at: http://localhost:8000/docs
