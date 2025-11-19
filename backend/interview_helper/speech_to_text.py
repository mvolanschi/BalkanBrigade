# For help migrating to the new Python SDK, check out our migration guide:
# https://github.com/deepgram/deepgram-python-sdk/blob/main/docs/Migrating-v3-to-v5.md

# main.py (python example)

import os
import dotenv

dotenv.load_dotenv()

from deepgram import (
    DeepgramClient,
)
from deepgram.environment import DeepgramClientEnvironment

self_hosted_env = DeepgramClientEnvironment(
    # base="http://localhost:8080",
    base="https://api.greenpt.ai/",
    production="",
    agent="",
)

# Path to the audio file
AUDIO_FILE = "./harvard.wav"

api_key = os.getenv("GREEN-PT-KEY") or os.getenv("DEEPGRAM_API_KEY")

if not api_key:
    raise ValueError("API key not found. Set GREEN-PT-KEY or DEEPGRAM_API_KEY in .env file")

def speech_to_text(AUDIO_FILE: str):
    try:
        # STEP 1 Create a Deepgram client using the API key
        deepgram = DeepgramClient(
            api_key=api_key,
            environment=self_hosted_env
        )

        # STEP 2: Call the transcribe_file method with the audio file and options
        with open(AUDIO_FILE, "rb") as audio_file:
            response = deepgram.listen.v1.media.transcribe_file(
                request=audio_file.read(),
                model="green-s",
                smart_format=True,
            )

        # print(response)

        transcript = response.results.channels[0].alternatives[0].transcript
        
        print(f"\n✅ Transcript extracted successfully!")
        print(f"{'='*60}")
        print(transcript)
        print(f"{'='*60}\n")

        return transcript
        # STEP 3: Print the response
        # print(response.to_json(indent=4))

    except Exception as e:
        print(f"Exception: {e}")

# if __name__ == "__main__":
speech_to_text(AUDIO_FILE)
