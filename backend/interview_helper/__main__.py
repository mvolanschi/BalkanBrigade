from speech_to_text import speech_to_text
from text_to_speech import generate_sound_files


if __name__ == "__main__":
    AUDIO_FILE = "./harvard.wav"

    text = speech_to_text(AUDIO_FILE)
    generate_sound_files(text=text)
