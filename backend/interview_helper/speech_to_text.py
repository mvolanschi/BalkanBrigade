import os
import dotenv

dotenv.load_dotenv()

from deepgram import DeepgramClient
from deepgram.environment import DeepgramClientEnvironment

self_hosted_env = DeepgramClientEnvironment(
    base="https://api.greenpt.ai/",
    production="",
    agent="",
)

api_key = os.getenv("GREEN-PT-KEY") or os.getenv("DEEPGRAM_API_KEY")

if not api_key:
    raise ValueError("API key not found. Set GREEN-PT-KEY or DEEPGRAM_API_KEY in .env file")


def speech_to_text(audio_bytes: bytes) -> str:
    """Transcribe audio bytes to text using Deepgram/GreenPT."""
    try:
        deepgram = DeepgramClient(api_key=api_key, environment=self_hosted_env)
        response = deepgram.listen.v1.media.transcribe_file(
            request=audio_bytes,
            model="green-s",
            smart_format=True,
        )
        transcript = response.results.channels[0].alternatives[0].transcript
        print("\n✅ Transcript extracted successfully!\n" + "=" * 60)
        print(transcript)
        print("=" * 60 + "\n")
        return transcript
    except Exception as e:
        print(f"Exception: {e}")
        raise


def speech_to_text2(audio_data: bytes) -> str:
    """Alternate helper identical to speech_to_text for compatibility."""
    return speech_to_text(audio_data)
