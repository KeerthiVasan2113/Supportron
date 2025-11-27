# Supportron

A hybrid chat system using Ollama qwen3.2:3b and RAG (Retrieval-Augmented Generation) for technical documentation support.

## Project Structure

```
Supportron/
├── backend/              # FastAPI backend server
│   ├── app/             # Main application code
│   │   ├── api/         # API routes and schemas
│   │   ├── core/        # Configuration and utilities
│   │   ├── db/          # Database management
│   │   ├── services/    # Business logic
│   │   └── utils/       # Helper functions
│   └── requirements.txt # Python dependencies
├── data-processing/     # RAG model and data processing
│   ├── vector_db/       # Vector database storage
│   └── requirements.txt # Python dependencies
└── frontend/            # Next.js frontend application
    └── package.json     # Node.js dependencies
```

## Prerequisites

1. **Python 3.10+** - Required for backend and data processing
2. **Node.js 18+** - Required for frontend
3. **Ollama** - Required for running LLM models
   - Download from: https://ollama.ai
   - Install and ensure it's running

## Setup Instructions

### 1. Install Ollama Model

Before running the application, you need to pull the required Ollama model:

```powershell
ollama pull qwen3.2:3b
```

### 2. Backend Setup

1. Navigate to the backend directory:
```powershell
cd backend
```

2. Create a virtual environment (recommended):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:
```powershell
pip install -r requirements.txt
```

### 3. Data Processing Setup

1. Navigate to the data-processing directory:
```powershell
cd ..\data-processing
```

2. Create a virtual environment (recommended):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:
```powershell
pip install -r requirements.txt
```

4. Build the RAG model (if not already built):
```powershell
python build_rag_model.py
```

Or run the full pipeline:
```powershell
python run_pipeline.py
```

### 4. Frontend Setup

1. Navigate to the frontend directory:
```powershell
cd ..\frontend
```

2. Install dependencies:
```powershell
npm install
```

## Running the Application

### Start Ollama (if not running)

Make sure Ollama is running before starting the backend:

```powershell
ollama serve
```

Or if Ollama is installed as a service, it should start automatically.

### Start the Backend Server

1. Navigate to the backend directory:
```powershell
cd backend
```

2. Activate virtual environment (if using one):
```powershell
.\venv\Scripts\Activate.ps1
```

3. Start the server:
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or using the main module directly:
```powershell
python -m app.main
```

The backend will be available at: `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### Start the Frontend

1. Navigate to the frontend directory:
```powershell
cd frontend
```

2. Start the development server:
```powershell
npm run dev
```

The frontend will be available at: `http://localhost:3000`

## API Endpoints

### Health Check
- `GET /` - Root endpoint with service information
- `GET /health` - Health check endpoint
- `GET /api/v1/health` - V1 health check endpoint

### Chat
- `POST /api/chat` - Legacy chat endpoint (backward compatible)
- `POST /api/v1/chat` - V1 chat endpoint with conversation history support

### Database Operations
- `POST /api/v1/db/universal` - Universal database CRUD operations
- `POST /api/v1/db/table-info` - Get table information
- `GET /api/v1/db/databases` - List all databases
- `GET /api/v1/db/{db_name}/tables` - List tables in a database

## Configuration

### Backend Configuration

Edit `backend/app/core/config.py` to modify:
- Model name (default: qwen3.2:3b)
- RAG configuration (distance thresholds, top docs)
- CORS origins
- Server host and port

### Frontend Configuration

Edit `frontend/lib/api.ts` to modify:
- API base URL (default: `https://supportron-api.loca.lt`)
- API version

## Development

### Backend Development

The backend uses FastAPI with automatic reload. Changes to Python files will trigger a reload.

### Frontend Development

The frontend uses Next.js with hot module replacement. Changes to React components will update automatically.

### Logging

- Backend logs: `backend/logs/api.log`
- Data processing logs: `data-processing/logs/`

## Troubleshooting

### Ollama Connection Issues

If you see errors about Ollama not being available:

1. Verify Ollama is running:
```powershell
ollama list
```

2. Check if model is pulled:
```powershell
ollama list
```

3. Test Ollama API:
```powershell
curl http://localhost:11434/api/tags
```

### RAG Model Not Found

If you see errors about the vector database:

1. Ensure the vector database exists:
```powershell
Test-Path data-processing\vector_db\faiss.index
```

2. Rebuild the RAG model if needed:
```powershell
cd data-processing
python build_rag_model.py
```

### Port Already in Use

If port 8000 or 3000 is already in use:

1. Backend: Change port in `backend/app/core/config.py` or use:
```powershell
python -m uvicorn app.main:app --port 8001
```

2. Frontend: Change port in `frontend/package.json` or use:
```powershell
npm run dev -- -p 3001
```

## Project Features

- **Chat System**: Uses Ollama qwen3.2:3b for intelligent responses
- **RAG Integration**: Retrieves relevant technical documentation for context-aware answers
- **Conversation History**: Maintains context across multiple messages
- **Code Formatting**: Automatically detects and formats code blocks in responses
- **Universal Database API**: Dynamic CRUD operations on SQLite databases
- **Modern Frontend**: Next.js with TypeScript and TailwindCSS

## License

See LICENSE file for details.

