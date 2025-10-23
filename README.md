
***

# Coffee Shop API 

A production-ready FastAPI application for user management with JWT authentication, email verification, role-based access control, and automated cleanup of unverified users.

## Features

- ✅ User registration with email validation
- ✅ JWT authentication (access + refresh tokens)
- ✅ Email verification with 6-digit codes (24-hour expiration)
- ✅ Role-based access control (User \& Admin)
- ✅ User management CRUD operations
- ✅ Automatic cleanup of unverified users after 2 days (Celery)
- ✅ Async SQLAlchemy with PostgreSQL
- ✅ Docker containerization
- ✅ OpenAPI documentation (Swagger UI)


## Technology Stack

- **FastAPI** - Modern async web framework
- **Python 3.11+** - Programming language
- **SQLAlchemy 2.0+** - Async ORM
- **PostgreSQL 15+** - Production database (SQLite supported for dev)
- **Redis 7+** - Message broker for Celery
- **Celery 5.3+** - Distributed task queue
- **python-jose** - JWT token handling
- **passlib[bcrypt]** - Password hashing
- **uv** - Fast Python package manager
- **Docker \& Docker Compose** - Containerization


## Quick Start with Docker

```bash
# Clone repository
git clone <your-repo-url>
cd coffee-shop-api

# Create .env file from example
cp .env.example .env

# Generate SECRET_KEY and add to .env
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Start all services
docker-compose up -d

# Create admin user (default: admin@email.com / admin123!)
docker-compose exec api python create_admin.py

# Access API documentation
open http://localhost:8000/docs
```


## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or SQLite for development)
- Redis 7+ (for Celery)
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Docker \& Docker Compose (optional)


### Local Setup with uv

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
uv sync

# Create .env file
cp .env.example .env

# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Add the generated key to .env file

# Start PostgreSQL (or use SQLite)
docker run --name coffee-db -p 5432:5432 \
  -e POSTGRES_USER=coffee_user \
  -e POSTGRES_PASSWORD=coffee_pass \
  -e POSTGRES_DB=coffee_shop \
  -d postgres:15-alpine

# Start Redis
docker run --name coffee-redis -p 6379:6379 -d redis:7-alpine

# Run FastAPI application
uv run fastapi dev app/main.py

# In another terminal: Start Celery
uv run celery -A app.core.celery_app worker --beat --loglevel=info
```


## Running with Docker

### Start All Services

```bash
docker-compose up -d
```

This starts:

- **API** (FastAPI) - http://localhost:8000
- **PostgreSQL** - Database on port 5432
- **Redis** - Message broker on port 6379
- **Celery Worker** - Background task processor
- **Celery Beat** - Task scheduler


### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f celery-worker
```


### Stop Services

```bash
docker-compose down

# Remove volumes (clean database)
docker-compose down -v
```


## API Endpoints

### Authentication (`/auth`)

| Method | Endpoint | Description | Auth Required |
| :-- | :-- | :-- | :-- |
| POST | `/auth/signup` | Register new user | No |
| POST | `/auth/login` | User login | No |
| POST | `/auth/verify` | Verify email with code | Yes |
| POST | `/auth/resend-verification` | Resend verification code | Yes |
| POST | `/auth/refresh` | Refresh access token | No |

### User Management (`/users`)

| Method | Endpoint | Description | Auth Required | Admin Only |
| :-- | :-- | :-- | :-- | :-- |
| GET | `/users/me` | Get current user profile | Yes | No |
| GET | `/users` | List all users | Yes | Yes |
| GET | `/users/{id}` | Get user by ID | Yes | Yes |
| PATCH | `/users/{id}` | Update user | Yes | Yes |
| DELETE | `/users/{id}` | Delete user | Yes | Yes |

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc


## Example Requests

### Register User

```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```


### Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```


### Get Current User

```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```


### Verify Email

```bash
curl -X POST "http://localhost:8000/auth/verify" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "123456"}'
```


## Creating Admin User

### Using create_admin.py Script

**Default credentials:**

