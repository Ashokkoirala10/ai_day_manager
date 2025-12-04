# manager/utills/tts_engine.py
"""
Enhanced Text-to-Speech Engine
Supports multiple TTS backends with fallbacks
"""

import platform
import threading
from queue import Queue

# Try importing pyttsx3 (cross-platform TTS)
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    print("⚠️ pyttsx3 not installed. TTS features will be limited.")
    PYTTSX3_AVAILABLE = False

# Initialize TTS engine (singleton pattern)
_engine = None
_engine_lock = threading.Lock()
_speech_queue = Queue()
_is_speaking = False


def get_engine():
    """
    Get or initialize the TTS engine (thread-safe singleton)
    """
    global _engine
    
    if not PYTTSX3_AVAILABLE:
        return None
    
    if _engine is None:
        with _engine_lock:
            if _engine is None:  # Double-check locking
                try:
                    _engine = pyttsx3.init()
                    
                    # Configure engine settings
                    _engine.setProperty('rate', 160)  # Speed (words per minute)
                    _engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
                    
                    # Try to set a better voice (prefer female voice if available)
                    voices = _engine.getProperty('voices')
                    if voices:
                        # Prefer female voice (usually clearer)
                        for voice in voices:
                            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                                _engine.setProperty('voice', voice.id)
                                break
                        else:
                            # Use first available voice
                            _engine.setProperty('voice', voices[0].id)
                    
                    print("✅ TTS engine initialized successfully")
                    print(f"   Platform: {platform.system()}")
                    print(f"   Voice: {_engine.getProperty('voice')}")
                    
                except Exception as e:
                    print(f"❌ Failed to initialize TTS engine: {e}")
                    return None
    
    return _engine


def speak(text, priority='normal', async_mode=False):
    """
    Speak text using TTS engine
    
    Args:
        text (str): Text to speak
        priority (str): 'high', 'normal', 'low' (for future queue management)
        async_mode (bool): If True, speak in background thread
    
    Returns:
        bool: True if speech was successful, False otherwise
    """
    if not PYTTSX3_AVAILABLE:
        print(f"🗣️ [TTS Disabled] Would speak: {text}")
        return False
    
    if not text or not isinstance(text, str):
        print("⚠️ Invalid text provided to TTS")
        return False
    
    # Clean text for better speech
    text = clean_text_for_speech(text)
    
    if async_mode:
        # Speak in background thread
        thread = threading.Thread(target=_speak_sync, args=(text,), daemon=True)
        thread.start()
        return True
    else:
        # Speak synchronously
        return _speak_sync(text)


def _speak_sync(text):
    """
    Internal synchronous speaking function
    """
    global _is_speaking
    
    engine = get_engine()
    if not engine:
        return False
    
    try:
        # Prevent overlapping speech
        with _engine_lock:
            _is_speaking = True
            print(f"🗣️ Speaking: {text}")
            engine.say(text)
            engine.runAndWait()
            _is_speaking = False
        
        return True
        
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        _is_speaking = False
        return False


def speak_notification(task_title, priority='medium'):
    """
    Speak a task notification with appropriate tone
    
    Args:
        task_title (str): Task title to announce
        priority (str): Task priority (affects message)
    """
    if priority == 'high':
        message = f"Important reminder: {task_title}. Please complete this task soon."
    elif priority == 'low':
        message = f"Gentle reminder: {task_title}."
    else:  # medium
        message = f"Reminder: {task_title}."
    
    speak(message, async_mode=True)


def speak_completion(task_title):
    """
    Speak task completion message
    """
    message = f"Great job! You completed {task_title}."
    speak(message, async_mode=True)


def speak_greeting(user_name=None):
    """
    Speak personalized greeting based on time of day
    """
    from datetime import datetime
    
    hour = datetime.now().hour
    
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    
    if user_name:
        message = f"{greeting}, {user_name}! Ready to plan your day?"
    else:
        message = f"{greeting}! Ready to plan your day?"
    
    speak(message, async_mode=True)


def speak_productivity_summary(completed, total):
    """
    Speak daily productivity summary
    """
    if total == 0:
        message = "You haven't added any tasks yet. Let's get started!"
    elif completed == total:
        message = f"Amazing! You completed all {total} tasks today. Perfect day!"
    elif completed > 0:
        percentage = int((completed / total) * 100)
        message = f"You completed {completed} out of {total} tasks today. That's {percentage} percent. Keep it up!"
    else:
        message = f"You have {total} tasks pending. Let's get started!"
    
    speak(message, async_mode=True)


