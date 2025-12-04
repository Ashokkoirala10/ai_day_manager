# manager/utills/ai_parser.py
import requests
import json
import re
from datetime import datetime, timedelta


def parse_command(command):
    """
    Enhanced natural language parser for task creation
    Extracts: task, time, date, priority, category from natural language
    
    Examples:
    - "Call mom at 3pm tomorrow" → task: "Call mom", time: "15:00", date: tomorrow
    - "High priority meeting at 10am" → task: "meeting", time: "10:00", priority: "high"
    - "Buy groceries tomorrow afternoon" → task: "Buy groceries", date: tomorrow, time: "14:00"
    """
    
    prompt = f"""
    Extract task information from natural language and return ONLY valid JSON.
    
    Input: "{command}"
    
    Extract:
    1. task: The main task description (remove time/date mentions)
    2. time: 24-hour format HH:MM
    3. date: YYYY-MM-DD format (use today if not specified)
    4. priority: "high", "medium", or "low" (default: medium)
    5. category: "work", "personal", "health", "study", "shopping", or "other"
    
    Time keywords:
    - morning → 09:00
    - afternoon → 14:00
    - evening → 18:00
    - night → 20:00
    
    Date keywords:
    - today → {datetime.now().date()}
    - tomorrow → {(datetime.now() + timedelta(days=1)).date()}
    - next week → {(datetime.now() + timedelta(days=7)).date()}
    
    Priority keywords: urgent, important, high priority → "high"
    
    Category keywords:
    - meeting, work, office, project → "work"
    - gym, exercise, workout, run → "health"
    - buy, shop, purchase, groceries → "shopping"
    - study, read, learn, course → "study"
    - call, family, friend → "personal"
    
    Return ONLY this JSON structure with no additional text:
    {{"task": "...", "time": "HH:MM", "date": "YYYY-MM-DD", "priority": "medium", "category": "other"}}
    """
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi3",
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return fallback_parser(command)
        
        result = response.json()
        text = result.get("response", "").strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{[^{}]*\}', text)
        if not json_match:
            return fallback_parser(command)
        
        parsed = json.loads(json_match.group())
        
        # Validate and clean the parsed data
        validated = validate_parsed_data(parsed, command)
        return validated
        
    except Exception as e:
        print(f"AI Parser Error: {e}")
        return fallback_parser(command)


def fallback_parser(command):
    """
    Fallback parser using regex when AI fails
    Basic parsing without AI
    """
    result = {
        'task': command,
        'time': None,
        'date': datetime.now().date().isoformat(),
        'priority': 'medium',
        'category': 'other'
    }
    
    # Extract time
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm)?',  # 3:30pm, 15:30
        r'(\d{1,2})\s*(am|pm)',           # 3pm
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if len(match.groups()) > 2 and match.group(2) else 0
            period = match.group(3).lower() if len(match.groups()) > 2 and match.group(3) else ''
            
            # Convert to 24-hour format
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            
            result['time'] = f"{hour:02d}:{minute:02d}"
            
            # Remove time from task description
            result['task'] = re.sub(pattern, '', command, flags=re.IGNORECASE).strip()
            break
    
    # Extract date
    today = datetime.now().date()
    if 'tomorrow' in command.lower():
        result['date'] = (today + timedelta(days=1)).isoformat()
        result['task'] = result['task'].replace('tomorrow', '').strip()
    elif 'today' in command.lower():
        result['date'] = today.isoformat()
        result['task'] = result['task'].replace('today', '').strip()
    
    # Extract priority
    if any(word in command.lower() for word in ['urgent', 'important', 'asap', 'critical']):
        result['priority'] = 'high'
    elif any(word in command.lower() for word in ['low priority', 'optional', 'maybe']):
        result['priority'] = 'low'
    
    # Extract category
    category_keywords = {
        'work': ['meeting', 'work', 'office', 'project', 'presentation', 'email'],
        'health': ['gym', 'exercise', 'workout', 'run', 'yoga', 'doctor'],
        'shopping': ['buy', 'shop', 'purchase', 'groceries', 'store'],
        'study': ['study', 'read', 'learn', 'course', 'homework', 'assignment'],
        'personal': ['call', 'family', 'friend', 'birthday', 'dinner', 'movie']
    }
    
    command_lower = command.lower()
    for category, keywords in category_keywords.items():
        if any(keyword in command_lower for keyword in keywords):
            result['category'] = category
            break
    
    # Set default time if not found
    if not result['time']:
        current_hour = datetime.now().hour
        if current_hour < 12:
            result['time'] = '09:00'  # Morning default
        elif current_hour < 17:
            result['time'] = '14:00'  # Afternoon default
        else:
            result['time'] = '18:00'  # Evening default
    
    # Clean up task description
    result['task'] = clean_task_description(result['task'])
    
    return result