```bash
# Uses default: admin@email.com / admin123!
docker-compose exec api python create_admin.py

# Or locally
uv run python create_admin.py
```

**Custom credentials:**

```bash
docker-compose exec api python create_admin.py admin@example.com MySecurePass123
```


### Default Admin Credentials

- **Email**: `admin@email.com`
- **Password**: `admin123!`


## Testing

### Run API Tests

```bash
# Start server first
uv run fastapi dev app/main.py

# In another terminal
uv run python test_api.py
```


### Run Cleanup Tests

```bash
uv run python test_cleanup.py
```


### Test in Docker

```bash
docker-compose exec api python test_api.py
docker-compose exec api python test_cleanup.py
```


## Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://coffee_user:coffee_pass@localhost:5432/coffee_shop
# For Docker: postgresql+asyncpg://coffee_user:coffee_pass@db:5432/coffee_shop

# PostgreSQL (for Docker)
POSTGRES_USER=coffee_user
POSTGRES_PASSWORD=coffee_pass
POSTGRES_DB=coffee_shop

# JWT
SECRET_KEY=your-secret-key-min-32-characters  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Verification
VERIFICATION_CODE_EXPIRE_HOURS=24
UNVERIFIED_USER_DELETE_DAYS=2

# Application
APP_NAME=Coffee Shop API
DEBUG=true

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
# For Docker: redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```


## Database Schema

### Users Table

| Column | Type | Description |
| :-- | :-- | :-- |
| id | Integer | Primary key |
| email | String | Unique user email |
| hashed_password | String | Bcrypt hashed password |
| first_name | String | Optional first name |
| last_name | String | Optional last name |
| role | Enum | USER or ADMIN |
| is_verified | Boolean | Email verification status |
| verification_code | String | Hashed verification code |
| verification_code_expires_at | DateTime | Code expiration |
| created_at | DateTime | Account creation timestamp |
| updated_at | DateTime | Last update timestamp |

## Background Tasks (Celery)

### Cleanup Task

Automatically deletes unverified users older than 2 days (configurable).

**Schedule**: Daily at 3:00 AM UTC

**Configuration**: `UNVERIFIED_USER_DELETE_DAYS` in `.env`

### Running Celery

**Development (combined):**

```bash
uv run celery -A app.core.celery_app worker --beat --loglevel=info
```

**Production (separate processes):**

```bash
# Terminal 1: Worker
uv run celery -A app.core.celery_app worker --loglevel=info

# Terminal 2: Beat scheduler
uv run celery -A app.core.celery_app beat --loglevel=info
```

**Docker:**

```bash
# Included in docker-compose.yml
docker-compose up -d celery-worker celery-beat
```


## Project Structure

```
coffee-shop-api/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application
│   ├── api/                       # Route handlers
│   │   ├── auth.py                # Authentication endpoints
│   │   └── users.py               # User management endpoints
│   ├── core/                      # Core configuration
│   │   ├── config.py              # Settings
│   │   ├── security.py            # JWT & passwords
│   │   ├── dependencies.py        # Dependency injection
│   │   └── celery_app.py          # Celery setup
│   ├── db/
│   │   └── database.py            # Database connection
│   ├── models/
│   │   └── user.py                # User model
│   ├── schemas/                   # Pydantic schemas
│   │   ├── auth.py
│   │   └── user.py
│   ├── services/                  # Business logic
│   │   ├── auth_service.py
│   │   └── user_service.py
│   └── tasks/                     # Celery tasks
│       └── cleanup.py             # Cleanup unverified users
├── test_api.py                    # API tests
├── test_cleanup.py                # Cleanup task tests
├── create_admin.py                # Admin user creation
├── pyproject.toml                 # Dependencies
├── Dockerfile
├── docker-compose.yml
├── .env                           # Environment variables
├── .env.example                   # Environment template
└── README.md                      # This file
```



## Database Access

### PostgreSQL (Docker)

```bash
# Connect to database
docker-compose exec db psql -U coffee_user -d coffee_shop

# List tables
\dt

# View users
SELECT id, email, role, is_verified FROM users;

# Exit
\q
```
