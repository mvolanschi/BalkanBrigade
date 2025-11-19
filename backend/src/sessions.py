from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from uuid import uuid4


class Message(BaseModel):
    role: str
    content: str


class Session(BaseModel):
    id: str
    system_prompt: str
    messages: List[Message]
    metadata: Dict[str, Any] = {}

    # Optional textual assets provided by the frontend per session
    cv: str | None = None
    job_description: str | None = None
    company_info: str | None = None


_SESSIONS: Dict[str, Session] = {}


def create_session(system_prompt: str, metadata: Dict[str, Any] | None = None) -> Session:
    sid = str(uuid4())
    session = Session(id=sid, system_prompt=system_prompt, messages=[Message(role="system", content=system_prompt)], metadata=metadata or {})
    _SESSIONS[sid] = session
    return session


def get_session(session_id: str) -> Session | None:
    return _SESSIONS.get(session_id)


def append_message(session_id: str, role: str, content: str) -> Message:
    session = _SESSIONS[session_id]
    msg = Message(role=role, content=content)
    session.messages.append(msg)
    return msg


def set_assets(
    session_id: str,
    cv: Optional[str] = None,
    job_description: Optional[str] = None,
    company_info: Optional[str] = None,
    base_prompt: Optional[str] = None,
) -> Session:
    """Attach textual assets to a session and update its system prompt.

    Responsibilities:
    - store raw assets on the session (`cv`, `job_description`, `company_info`)
    - rebuild the session.system_prompt to include the assets under clear headings
      using `base_prompt` when provided; otherwise try to recover a sensible base
      by stripping any previously embedded asset sections.

    This also replaces the first system message so the chat history has the
    correct system message the model will consume.
    """
    session = _SESSIONS[session_id]

    # store incoming assets (allow partial updates)
    if cv is not None:
        session.cv = cv
    if job_description is not None:
        session.job_description = job_description
    if company_info is not None:
        session.company_info = company_info

    # determine a clean base prompt to avoid double-including assets
    if base_prompt:
        base = base_prompt.strip()
    else:
        # try to strip previously appended assets from the stored prompt
        raw = session.system_prompt or ""
        separator = "\n\n---\nCandidate CV:"
        idx = raw.find(separator)
        if idx != -1:
            base = raw[:idx].strip()
        else:
            base = raw.strip()

    # small helper to avoid sending extremely long assets in full
    def _truncate(text: str, max_chars: int = 4000) -> str:
        if not text:
            return ""
        t = text.strip()
        if len(t) <= max_chars:
            return t
        return t[: max_chars - 12].rstrip() + "\n\n[TRUNCATED]"

    # instruction header: explicitly tell the model to prioritize the job description
    instruction_header = (
        "Important: When selecting, ordering, and framing interview questions, prioritize the Job Description as the primary source. "
        "Use the Candidate CV to ground questions in the candidate's background and experience, and use Company Info to align tone and context. "
        "Make sure questions are relevant to the job description and avoid asking unrelated details."
    )

    # assemble the final prompt: instruction header, base prompt, then assets sections
    parts = [instruction_header]
    if base:
        parts.append(base)

    if session.cv:
        parts.append("---\nCandidate CV:\n" + _truncate(session.cv))
    if session.job_description:
        parts.append("---\nJob Description:\n" + _truncate(session.job_description))
    if session.company_info:
        parts.append("---\nCompany Info:\n" + _truncate(session.company_info))

    # join with spacing between sections
    final_prompt = "\n\n".join(parts)
    if final_prompt:
        session.system_prompt = final_prompt
        # update the first system message so chat history is consistent
        if session.messages:
            session.messages[0] = Message(role="system", content=session.system_prompt)

    return session


def list_sessions() -> List[Session]:
    return list(_SESSIONS.values())


def set_system_prompt(session_id: str, system_prompt: str) -> Session:
    """Set the session system prompt and update the first system message.

    Use this when you want to directly apply a prepared system prompt to an
    existing session (for example, one selected from a prompts store).
    """
    session = _SESSIONS[session_id]
    session.system_prompt = system_prompt
    if session.messages:
        session.messages[0] = Message(role="system", content=session.system_prompt)
    return session
