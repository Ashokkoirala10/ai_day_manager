# manager/scheduler/scheduler.py
import schedule
import time
import threading
from datetime import datetime
from django.utils import timezone

from manager.utills.tts_engine import speak
from plyer import notification
from manager.models import Routine

_scheduler_thread = None
_running = False


def notify(task, repeat_times=3, interval=2):
    """Show desktop notification and speak the reminder"""
    from time import sleep
    now_str = datetime.now().strftime("%I:%M %p")
    message = f"It's {now_str}. Time to {task}!"
    print(f"🔔 Reminder → {message}")

    # Desktop notification
    try:
        notification.notify(
            title="Routine Reminder",
            message=message,
            timeout=5
        )
    except Exception as e:
        print("⚠️ Notification error:", e)

    # TTS speaking
    for i in range(repeat_times):
        print(f"🗣️ Speaking round {i+1}/{repeat_times}")
        speak(message)
        if i < repeat_times - 1:
            sleep(interval)


def normalize_time(time_str):
    """
    Convert to 24-hour HH:MM
    Accepts: '6 40 pm', '6:40 PM', '18:40'
    """
    time_str = time_str.strip().lower().replace('.', '')
    formats = ["%I %M %p", "%I:%M %p", "%H:%M", "%H%M"]
    for f in formats:
        try:
            dt = datetime.strptime(time_str, f)
            return dt.strftime("%H:%M")
        except ValueError:
            continue
    raise ValueError(f"Cannot parse time: '{time_str}'")


def get_upcoming_routines():
    """Load all routines for the scheduler."""
    routines = Routine.objects.all().values("title", "time", "repeat_type")
    return list(routines)


def schedule_all_routines():
    """Clear all and schedule routines"""
    schedule.clear()
    routines = Routine.objects.all().values("title", "time", "repeat_type")

    for r in routines:
        title = r["title"]
        time_raw = r["time"].strftime("%H:%M")
        repeat_type = r["repeat_type"]

        try:
            normalized = normalize_time(time_raw)
            if repeat_type == "once":
                schedule.every().day.at(normalized).do(notify, title).tag("once")
            elif repeat_type == "daily":
                schedule.every().day.at(normalized).do(notify, title)
            elif repeat_type == "weekly":
                schedule.every().week.at(normalized).do(notify, title)
            print(f"⏰ Scheduled: '{title}' ({repeat_type}) at {normalized}")
        except Exception as e:
            print(f"⚠️ Skipping routine '{title}' (invalid time): {e}")



def _scheduler_loop():
    while _running:
        schedule.run_pending()
        time.sleep(5)


def start_scheduler():
    """Start background scheduler thread"""
    global _scheduler_thread, _running

    if _scheduler_thread and _scheduler_thread.is_alive():
        print("Scheduler already running")
        return

    _running = True
    schedule_all_routines()

    _scheduler_thread = threading.Thread(
        target=_scheduler_loop,
        daemon=True
    )
    _scheduler_thread.start()

    print("✅ Scheduler started")


def stop_scheduler():
    """Stop the scheduler thread safely"""
    global _running, _scheduler_thread

    _running = False
    if _scheduler_thread:
        _scheduler_thread.join()

    print("🛑 Scheduler stopped")


def refresh_scheduler():
    """Reload routines without restarting thread"""
    schedule_all_routines()
