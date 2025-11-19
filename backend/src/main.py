from typing import Optional
import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .sessions import create_session, get_session, append_message, set_assets
from .greenpt import get_client


app = FastAPI(title="Interview Practice Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROMPT_PATH = Path(__file__).with_name("system_prompt.txt")
try:
    DEFAULT_PROMPT_TEMPLATE = PROMPT_PATH.read_text(encoding="utf-8").strip()
except OSError:
    DEFAULT_PROMPT_TEMPLATE = (
        "You are a helpful {role} for job interview practice. "
        "Ask clear interview questions, follow up when answers are incomplete, "
        "and at the end provide concise feedback: strengths, areas to improve, and a sample improved answer. "
        "Keep responses actionable and friendly."
    )


def default_system_prompt(role: Optional[str] = None) -> str:
    role = role or "software engineering interviewer"
    try:
        return DEFAULT_PROMPT_TEMPLATE.format(role=role)
    except KeyError:
        return DEFAULT_PROMPT_TEMPLATE


class CreateSessionReq(BaseModel):
    role: Optional[str] = None
    system_prompt: Optional[str] = None
    metadata: Optional[dict] = None
    # optional textual assets to include in the system prompt
    cv: Optional[str] = None
    job_description: Optional[str] = None
    company_info: Optional[str] = None

class MessageReq(BaseModel):
    content: str


@app.post("/session")
async def create_session_endpoint(req: CreateSessionReq):
    base = req.system_prompt or default_system_prompt(req.role)
    # create the session with the base instructions; if assets were provided
    # store them and rebuild the system prompt via sessions.set_assets
    session = create_session(system_prompt=base, metadata=req.metadata or {})
    if any([req.cv, req.job_description, req.company_info]):
        set_assets(session.id, cv=req.cv, job_description=req.job_description, company_info=req.company_info, base_prompt=base)
    return {"id": session.id, "system_prompt": session.system_prompt}


# Assets are accepted only at session creation. There is no separate
# POST /session/{session_id}/assets endpoint to avoid redundancy.


@app.get("/session/{session_id}")
async def get_session_endpoint(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    return session.dict()


@app.post("/session/{session_id}/message")
async def post_message(session_id: str, req: MessageReq):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    # append user message
    append_message(session_id, role="user", content=req.content)

    # prepare messages for GreenPT: include system and history
    messages = [m.dict() for m in session.messages]

    client = get_client()
    try:
        resp = await client.chat(messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # try to extract assistant content (compatible with common chat APIs)
    assistant_text = ""
    if isinstance(resp, dict):
        choices = resp.get("choices") or []
        if choices:
            first = choices[0]
            if isinstance(first, dict) and "message" in first and isinstance(first["message"], dict):
                assistant_text = first["message"].get("content", "")
            else:
                assistant_text = first.get("text", "")

    if not assistant_text and isinstance(resp, dict):
        assistant_text = resp.get("text", "") or resp.get("response", "")

    if not assistant_text:
        assistant_text = "(no text returned from model)"

    # append assistant reply to session
    append_message(session_id, role="assistant", content=assistant_text)

    return {"reply": assistant_text, "raw": resp}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.src.main:app", host="0.0.0.0", port=port, reload=True)
