import os
import dotenv
import io

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
    """
    Transcribe audio bytes to text using Deepgram/GreenPT.
    
    Args:
        audio_bytes: Raw audio data as bytes (e.g., from UploadFile)
    
    Returns:
        Transcribed text as string
    """
    try:
        # Create a Deepgram client using the API key
        deepgram = DeepgramClient(
            api_key=api_key,
            environment=self_hosted_env
        )

        # Transcribe the audio bytes directly
        response = deepgram.listen.v1.media.transcribe_file(
            request=audio_bytes,
            model="green-s",
            smart_format=True,
        )

        transcript = response.results.channels[0].alternatives[0].transcript
        
        print(f"\n✅ Transcript extracted successfully!")
        print(f"{'='*60}")
        print(transcript)
        print(f"{'='*60}\n")

        return transcript

    except Exception as e:
        print(f"Exception in speech_to_text: {e}")
        raise