from typing import Optional, Any
import asyncio
import os
from pathlib import Path
import io

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
import logging

from .sessions import create_session, get_session, append_message, set_assets, set_system_prompt
from .greenpt import get_client
from .prompt_store import get_prompt, DEFAULT_PROMPT

# NEW: imports for CV text extraction
from pypdf import PdfReader
import docx as docx_lib

base_path = Path(__file__).resolve()
load_dotenv(base_path.parents[2] / ".env")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Interview Practice Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageReq(BaseModel):
    content: str


class SettingsReq(BaseModel):
    technicality: int
    politeness: int
    difficulty: int

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


def _extract_assistant_text(resp: Any) -> str:
    """Robustly extract assistant text from common model response shapes.

    Tries several common locations used by chat/completion APIs, including:
    - resp['choices'][0]['message']['content']
    - resp['choices'][0]['delta']['content']
    - resp['choices'][0]['text']
    - top-level 'text', 'response', or 'reply' fields
    Returns empty string when no content was found.
    """
    if not resp:
        return ""

    # If dict-like response (common)
    if isinstance(resp, dict):
        choices = resp.get("choices") or []
        if choices and isinstance(choices, list):
            first = choices[0]
            if isinstance(first, dict):
                # new-style chat: message.content
                msg = first.get("message")
                if isinstance(msg, dict):
                    content = msg.get("content")
                    if content:
                        return content

                # streaming delta: delta.content
                delta = first.get("delta")
                if isinstance(delta, dict):
                    content = delta.get("content")
                    if content:
                        return content

                # older completions: text
                text = first.get("text")
                if text:
                    return text

        # fallback top-level
        for key in ("text", "response", "reply"):
            v = resp.get(key)
            if v:
                return v

    # If it's already a string, return as-is
    if isinstance(resp, str):
        return resp

    return ""


async def evaluate_cv(
    cv_text: str,
    job_description: str,
    company_info: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 600,
) -> dict:
    """Ask GreenPT to evaluate how well a CV fits a role and return the formatted reply."""

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

    assistant_text = _extract_assistant_text(resp)
    if not assistant_text:
        logging.warning("Empty assistant text for CV evaluation; raw response: %s", resp)
        raise HTTPException(status_code=502, detail="GreenPT returned an empty evaluation.")

    # Validate basic structure we expect: SCORE, STRENGTHS, IMPROVEMENTS, SUMMARY
    def _looks_like_eval(text: str) -> bool:
        t = (text or "").upper()
        return all(k in t for k in ("SCORE:", "STRENGTHS:", "IMPROVEMENTS:", "SUMMARY:"))

    if not _looks_like_eval(assistant_text):
        logging.info("Evaluation missing expected sections; attempting one-pass reformat.")
        # Ask the model to reformat the assistant output into the required sections.
        try:
            reform_prompt = (
                "The assistant produced the following evaluation, but it may not follow the required format.\n"
                "Please reformat the content exactly into the following sections (use the same content where possible):\n"
                "SCORE: <number>\nSTRENGTHS:\n- ...\nIMPROVEMENTS:\n- ...\nSUMMARY:\n<one paragraph>\n\n"
                "Here is the original evaluation:\n---\n" + assistant_text + "\n---\n"
            )

            resp2 = await client.chat(
                [
                    {"role": "system", "content": "You are a helpful formatter that converts text into a strict labeled evaluation format."},
                    {"role": "user", "content": reform_prompt},
                ],
                temperature=0.0,
                max_tokens=400,
            )
            reformatted = _extract_assistant_text(resp2)
            if reformatted and _looks_like_eval(reformatted):
                logging.info("Reformatted evaluation succeeded.")
                return {"reply": reformatted.strip()}
            else:
                logging.warning("Reformat attempt failed; returning original evaluation. Raw reformat response: %s", resp2)
        except Exception as exc:
            logging.warning("Reformat attempt raised an exception: %s", exc)

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
    max_questions: int = Form(10),
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

    # 2) Build base system prompt (use default prompt if frontend didn't set presets)
    base = DEFAULT_PROMPT

    # 3) Create a new session
    session = create_session(system_prompt=base, metadata={})

    # initialize question counters and limits
    session.metadata.setdefault("questions_asked", 0)
    session.metadata.setdefault("max_questions", int(max_questions or 10))

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

