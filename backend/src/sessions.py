from typing import List, Dict, Any
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


def list_sessions() -> List[Session]:
    return list(_SESSIONS.values())