def clean_text_for_speech(text):
    """
    Clean and format text for better speech synthesis
    
    Args:
        text (str): Raw text
    
    Returns:
        str: Cleaned text
    """
    import re
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove hashtags and mentions
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'@\w+', '', text)
    
    # Replace common abbreviations
    replacements = {
        'asap': 'as soon as possible',
        'btw': 'by the way',
        'fyi': 'for your information',
        'am': 'A M',
        'pm': 'P M',
        '&': 'and',
        '@': 'at',
        '#': 'number',
    }
    
    for abbr, full in replacements.items():
        text = re.sub(r'\b' + abbr + r'\b', full, text, flags=re.IGNORECASE)
    
    # Remove excessive punctuation
    text = re.sub(r'[!?]{2,}', '!', text)
    text = re.sub(r'\.{2,}', '.', text)
    
    # Remove emojis (they don't speak well)
    text = re.sub(r'[^\w\s,.!?\'-]', '', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text.strip()


def set_voice_properties(rate=None, volume=None, voice_id=None):
    """
    Customize TTS voice properties
    
    Args:
        rate (int): Speaking rate (words per minute), default 160
        volume (float): Volume level (0.0 to 1.0), default 0.9
        voice_id (str): Specific voice ID to use
    """
    engine = get_engine()
    if not engine:
        return False
    
    try:
        if rate is not None:
            engine.setProperty('rate', rate)
            print(f"✅ TTS rate set to {rate} WPM")
        
        if volume is not None:
            engine.setProperty('volume', min(1.0, max(0.0, volume)))
            print(f"✅ TTS volume set to {volume}")
        
        if voice_id is not None:
            engine.setProperty('voice', voice_id)
            print(f"✅ TTS voice changed")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to set TTS properties: {e}")
        return False


def list_available_voices():
    """
    List all available TTS voices on the system
    
    Returns:
        list: List of voice dictionaries with id, name, languages
    """
    engine = get_engine()
    if not engine:
        return []
    
    try:
        voices = engine.getProperty('voices')
        voice_list = []
        
        print("\n📢 Available TTS Voices:")
        print("=" * 60)
        
        for i, voice in enumerate(voices, 1):
            voice_info = {
                'id': voice.id,
                'name': voice.name,
                'languages': voice.languages,
                'gender': voice.gender if hasattr(voice, 'gender') else 'unknown'
            }
            voice_list.append(voice_info)
            
            print(f"{i}. {voice.name}")
            print(f"   ID: {voice.id}")
            print(f"   Languages: {voice.languages}")
            print()
        
        print("=" * 60 + "\n")
        
        return voice_list
        
    except Exception as e:
        print(f"❌ Failed to list voices: {e}")
        return []


def is_speaking():
    """
    Check if TTS engine is currently speaking
    
    Returns:
        bool: True if speaking, False otherwise
    """
    return _is_speaking


def stop_speaking():
    """
    Stop current speech immediately
    """
    engine = get_engine()
    if engine:
        try:
            engine.stop()
            print("🛑 TTS stopped")
        except Exception as e:
            print(f"⚠️ Failed to stop TTS: {e}")


def test_tts():
    """
    Test TTS functionality
    """
    print("\n🧪 TESTING TTS ENGINE")
    print("=" * 60)
    
    if not PYTTSX3_AVAILABLE:
        print("❌ pyttsx3 not available. Please install it:")
        print("   pip install pyttsx3")
        return False
    
    # List voices
    list_available_voices()
    
    # Test speech
    test_phrases = [
        "Hello! This is a test of the text to speech engine.",
        "Testing different punctuation. Does it sound natural?",
        "Numbers: 1, 2, 3. Time: 3:30 PM.",
    ]
    
    for i, phrase in enumerate(test_phrases, 1):
        print(f"Test {i}/{len(test_phrases)}: {phrase}")
        speak(phrase)
        import time
        time.sleep(1)  # Small pause between tests
    
    print("=" * 60)
    print("✅ TTS test complete!\n")
    return True


# Initialize engine on module load (optional)
# Uncomment to pre-initialize
# get_engine()


if __name__ == "__main__":
    # Run tests if executed directly
    test_tts()