@app.get("/session/{session_id}")
async def get_session_endpoint(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    return session.dict()

@app.post("/session/{session_id}/start")
async def start_session(session_id: str):
    """Trigger the model to produce the first assistant question for a session.

    This calls the model with the current system prompt (and any messages),
    appends the assistant reply to the session, and increments the question counter.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    q = session.metadata.get("questions_asked", 0)
    max_q = session.metadata.get("max_questions", 10)
    if q >= max_q:
        raise HTTPException(status_code=400, detail="Question limit reached")

    # Build a focused message set for the session start call: use the session's
    # system prompt but explicitly instruct the model to ask exactly one
    # interview question. This avoids the model returning an overall
    # evaluation/summary at session start.
    start_instruction = (
        "Please ask exactly one interview question tailored to the candidate. "
        "Do NOT provide any evaluation, summary, or feedback — ask only the question. "
        "Keep it concise and clear."
    )

    messages = [
        {"role": "system", "content": session.system_prompt},
        {"role": "user", "content": start_instruction},
    ]

    client = get_client()
    try:
        resp = await client.chat(messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    assistant_text = _extract_assistant_text(resp)
    if not assistant_text:
        logging.warning("No assistant text found for session start; raw response: %s", resp)
        assistant_text = "(no text returned from model)"

    # append assistant reply and increment counter
    append_message(session_id, role="assistant", content=assistant_text)
    session.metadata["questions_asked"] = q + 1

    return {"reply": assistant_text, "raw": resp}

@app.post("/session/{session_id}/settings")
async def apply_session_settings(session_id: str, req: SettingsReq):
    """Apply system-prompt settings for a session using the prompts stored in system_prompts.json.

    Expects JSON body with fields: technicality (1-3), politeness (1-3), difficulty (1-3).
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    # get prompt from the prompts store
    prompt = get_prompt(req.technicality, req.politeness, req.difficulty)
    if not prompt:
        raise HTTPException(status_code=400, detail="No prompt available for given settings")

    updated = set_system_prompt(session_id, prompt)
    return {"id": updated.id, "system_prompt": updated.system_prompt}


@app.post("/session/{session_id}/message")
async def post_message(
    session_id: str,
    request: Request,
    audio: Optional[UploadFile] = File(None),
    question_index: Optional[int] = Form(None),
):
    """Accept either JSON with `{content: string}` or multipart `audio` upload.

    - If `Content-Type` is `application/json`, read `content` from the body and use it
      as the user's message (useful for summary prompts from the frontend).
    - Otherwise, if an `audio` file is provided, run server-side transcription and
      use the transcript as the user's message.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    # Determine whether this is a JSON request or a form/audio request
    content_type = request.headers.get("content-type", "")
    is_json = content_type.startswith("application/json")

    transcribed_text = ""

    if is_json:
        # Read JSON body and extract `content`
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        if not isinstance(body, dict) or "content" not in body:
            raise HTTPException(status_code=422, detail="JSON body must contain 'content' field")

        transcribed_text = str(body.get("content") or "").strip()
        if not transcribed_text:
            raise HTTPException(status_code=400, detail="Empty 'content' in JSON body")

    else:
        # Expect an audio file in multipart/form-data
        if audio is None:
            raise HTTPException(status_code=400, detail="No audio file provided")

        try:
            audio_content = await audio.read()
            from interview_helper.speech_to_text import speech_to_text2
            transcribed_text = speech_to_text2(audio_content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {str(e)}")

    # append user message
    append_message(session_id, role="user", content=transcribed_text)
    

    # enforce question limit before generating a new assistant reply
    q = session.metadata.get("questions_asked", 0)
    max_q = session.metadata.get("max_questions", 10)
    if q >= max_q:
        raise HTTPException(status_code=400, detail="Question limit reached")
    
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
        logging.warning("No assistant text found for message reply; raw response: %s", resp)
        assistant_text = "(no text returned from model)"
    
    # append assistant reply to session and increment question counter
    append_message(session_id, role="assistant", content=assistant_text)
    session.metadata["questions_asked"] = q + 1
    
    return {
        "reply": assistant_text, 
        "raw": resp,
        "question_index": question_index,
        "transcribed_text": transcribed_text
    }

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.src.main:app", host="0.0.0.0", port=port, reload=True)
