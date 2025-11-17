# Multi-Agent Flashcard API

Small FastAPI service and helper scripts to generate interview-style flashcards using local Ollama or Google Gemini models.  
This README explains how the repository pieces work, how to configure environment variables, and how to run the API and example scripts on Windows.

## Project layout (relevant files)
- backend/
  - main.py                - FastAPI application with async job queue + sync endpoint
  - multi_agent_system.py  - Ollama-based runner that requests a model at http://localhost:11434/api/generate
- README.md

## Requirements
- Python 3.10+ (adjust if needed)
- Windows PowerShell (commands below use PowerShell)
- If using Ollama locally:
  - Ollama installed and `ollama serve` running

Python packages (install in a virtualenv):
- fastapi, uvicorn, aiohttp, pydantic, python-dotenv, typing-extensions
- optionally: llama-index and google-genai if you plan to run v1_basic_agent.py

Example install:
```powershell

py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn aiohttp python-dotenv pydantic typing-extensions
# optional:
pip install -r requirements.txt
```

## Configuration (.env)
Create a `.env` in the project root (same folder as README) with relevant keys:

For Ollama (local, default no API key required):
```
# .env (optional for Ollama)
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_API_KEY=            # optional if your remote Ollama requires auth
```

## Running Ollama locally (if used)
1. Install Ollama: https://ollama.ai
2. Pull a small model (example):
```powershell
ollama pull llama3.2:1b
```
3. Start the Ollama HTTP server:
```powershell
ollama serve
```
4. Confirm model is available:
```powershell
ollama list
```

## Run the API (FastAPI)
From project root:
```powershell
.venv\Scripts\Activate.ps1
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open http://127.0.0.1:8000/docs for interactive API docs (Swagger UI).

## API endpoints
- GET /                 - service status
- GET /health           - health check
- POST /generate-flashcards
  - Body: { "text": "topic text", "user_id": "optional" }
  - Returns job id; processing runs in background.
- GET /job-status/{job_id}
  - Poll for status and progress
- GET /job-result/{job_id}
  - Get final result once status == completed
- POST /generate-flashcards-sync
  - Body same as above, waits for result and returns it in response

## Example curl (sync endpoint)
```powershell
curl -X POST "http://127.0.0.1:8000/generate-flashcards-sync" -H "Content-Type: application/json" -d ^
'{"text":"prepare for java technical interview"}'
```

## Memory / storage notes
- Ollama stores downloaded model files on disk (Windows: %LOCALAPPDATA%\ollama\models) and loads model weights into RAM/VRAM when serving. Choose smaller models (e.g., 1B) to reduce disk & memory usage.
- The backend code only holds responses in memory and does not persist large files.
- To free disk space: `ollama remove <model>`.

## Troubleshooting
- "Connection refused" to Ollama: ensure `ollama serve` is running and the URL matches `multi_agent_system.py`.
- JSON parse errors from model output: multi_agent_system.py includes a repair helper; inspect logs printed by the app for raw model output.
- Missing environment variables: ensure `.env` is present and `python-dotenv` loads it (load_dotenv() is used in some scripts).


## License & Safety
- This repository is a simple demo. Check model licenses before production use and ensure you comply with the model provider terms.

If you want, I can produce a ready-to-add README.md file with this exact content or add example Postman/cURL snippets for the async job flow.