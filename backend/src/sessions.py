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

    # assemble the final prompt only if there are assets to include
    parts = [base] if base else []
    if session.cv:
        parts.append("---\nCandidate CV:\n" + session.cv.strip())
    if session.job_description:
        parts.append("---\nJob Description:\n" + session.job_description.strip())
    if session.company_info:
        parts.append("---\nCompany Info:\n" + session.company_info.strip())

    # join with spacing between sections
    final_prompt = "\n\n".join(parts) if parts else base
    if final_prompt:
        session.system_prompt = final_prompt
        # update the first system message so chat history is consistent
        if session.messages:
            session.messages[0] = Message(role="system", content=session.system_prompt)

    return session


def list_sessions() -> List[Session]:
    return list(_SESSIONS.values())
