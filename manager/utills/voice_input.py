# voice_input.py
import speech_recognition as sr

def listen_for_command():
    """Listen through microphone and return recognized text."""
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("🎙️ Speak now... (say something like 'Remind me to cook at 5 PM')")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"🗣️ You said: {text}")
        return text
    except sr.UnknownValueError:
        print("❌ Sorry, I couldn’t understand that.")
        return None
    except sr.RequestError as e:
        print(f"⚠️ Speech recognition error: {e}")
        return None
