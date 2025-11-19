# Backend (Interview Practice) — Skeleton

This small FastAPI backend is a hackathon skeleton for an LLM-powered interview practice tool.

Environment
- `GREENPT_API_KEY` — your GreenPT API key
- `GREENPT_API_URL` — optional, override default GreenPT chat/completions endpoint
- `CORS_ORIGIN` — optional, defaults to `*`

Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run (development)
```bash
export GREENPT_API_KEY="sk-..."
uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints
- `POST /session` — create a new practice session. Body: `{ "role": "interviewer role" }`
- `GET /session/{id}` — get session state
- `POST /session/{id}/message` — send a message (user answer); returns model reply

Notes
- Sessions are stored in-memory for the prototype. Replace with a DB for persistence.
- The GreenPT client is in `backend/src/greenpt.py`. It expects OpenAI-like response JSON with `choices`.
