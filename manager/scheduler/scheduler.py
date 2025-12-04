# manager/scheduler/scheduler.py
import schedule
import time
import threading
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q

# Conditional imports with fallbacks
try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    print("⚠️ plyer not installed. Desktop notifications disabled.")
    NOTIFICATIONS_AVAILABLE = False

try:
    from manager.utills.tts_engine import speak
    TTS_AVAILABLE = True
except ImportError:
    print("⚠️ TTS engine not available. Voice reminders disabled.")
    TTS_AVAILABLE = False

_scheduler_thread = None
_running = False


def notify(task_id, task_title, priority='medium', repeat_times=2, interval=3):
    """
    Enhanced notification system with desktop and voice alerts
    
    Args:
        task_id: Task database ID
        task_title: Task title to display
        priority: Task priority (high/medium/low)
        repeat_times: How many times to speak reminder
        interval: Seconds between speech repetitions
    """
    from manager.models import Routine
    from time import sleep
    
    try:
        # Get task from database to check if it's still active
        task = Routine.objects.filter(id=task_id).first()
        if not task or task.is_completed:
            print(f"⏭️ Skipping reminder for completed/deleted task: {task_title}")
            return
        
        # Mark that reminder was sent
        task.reminder_sent = True
        task.save(update_fields=['reminder_sent'])
        
        now_str = datetime.now().strftime("%I:%M %p")
        message = f"⏰ {task_title}"
        
        # Priority emoji
        priority_emoji = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
        emoji = priority_emoji.get(priority, '📋')
        
        print(f"{emoji} REMINDER [{now_str}] → {task_title}")
        
        # Desktop notification
        if NOTIFICATIONS_AVAILABLE:
            try:
                notification.notify(
                    title=f"{emoji} Task Reminder - {priority.upper()}",
                    message=message,
                    app_name="AI Day Planner",
                    timeout=10
                )
            except Exception as e:
                print(f"⚠️ Desktop notification failed: {e}")
        
        # Voice reminder (TTS)
        if TTS_AVAILABLE:
            try:
                speech_message = f"Reminder: {task_title}"
                if priority == 'high':
                    speech_message = f"Important reminder: {task_title}"
                
                for i in range(repeat_times):
                    print(f"🗣️ Speaking reminder {i+1}/{repeat_times}")
                    speak(speech_message)
                    if i < repeat_times - 1:
                        sleep(interval)
            except Exception as e:
                print(f"⚠️ TTS failed: {e}")
        
    except Exception as e:
        print(f"❌ Notification error for task '{task_title}': {e}")


def schedule_task(task):
    """
    Schedule a single task with enhanced logic
    
    Args:
        task: Routine model instance
    """
    try:
        task_id = task.id
        title = task.title
        task_time = task.time.strftime("%H:%M")
        task_date = task.date
        repeat_type = task.repeat_type
        priority = task.priority
        
        today = timezone.now().date()
        
        # Only schedule tasks for today or future
        if task_date < today:
            print(f"⏭️ Skipping past task: {title} ({task_date})")
            return
        
        # Different scheduling based on repeat type
        if repeat_type == 'once':
            # Only schedule if task is for today
            if task_date == today:
                schedule.every().day.at(task_time).do(
                    notify, task_id, title, priority
                ).tag(f"task_{task_id}", "once")
                print(f"⏰ Scheduled ONCE: '{title}' at {task_time} [{priority}]")
        
        elif repeat_type == 'daily':
            schedule.every().day.at(task_time).do(
                notify, task_id, title, priority
            ).tag(f"task_{task_id}", "daily")
            print(f"⏰ Scheduled DAILY: '{title}' at {task_time} [{priority}]")
        
        elif repeat_type == 'weekly':
            # Get day of week
            day_name = task_date.strftime("%A").lower()
            getattr(schedule.every(), day_name).at(task_time).do(
                notify, task_id, title, priority
            ).tag(f"task_{task_id}", "weekly")
            print(f"⏰ Scheduled WEEKLY: '{title}' every {day_name.title()} at {task_time} [{priority}]")
        
        elif repeat_type == 'monthly':
            # Monthly tasks - check date each day
            schedule.every().day.at(task_time).do(
                check_and_notify_monthly, task_id, title, priority, task_date.day
            ).tag(f"task_{task_id}", "monthly")
            print(f"⏰ Scheduled MONTHLY: '{title}' on day {task_date.day} at {task_time} [{priority}]")
        
    except Exception as e:
        print(f"⚠️ Failed to schedule task '{title}': {e}")


def check_and_notify_monthly(task_id, title, priority, target_day):
    """
    Check if today matches the target day of month for monthly tasks
    """
    today = datetime.now().day
    if today == target_day:
        notify(task_id, title, priority)


