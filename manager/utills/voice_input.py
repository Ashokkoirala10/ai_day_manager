# manager/utills/voice_input.py
"""
Enhanced Voice Input Module
Supports multiple speech recognition backends with fallbacks
"""

import threading
from typing import Optional, Callable

# Try importing speech recognition
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    print("⚠️ SpeechRecognition not installed. Voice input disabled.")
    SR_AVAILABLE = False


class VoiceInputManager:
    """
    Manager class for handling voice input with various options
    """
    
    def __init__(self):
        self.recognizer = sr.Recognizer() if SR_AVAILABLE else None
        self.microphone = None
        self.is_listening = False
        
        if SR_AVAILABLE:
            self._initialize_microphone()
    
    def _initialize_microphone(self):
        """Initialize and configure microphone"""
        try:
            self.microphone = sr.Microphone()
            
            # Calibrate for ambient noise
            print("🎤 Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            print("✅ Microphone initialized successfully")
            
            # Configure recognizer settings
            self.recognizer.energy_threshold = 4000  # Minimum audio energy
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8  # Seconds of silence to consider end
            
        except Exception as e:
            print(f"❌ Failed to initialize microphone: {e}")
            self.microphone = None


def listen_for_command(timeout=5, phrase_time_limit=10, language='en-US'):
    """
    Listen for a voice command and return recognized text
    
    Args:
        timeout (int): Seconds to wait for speech to start
        phrase_time_limit (int): Maximum seconds for phrase
        language (str): Language code (e.g., 'en-US', 'en-IN')
    
    Returns:
        str: Recognized text or None if failed
    """
    if not SR_AVAILABLE:
        print("❌ Speech recognition not available")
        return None
    
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            print("🎤 Listening... Speak now!")
            print(f"⏱️ Timeout: {timeout}s | Phrase limit: {phrase_time_limit}s")
            
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            # Listen for audio
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit
            )
            
            print("🔄 Processing speech...")
            
            # Try Google Speech Recognition (free)
            try:
                text = recognizer.recognize_google(audio, language=language)
                print(f"✅ Recognized: '{text}'")
                return text
            
            except sr.UnknownValueError:
                print("❌ Could not understand audio")
                return None
            
            except sr.RequestError as e:
                print(f"❌ Google Speech Recognition error: {e}")
                
                # Fallback to Sphinx (offline, less accurate)
                try:
                    text = recognizer.recognize_sphinx(audio)
                    print(f"✅ Recognized (Sphinx): '{text}'")
                    return text
                except Exception as sphinx_error:
                    print(f"❌ Sphinx also failed: {sphinx_error}")
                    return None
    
    except sr.WaitTimeoutError:
        print("⏱️ Listening timed out - no speech detected")
        return None
    
    except Exception as e:
        print(f"❌ Voice input error: {e}")
        return None


def listen_for_task(timeout=10, phrase_time_limit=15):
    """
    Specialized function to listen for task creation commands
    Provides helpful feedback and examples
    
    Returns:
        str: Task command text or None
    """
    print("\n" + "="*60)
    print("🎤 VOICE TASK INPUT")
    print("="*60)
    print("Examples:")
    print("  • 'Remind me to call mom at 3 PM'")
    print("  • 'Meeting with team tomorrow at 10 AM'")
    print("  • 'Buy groceries this evening'")
    print("  • 'High priority project deadline Friday'")
    print("="*60)
    
    return listen_for_command(
        timeout=timeout,
        phrase_time_limit=phrase_time_limit
    )


def listen_continuously(callback: Callable[[str], None], stop_event: threading.Event):
    """
    Listen continuously in the background and call callback with recognized text
    
    Args:
        callback: Function to call with recognized text
        stop_event: Threading event to stop listening
    
    Example:
        stop = threading.Event()
        def handler(text):
            print(f"Heard: {text}")
        
        thread = threading.Thread(
            target=listen_continuously,
            args=(handler, stop),
            daemon=True
        )
        thread.start()
        
        # Later: stop.set()
    """
    if not SR_AVAILABLE:
        print("❌ Speech recognition not available")
        return
    
    recognizer = sr.Recognizer()
    
    print("🎤 Starting continuous listening...")
    print("💡 Say 'stop listening' to exit")
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        while not stop_event.is_set():
            try:
                print("🎤 Listening...")
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=10)
                
                try:
                    text = recognizer.recognize_google(audio)
                    print(f"✅ Heard: '{text}'")
                    
                    # Check for stop command
                    if 'stop listening' in text.lower():
                        print("🛑 Stop command received")
                        stop_event.set()
                        break
                    
                    # Call the callback
                    callback(text)
                
                except sr.UnknownValueError:
                    pass  # No speech detected, continue listening
                
                except sr.RequestError as e:
                    print(f"⚠️ Recognition error: {e}")
            
            except sr.WaitTimeoutError:
                pass  # Timeout, continue listening
            
            except Exception as e:
                print(f"❌ Listening error: {e}")
                import time
                time.sleep(1)  # Wait before retrying
    
    print("🛑 Continuous listening stopped")


