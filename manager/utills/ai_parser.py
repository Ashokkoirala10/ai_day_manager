import requests, json, re
from datetime import datetime, timedelta

def parse_command(command):
    """
    Extract task and time from natural language commands
    Return dict: {"task": ..., "time": "HH:MM"}
    """
    prompt = f"""
    ONLY extract a reminder task and time in 24-hour HH:MM format.
    Respond in JSON like: {{"task": "...", "time": "HH:MM"}}
    User request: "{command}"
    """
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "phi3", "prompt": prompt},
            timeout=60
        )
        text = response.json().get("response", "").strip()

        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if not match:
            return None

        result = json.loads(match.group())

        # Clean task text (remove any time mentions)
        task_clean = re.sub(
            r'\b(at\s*)?\d{1,2}[:\s]?\d{2}\s?(AM|PM|am|pm)?\b',
            '',
            result.get("task", "")
        ).strip()
        result["task"] = task_clean

        # Ensure time exists, fallback to +5min
        if not result.get("time"):
            result["time"] = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M")

        return result

    except Exception as e:
        print("AI parse error:", e)
        return None