def validate_parsed_data(parsed, original_command):
    """
    Validate and fix parsed data
    """
    result = {
        'task': parsed.get('task', original_command),
        'time': parsed.get('time'),
        'date': parsed.get('date'),
        'priority': parsed.get('priority', 'medium'),
        'category': parsed.get('category', 'other')
    }
    
    # Validate time format
    if result['time']:
        time_match = re.match(r'^(\d{1,2}):(\d{2})$', result['time'])
        if not time_match:
            result['time'] = '09:00'
        else:
            hour, minute = int(time_match.group(1)), int(time_match.group(2))
            if hour > 23 or minute > 59:
                result['time'] = '09:00'
            else:
                result['time'] = f"{hour:02d}:{minute:02d}"
    else:
        result['time'] = '09:00'
    
    # Validate date format
    if result['date']:
        try:
            datetime.strptime(result['date'], '%Y-%m-%d')
        except:
            result['date'] = datetime.now().date().isoformat()
    else:
        result['date'] = datetime.now().date().isoformat()
    
    # Validate priority
    if result['priority'] not in ['low', 'medium', 'high']:
        result['priority'] = 'medium'
    
    # Validate category
    valid_categories = ['work', 'personal', 'health', 'study', 'shopping', 'other']
    if result['category'] not in valid_categories:
        result['category'] = 'other'
    
    # Clean task description
    result['task'] = clean_task_description(result['task'])
    
    return result


def clean_task_description(task):
    """
    Clean up task description by removing time/date mentions
    """
    # Remove common time/date patterns
    patterns = [
        r'\bat\s+\d{1,2}:\d{2}\s*(am|pm)?\b',
        r'\b\d{1,2}\s*(am|pm)\b',
        r'\btomorrow\b',
        r'\btoday\b',
        r'\bnext week\b',
        r'\bmorning\b',
        r'\bafternoon\b',
        r'\bevening\b',
        r'\bnight\b',
        r'\burgent\b',
        r'\bhigh priority\b',
        r'\bimportant\b',
    ]
    
    for pattern in patterns:
        task = re.sub(pattern, '', task, flags=re.IGNORECASE)
    
    # Remove extra spaces and trim
    task = re.sub(r'\s+', ' ', task).strip()
    
    # Remove leading/trailing punctuation
    task = task.strip('.,!?;:- ')
    
    # Capitalize first letter
    if task:
        task = task[0].upper() + task[1:]
    
    return task or "New Task"


def extract_time_from_text(text):
    """
    Extract time in HH:MM format from various text formats
    """
    patterns = [
        (r'(\d{1,2}):(\d{2})\s*(am|pm)?', lambda m: convert_to_24h(m.group(1), m.group(2), m.group(3))),
        (r'(\d{1,2})\s*(am|pm)', lambda m: convert_to_24h(m.group(1), '00', m.group(2))),
    ]
    
    for pattern, converter in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return converter(match)
    
    return None


def convert_to_24h(hour_str, minute_str, period):
    """
    Convert 12-hour time to 24-hour format
    """
    hour = int(hour_str)
    minute = int(minute_str) if minute_str else 0
    
    if period:
        period = period.lower()
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
    
    return f"{hour:02d}:{minute:02d}"


def suggest_task_breakdown(task_title):
    """
    Use AI to suggest subtasks for complex tasks
    Returns a list of subtask titles
    """
    prompt = f"""
    Break down this task into 3-5 concrete, actionable subtasks.
    Task: "{task_title}"
    
    Return ONLY a JSON array of subtask titles:
    ["Subtask 1", "Subtask 2", "Subtask 3"]
    
    Make subtasks specific and actionable.
    Each subtask should be completable in 15-30 minutes.
    """
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi3",
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return []
        
        result = response.json()
        text = result.get("response", "").strip()
        
        # Extract JSON array
        array_match = re.search(r'\[.*?\]', text, re.DOTALL)
        if not array_match:
            return []
        
        subtasks = json.loads(array_match.group())
        
        # Clean and validate subtasks
        cleaned_subtasks = []
        for subtask in subtasks[:5]:  # Max 5 subtasks
            if isinstance(subtask, str):
                cleaned = clean_task_description(subtask.strip('"\''))
                if cleaned and len(cleaned) > 3:
                    cleaned_subtasks.append(cleaned)
        
        return cleaned_subtasks
        
    except Exception as e:
        print(f"Subtask generation error: {e}")
        return []