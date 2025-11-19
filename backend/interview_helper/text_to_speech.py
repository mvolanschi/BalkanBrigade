import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Get API key
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")

if not ELEVEN_LABS_API_KEY:
    raise ValueError("ELEVEN_LABS_API_KEY not found in .env file")

# ElevenLabs API endpoint
ELEVEN_LABS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Available voice IDs (popular ones)
VOICES = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "drew": "29vD33N1CtxCmqQRPOHJ",
    "clyde": "2EiwWnXFnvU5JabPnv8n",
    "paul": "5Q0t7uMcjvnagumLfvZi",
    "domi": "AZnzlk1XvdvUeBnXmlld",
    "dave": "CYw3kZ02Hs0563khs1Fj",
    "fin": "D38z5RcWu1voky8WS1ja",
    "sarah": "EXAVITQu4vr4xnSDxMaL",
    "antoni": "ErXwobaYiN019PkySvjV",
    "thomas": "GBv7mTt0atIp3Br8iCZE",
    "charlie": "IKne3meq5aSn9XLyUdCD",
    "george": "JBFqnCBsd6RMkjVDRZzb",
    "callum": "N2lVS1w4EtoT3dr4eOWO",
    "lily": "pFZP5JQG7iQjIQuC4Bku",
    "liam": "TX3LPaxmHKxFdv7VOQHJ",
    "dorothy": "ThT5KcBeYPX3keUQqHPh",
}

def text_to_speech(
    text,
    voice_id="rachel",
    output_file="output.mp3",
    model_id="eleven_monolingual_v1",
    stability=0.5,
    similarity_boost=0.75
):
    """
    Convert text to speech using ElevenLabs API
    
    Args:
        text: Text to convert to speech
        voice_id: Voice ID or name from VOICES dict
        output_file: Output filename
        model_id: Model to use (eleven_monolingual_v1, eleven_multilingual_v1, eleven_multilingual_v2)
        stability: Voice stability (0-1)
        similarity_boost: Voice similarity boost (0-1)
    """
    print(f"\n{'='*60}")
    print("ELEVENLABS TEXT-TO-SPEECH")
    print(f"{'='*60}")
    
    try:
        # Get voice ID if voice name was provided
        if voice_id in VOICES:
            actual_voice_id = VOICES[voice_id]
            print(f"🎤 Voice: {voice_id} ({actual_voice_id})")
        else:
            actual_voice_id = voice_id
            print(f"🎤 Voice ID: {actual_voice_id}")
        
        print(f"📝 Text: {text[:100]}{'...' if len(text) > 100 else ''}")
        print(f"🎵 Model: {model_id}")
        
        # Prepare the request
        url = f"{ELEVEN_LABS_URL}/{actual_voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVEN_LABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost
            }
        }
        
        # Make the request
        print("🔄 Generating audio...")
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # Save the audio file
            with open(output_file, "wb") as f:
                f.write(response.content)
            
            file_size = os.path.getsize(output_file) / 1024  # KB
            print(f"✅ Audio saved to: {output_file} ({file_size:.1f} KB)")
            return output_file
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def list_available_voices():
    """List all available voices from ElevenLabs"""
    print(f"\n{'='*60}")
    print("AVAILABLE VOICES")
    print(f"{'='*60}")
    
    try:
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {
            "Accept": "application/json",
            "xi-api-key": ELEVEN_LABS_API_KEY
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            voices = response.json().get("voices", [])
            
            print(f"\nFound {len(voices)} voices:\n")
            for voice in voices:
                name = voice.get("name", "Unknown")
                voice_id = voice.get("voice_id", "Unknown")
                category = voice.get("category", "Unknown")
                print(f"  • {name:20} | ID: {voice_id} | Category: {category}")
            
            return voices
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_voice_info(voice_id):
    """Get detailed info about a specific voice"""
    try:
        # Get voice ID if voice name was provided
        if voice_id in VOICES:
            actual_voice_id = VOICES[voice_id]
        else:
            actual_voice_id = voice_id
        
        url = f"https://api.elevenlabs.io/v1/voices/{actual_voice_id}"
        headers = {
            "Accept": "application/json",
            "xi-api-key": ELEVEN_LABS_API_KEY
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            voice_data = response.json()
            print(f"\nVoice: {voice_data.get('name', 'Unknown')}")
            print(f"ID: {voice_data.get('voice_id', 'Unknown')}")
            print(f"Category: {voice_data.get('category', 'Unknown')}")
            print(f"Description: {voice_data.get('description', 'N/A')}")
            return voice_data
        else:
            print(f"❌ Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Main execution
# if __name__ == "__main__":
def generate_sound_files(text: str):
    print("\n" + "="*60)
    print("ELEVENLABS TEXT-TO-SPEECH DEMO")
    print("="*60)
    
    # List available voices
    print("\n1. Listing all available voices...")
    list_available_voices()
    
    # Generate speech with different voices
    print("\n2. Generating speech samples...")
    
    # text = "Hello! This is a test of the ElevenLabs text to speech API. It can generate very natural sounding speech in multiple voices."
    
    # Example 1: Female voice (Rachel)
    text_to_speech(
        text=text,
        voice_id="rachel",
        output_file="recordings/output_rachel.mp3"
    )
     
    print("\n" + "="*60)
    print("DEMO COMPLETED")
    print("="*60)
    print("\n💡 Available preset voices:")
    for name, vid in VOICES.items():
        print(f"   • {name}")