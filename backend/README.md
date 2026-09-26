# Learning Debugger - Backend

The backend foundation for **Learning Debugger**, an EdTech platform designed to help students analyze, debug, and understand coding issues and concepts effectively.

This service is built with **FastAPI**, **Uvicorn**, and **Pydantic** using a modular, clean, and extensible REST API architecture.

---

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** FastAPI
- **ASGI Server:** Uvicorn
- **Data Validation & Settings:** Pydantic & Pydantic-Settings
- **Configuration:** python-dotenv
- **API Style:** RESTful API with OpenAPI / Swagger documentation

---

## Project Structure

```text
backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entrypoint & middleware configuration
│   │
│   ├── api/
│   │   ├── __init__.py      # Aggregates API routers
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── health.py    # Health check endpoint (/api/v1/health)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Environment & application configuration
│   │
│   ├── models/              # Future database / ORM models
│   │   └── __init__.py
│   │
│   ├── schemas/             # Future Pydantic request/response schemas
│   │   └── __init__.py
│   │
│   └── services/            # Future business logic services
│       └── __init__.py
│
├── .env.example             # Template for environment variables
├── .gitignore               # Git ignore rules for Python & environments
├── requirements.txt         # Production & runtime dependencies
└── README.md                # Project documentation
```

---

## Getting Started

### 1. Prerequisites

- Python 3.11 or higher installed on your system.

### 2. Navigate to the Backend Directory

Open your terminal and navigate to the `backend` directory:

```bash
cd backend
```

### 3. Create a Virtual Environment

Create an isolated virtual environment:

**On Windows (PowerShell):**
```powershell
python -m venv .venv
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
```

### 4. Activate the Virtual Environment

**On Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first, or use `.venv\Scripts\activate.bat` in CMD).*

**On macOS / Linux:**
```bash
source .venv/bin/activate
```

### 5. Install Dependencies

Upgrade pip and install the backend dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Environment Configuration (Optional)

Copy the `.env.example` file to create a local `.env` file if you wish to override default settings:

```bash
cp .env.example .env
```

*(On Windows PowerShell: `Copy-Item .env.example .env`)*

---

## Running the Server

From the `backend/` directory, start the development server with live reload:

```bash
uvicorn app.main:app --reload
```

By default, the server runs on [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## Available Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root status message verifying API availability |
| `GET` | `/api/v1/health` | Health check endpoint returning `{"status": "healthy"}` |
| `GET` | `/docs` | Interactive Swagger UI documentation |
| `GET` | `/redoc` | ReDoc alternative API documentation |
| `GET` | `/api/v1/openapi.json` | OpenAPI JSON schema |

---

## Interactive API Documentation

FastAPI provides built-in interactive documentation:

- **Swagger UI:** Open your browser and navigate to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** Open [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
