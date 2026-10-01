# 01 Project Backend API

A modular, clean architecture FastAPI backend built with SQLAlchemy 2.0 (ORM), Alembic, PostgreSQL, and Pydantic Settings, integrated with `fastapi-response-handler`.

## 🚀 Features
- **FastAPI**: High performance Python web framework.
- **SQLAlchemy 2.0 & Alembic**: Database ORM and migrations stored in `app/db/versions`.
- **Repository Pattern & Service Layer**: Separation of concern for clean code structure.
- **`fastapi-response-handler`**: Standardized HTTP exception handling and dynamic Pydantic response formatting.
- **JWT Authentication**: Password hashing, access/refresh tokens, user sessions.

---

## ⚙️ Setup & Local Development

### 1. Environment Setup
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Database Migrations
```bash
alembic upgrade head
```

### 4. Start Server
```bash
uvicorn app.main:app --reload
```
API Documentation will be available at: http://localhost:8000/docs
