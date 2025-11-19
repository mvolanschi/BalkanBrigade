from typing import Optional
import asyncio
import os
from pathlib import Path
import io

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .sessions import create_session, get_session, append_message, set_assets
from .greenpt import get_client

# NEW: imports for CV text extraction
from pypdf import PdfReader
import docx as docx_lib


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

# ---------- helpers for CV text extraction ----------

def _get_ext(filename: str) -> str:
    return os.path.splitext(filename.lower())[1]


def extract_text_from_cv_file(filename: str, data: bytes) -> str:
    """Very simple text extractor for CV files.

    Supports: .pdf, .docx
    """
    ext = _get_ext(filename)

    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        parts = []
        for page in reader.pages:
            txt = page.extract_text() or ""
            parts.append(txt)
        text = "\n".join(parts).strip()
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF CV.")
        return text

    elif ext == ".docx":
        doc = docx_lib.Document(io.BytesIO(data))
        parts = [para.text for para in doc.paragraphs if para.text]
        text = "\n".join(parts).strip()
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from DOCX CV.")
        return text

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported CV file type: {ext}. Please upload a PDF or DOCX.",
        )


async def evaluate_cv(
    cv_text: str,
    job_description: str,
    company_info: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 600,
) -> dict:
    """Ask GreenPT to evaluate a CV against a job description and company context."""

    if not cv_text.strip():
        raise HTTPException(status_code=400, detail="CV text is required for evaluation.")

    system_prompt = (
        "You are an expert technical recruiter. Score the candidate CV against the job "
        "requirements from 0 to 100 and list concrete strengths, improvements, and a one-paragraph summary. "
        "Respond exactly in this format: '\nSCORE: <number>' followed by sections 'STRENGTHS:', 'IMPROVEMENTS:' and 'SUMMARY:' with bullet points. "
        "Use concise bullet points (max 3 per section) and be direct."
    )

    user_payload = (
        "Candidate CV:\n"
        f"{cv_text.strip()}\n\n"
        "Job Description:\n"
        f"{(job_description or '').strip() or '(not provided)'}\n\n"
        "Company Info:\n"
        f"{(company_info or '').strip() or '(not provided)'}"
    )

    client = get_client()
    try:
        resp = await client.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to evaluate CV: {exc}")

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
        raise HTTPException(status_code=502, detail="GreenPT returned an empty evaluation.")

    return {"reply": assistant_text.strip()}


# ---------- endpoint to turn CV file into text (still available if needed) ----------

@app.post("/cv-text")
async def extract_cv_text(cv: UploadFile = File(...)):
    """Accept a CV file and return extracted plain text.

    Frontend will send FormData with field name 'cv'.
    """
    try:
        data = await cv.read()
        text = extract_text_from_cv_file(cv.filename, data)
    except HTTPException:
        # propagate our HTTPExceptions (unsupported type, etc.)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract CV text: {e}")

    return {"text": text}


# ---------- NEW: combined endpoint: file + texts -> session ----------

@app.post("/session-from-upload")
async def create_session_from_upload(
    cv: UploadFile = File(...),
    job_description: str = Form(...),
    company_info: str = Form(""),
    role: Optional[str] = Form(None),
):
    """
    Accept a CV file plus job & company text in a single request, then:

    - Extract CV text
    - Create a session
    - Attach CV, job description and company info as assets
    - Evaluate CV
    - Return { id, cv_eval }
    """
    # 1) Extract text from the uploaded CV
    try:
        data = await cv.read()
        cv_text = extract_text_from_cv_file(cv.filename, data)
    except HTTPException:
        # Propagate known HTTP errors as-is (e.g. unsupported file types)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract CV text: {e}")

    # 2) Build base system prompt
    base = default_system_prompt(role=role)

    # 3) Create a new session
    session = create_session(system_prompt=base, metadata={})

    # 4) Attach assets (CV text + job description + company info)
    set_assets(
        session.id,
        cv=cv_text,
        job_description=job_description,
        company_info=company_info,
        base_prompt=base,
    )

    # 5) Evaluate CV with GreenPT
    cv_eval = await evaluate_cv(
        cv_text=cv_text,
        job_description=job_description,
        company_info=company_info,
    )

    # 5) Return session info
    return {"id": session.id, "cv_eval": cv_eval}


# ---------- EXISTING SESSION ENDPOINTS (unchanged) ----------

@app.post("/session")
async def create_session_endpoint(req: CreateSessionReq):
    base = req.system_prompt or default_system_prompt(req.role)
    # create the session with the base instructions; if assets were provided
    # store them and rebuild the system prompt via sessions.set_assets
    session = create_session(system_prompt=base, metadata=req.metadata or {})
    if any([req.cv, req.job_description, req.company_info]):
        set_assets(
            session.id,
            cv=req.cv,
            job_description=req.job_description,
            company_info=req.company_info,
            base_prompt=base,
        )
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
