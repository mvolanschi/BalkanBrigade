"""Utility helpers to transcribe audio using Deepgram/GreenPT."""

from __future__ import annotations

import os
from functools import lru_cache

import dotenv
from deepgram import DeepgramClient
from deepgram.environment import DeepgramClientEnvironment

dotenv.load_dotenv()

# Allow overriding the STT base URL via env for local testing.
self_hosted_env = DeepgramClientEnvironment(
    base=os.getenv("GREENPT_STT_BASE", "https://api.greenpt.ai/"),
    production="",
    agent="",
)

AUDIO_FILE = "./harvard.wav"  # only used for manual CLI runs
DEFAULT_MODEL = os.getenv("GREENPT_STT_MODEL", "green-s")


def _get_api_key() -> str:
    key = os.getenv("GREEN-PT-KEY") or os.getenv("DEEPGRAM_API_KEY")
    if not key:
        raise ValueError("Missing GREEN-PT-KEY or DEEPGRAM_API_KEY in environment")
    return key


@lru_cache(maxsize=1)
def _get_client() -> DeepgramClient:
    return DeepgramClient(api_key=_get_api_key(), environment=self_hosted_env)


def _transcribe_bytes(audio_bytes: bytes) -> str:
    if not audio_bytes:
        raise ValueError("Audio content is empty; cannot transcribe")

    client = _get_client()
    response = client.listen.v1.media.transcribe_file(
        request=audio_bytes,
        model=DEFAULT_MODEL,
        smart_format=True,
    )

    try:
        transcript = response.results.channels[0].alternatives[0].transcript
    except (AttributeError, IndexError, KeyError) as exc:  # defensive against schema drift
        raise RuntimeError("Speech-to-text response missing transcript field") from exc

    transcript = (transcript or "").strip()
    if not transcript:
        raise RuntimeError("Speech-to-text produced an empty transcript")
    return transcript


def speech_to_text(audio_path: str) -> str:
    """Transcribe an audio file from disk (legacy helper)."""

    with open(audio_path, "rb") as audio_file:
        transcript = _transcribe_bytes(audio_file.read())

    print("\n✅ Transcript extracted successfully!")
    print("=" * 60)
    print(transcript)
    print("=" * 60 + "\n")
    return transcript


def speech_to_text2(audio_content: bytes) -> str:
    """Transcribe in-memory audio bytes uploaded via the API."""

    return _transcribe_bytes(audio_content)


if __name__ == "__main__":
    speech_to_text(AUDIO_FILE)
