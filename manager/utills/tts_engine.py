# tts_engine.py
import pyttsx3

def speak(message):
    """Use the system's TTS engine to speak text aloud."""
    engine = pyttsx3.init()
    engine.setProperty("rate", 160)   # Speed of speech
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[0].id)  # Use first available voice
    print("🗣️ Speaking:", message)
    engine.say(message)
    engine.runAndWait()