def schedule_all_routines():
    """
    Load all active routines and schedule them
    Clear existing schedule first
    """
    from manager.models import Routine
    
    print("\n" + "="*50)
    print("🔄 REFRESHING SCHEDULER")
    print("="*50)
    
    # Clear all existing jobs
    schedule.clear()
    print("✅ Cleared existing schedule")
    
    try:
        # Get all non-completed tasks
        today = timezone.now().date()
        routines = Routine.objects.filter(
            Q(is_completed=False) &
            (Q(date__gte=today) | Q(repeat_type__in=['daily', 'weekly', 'monthly']))
        ).select_related('user')
        
        scheduled_count = 0
        for task in routines:
            schedule_task(task)
            scheduled_count += 1
        
        print(f"\n✅ Scheduled {scheduled_count} task(s)")
        print(f"📊 Total jobs in schedule: {len(schedule.get_jobs())}")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"❌ Error scheduling routines: {e}")


def _scheduler_loop():
    """
    Main scheduler loop that runs in background thread
    Checks every 30 seconds for pending tasks
    """
    print("🚀 Scheduler loop started")
    check_interval = 30  # seconds
    
    while _running:
        try:
            schedule.run_pending()
            
            # Show active jobs count every 5 minutes
            if datetime.now().second == 0 and datetime.now().minute % 5 == 0:
                job_count = len(schedule.get_jobs())
                print(f"💓 Scheduler heartbeat - {job_count} active job(s)")
            
        except Exception as e:
            print(f"⚠️ Scheduler loop error: {e}")
        
        time.sleep(check_interval)
    
    print("🛑 Scheduler loop stopped")


def start_scheduler():
    """
    Start the background scheduler thread
    """
    global _scheduler_thread, _running
    
    if _scheduler_thread and _scheduler_thread.is_alive():
        print("⚠️ Scheduler already running")
        return
    
    print("\n" + "="*50)
    print("🚀 STARTING SCHEDULER")
    print("="*50)
    
    _running = True
    
    # Load all routines
    schedule_all_routines()
    
    # Start background thread
    _scheduler_thread = threading.Thread(
        target=_scheduler_loop,
        daemon=True,
        name="SchedulerThread"
    )
    _scheduler_thread.start()
    
    print("✅ Scheduler started successfully")
    print("="*50 + "\n")


def stop_scheduler():
    """
    Stop the scheduler thread safely
    """
    global _running, _scheduler_thread
    
    print("\n" + "="*50)
    print("🛑 STOPPING SCHEDULER")
    print("="*50)
    
    _running = False
    
    if _scheduler_thread:
        _scheduler_thread.join(timeout=5)
        if _scheduler_thread.is_alive():
            print("⚠️ Scheduler thread did not stop gracefully")
        else:
            print("✅ Scheduler thread stopped")
    
    # Clear all jobs
    schedule.clear()
    print("✅ Cleared all scheduled jobs")
    print("="*50 + "\n")


def refresh_scheduler():
    """
    Reload routines without stopping the thread
    Useful when tasks are added/modified
    """
    print("\n🔄 Quick refresh - reloading tasks...")
    schedule_all_routines()


def get_scheduler_status():
    """
    Get current scheduler status and statistics
    
    Returns:
        dict: Scheduler status information
    """
    global _running, _scheduler_thread
    
    is_alive = _scheduler_thread.is_alive() if _scheduler_thread else False
    job_count = len(schedule.get_jobs())
    
    # Get job breakdown by tag
    jobs_by_type = {
        'once': len([j for j in schedule.get_jobs() if 'once' in j.tags]),
        'daily': len([j for j in schedule.get_jobs() if 'daily' in j.tags]),
        'weekly': len([j for j in schedule.get_jobs() if 'weekly' in j.tags]),
        'monthly': len([j for j in schedule.get_jobs() if 'monthly' in j.tags]),
    }
    
    return {
        'running': _running,
        'thread_alive': is_alive,
        'total_jobs': job_count,
        'jobs_by_type': jobs_by_type,
        'next_run': schedule.next_run() if job_count > 0 else None
    }


def test_scheduler():
    """
    Test function to verify scheduler is working
    Schedules a test notification 10 seconds from now
    """
    print("\n🧪 TESTING SCHEDULER")
    print("="*50)
    
    test_time = (datetime.now() + timedelta(seconds=10)).strftime("%H:%M:%S")
    
    schedule.every().day.at(test_time).do(
        lambda: print("✅ TEST NOTIFICATION: Scheduler is working!")
    ).tag("test")
    
    print(f"⏰ Test notification scheduled for {test_time}")
    print(f"Waiting 10 seconds...")
    print("="*50 + "\n")


# Auto-start scheduler when module is imported (optional)
# Uncomment if you want scheduler to start automatically with Django
# import atexit
# start_scheduler()
# atexit.register(stop_scheduler)