def listen_for_confirmation(expected_phrases=None, timeout=5):
    """
    Listen for confirmation (yes/no or custom phrases)
    
    Args:
        expected_phrases (list): List of expected phrases, default ['yes', 'no']
        timeout (int): Seconds to wait
    
    Returns:
        str: Matched phrase or None
    """
    if expected_phrases is None:
        expected_phrases = ['yes', 'no', 'confirm', 'cancel']
    
    print(f"🎤 Say one of: {', '.join(expected_phrases)}")
    
    text = listen_for_command(timeout=timeout, phrase_time_limit=5)
    
    if text:
        text_lower = text.lower()
        for phrase in expected_phrases:
            if phrase.lower() in text_lower:
                print(f"✅ Confirmed: '{phrase}'")
                return phrase
    
    return None


def get_microphone_list():
    """
    List all available microphones
    
    Returns:
        list: List of microphone names
    """
    if not SR_AVAILABLE:
        return []
    
    try:
        mic_list = sr.Microphone.list_microphone_names()
        
        print("\n🎤 Available Microphones:")
        print("="*60)
        for i, mic_name in enumerate(mic_list):
            print(f"{i}. {mic_name}")
        print("="*60 + "\n")
        
        return mic_list
    
    except Exception as e:
        print(f"❌ Failed to list microphones: {e}")
        return []


def test_microphone(duration=3):
    """
    Test microphone by recording and playing back audio level
    
    Args:
        duration (int): Seconds to record
    """
    if not SR_AVAILABLE:
        print("❌ Speech recognition not available")
        return False
    
    print("\n🧪 TESTING MICROPHONE")
    print("="*60)
    
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            print(f"🎤 Recording for {duration} seconds...")
            print("💬 Say something!")
            
            # Show energy level
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"📊 Ambient energy threshold: {recognizer.energy_threshold}")
            
            audio = recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
            
            print("🔄 Processing...")
            
            # Try to recognize
            try:
                text = recognizer.recognize_google(audio)
                print(f"✅ Successfully recognized: '{text}'")
                print("="*60 + "\n")
                return True
            
            except sr.UnknownValueError:
                print("⚠️ Audio recorded but could not understand speech")
                print("💡 Try speaking louder and more clearly")
                print("="*60 + "\n")
                return False
            
            except sr.RequestError as e:
                print(f"❌ Recognition service error: {e}")
                print("="*60 + "\n")
                return False
    
    except Exception as e:
        print(f"❌ Microphone test failed: {e}")
        print("="*60 + "\n")
        return False


def listen_with_timeout_feedback(timeout=5):
    """
    Listen with visual countdown feedback
    """
    if not SR_AVAILABLE:
        return None
    
    import time
    
    print("\n🎤 Get ready to speak...")
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    print("🎤 Speak NOW!")
    return listen_for_command(timeout=timeout)


def parse_voice_time(text):
    """
    Extract time from voice input
    
    Examples:
        "3 PM" -> "15:00"
        "three thirty" -> "15:30"
        "noon" -> "12:00"
        "midnight" -> "00:00"
    """
    import re
    from datetime import datetime
    
    text = text.lower()
    
    # Number words to digits
    number_words = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
        'ten': 10, 'eleven': 11, 'twelve': 12
    }
    
    for word, digit in number_words.items():
        text = text.replace(word, str(digit))
    
    # Special times
    if 'noon' in text:
        return '12:00'
    if 'midnight' in text:
        return '00:00'
    
    # Pattern: "3 PM", "3:30 PM", "15:30"
    patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm)?',
        r'(\d{1,2})\s*(am|pm)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if len(match.groups()) >= 2 and match.group(2).isdigit() else 0
            period = match.group(3) if len(match.groups()) >= 3 else None
            
            if period:
                period = period.lower()
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
            
            return f"{hour:02d}:{minute:02d}"
    
    return None


# Example usage and testing
if __name__ == "__main__":
    print("\n" + "="*60)
    print("VOICE INPUT MODULE TEST")
    print("="*60)
    
    if not SR_AVAILABLE:
        print("❌ SpeechRecognition not installed")
        print("Install with: pip install SpeechRecognition pyaudio")
        exit(1)
    
    print("\n1. Testing microphone...")
    test_microphone(duration=3)
    
    print("\n2. Listing available microphones...")
    get_microphone_list()
    
    print("\n3. Testing task input...")
    task_text = listen_for_task()
    if task_text:
        print(f"✅ Got task: {task_text}")
        
        # Try to extract time
        time_str = parse_voice_time(task_text)
        if time_str:
            print(f"⏰ Extracted time: {time_str}")
    
    print("\n✅ Voice input tests complete!\n")