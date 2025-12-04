from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Routine, UserPreference, ProductivityLog, TaskNote
from django.contrib.auth.models import User
import json
import requests
from manager.scheduler.scheduler import start_scheduler, stop_scheduler, refresh_scheduler
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator


def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"]
        )
        if user:
            login(request, user)
            return redirect("dashboard")
        return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        email = request.POST.get("email", "")

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {"error": "Username already exists"})

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        
        # Create default user preferences
        UserPreference.objects.create(user=user)
        
        return redirect("login")

    return render(request, "register.html")


@login_required
def dashboard(request):
    today = timezone.now().date()
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    category_filter = request.GET.get('category', 'all')
    search_query = request.GET.get('search', '')
    
    # Base query
    routines = Routine.objects.filter(user=request.user, date=today, parent_task__isnull=True)
    
    # Apply filters
    if status_filter != 'all':
        routines = routines.filter(status=status_filter)
    if priority_filter != 'all':
        routines = routines.filter(priority=priority_filter)
    if category_filter != 'all':
        routines = routines.filter(category=category_filter)
    if search_query:
        routines = routines.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Calculate stats
    total_tasks = Routine.objects.filter(user=request.user, date=today).count()
    completed_tasks = Routine.objects.filter(user=request.user, date=today, is_completed=True).count()
    pending_tasks = total_tasks - completed_tasks
    
    # Calculate streak
    streak = calculate_streak(request.user)
    
    # Completion rate
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Get upcoming tasks
    now = timezone.localtime()
    upcoming = Routine.objects.filter(
        user=request.user,
        date=today,
        time__gt=now.time(),
        is_completed=False
    ).order_by('time')[:3]
    
    context = {
        'routines': routines,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'streak': streak,
        'completion_rate': round(completion_rate, 1),
        'upcoming': upcoming,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'search_query': search_query,
    }
    
    return render(request, "dashboard.html", context)


@login_required
@csrf_exempt
def add_routine(request):
    if request.method == "POST":
        # Handle both form data and JSON
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        title = data.get("title")
        time_str = data.get("time")
        repeat_type = data.get("repeat_type", "once")
        priority = data.get("priority", "medium")
        category = data.get("category", "other")
        description = data.get("description", "")
        date_str = data.get("date", timezone.now().date().isoformat())
        estimated_duration = data.get("estimated_duration", 30)
        tags = data.get("tags", "")
        
        # Parse natural language if needed
        if "at" in title.lower() or "by" in title.lower():
            parsed = parse_natural_language(title)
            if parsed:
                title = parsed.get("task", title)
                if parsed.get("time"):
                    time_str = parsed["time"]
                if parsed.get("date"):
                    date_str = parsed["date"]
        
        task = Routine.objects.create(
            user=request.user,
            title=title,
            time=time_str,
            date=date_str,
            repeat_type=repeat_type,
            priority=priority,
            category=category,
            description=description,
            estimated_duration=estimated_duration,
            tags=tags
        )
        
        # Check if AI should break down the task
        prefs = get_user_preferences(request.user)
        if prefs.ai_auto_breakdown and is_complex_task(title):
            breakdown_task(task)
        
        # Update productivity log
        update_productivity_log(request.user, 'created')
        
        # Refresh scheduler
        refresh_scheduler()
        
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'task_id': task.id,
                'message': 'Task added successfully'
            })
        
        return redirect("dashboard")
    
    return redirect("dashboard")


@login_required
def delete_routine(request, id):
    routine = get_object_or_404(Routine, id=id, user=request.user)
    routine.delete()
    refresh_scheduler()
    return redirect("dashboard")


@login_required
@csrf_exempt
def update_routine(request, id):
    """Update task details"""
    if request.method == "POST":
        routine = get_object_or_404(Routine, id=id, user=request.user)
        data = json.loads(request.body)
        
        # Update fields
        for field in ['title', 'description', 'time', 'date', 'priority', 'category', 'status', 'estimated_duration', 'tags']:
            if field in data:
                setattr(routine, field, data[field])
        
        routine.save()
        refresh_scheduler()
        
        return JsonResponse({'success': True, 'message': 'Task updated successfully'})
    
    return JsonResponse({'success': False}, status=400)


@login_required
@csrf_exempt
def toggle_complete(request, id):
    """Toggle task completion status"""
    routine = get_object_or_404(Routine, id=id, user=request.user)
    
    if routine.is_completed:
        routine.is_completed = False
        routine.status = 'pending'
        routine.completed_at = None
    else:
        routine.mark_complete()
        update_productivity_log(request.user, 'completed')
    
    return JsonResponse({
        'success': True,
        'is_completed': routine.is_completed,
        'completed_at': routine.completed_at.isoformat() if routine.completed_at else None
    })


@login_required
def get_task_details(request, id):
    """Get detailed task information including subtasks"""
    task = get_object_or_404(Routine, id=id, user=request.user)
    subtasks = task.get_subtasks()
    notes = task.notes.all()
    
    return JsonResponse({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'time': task.time.strftime('%H:%M'),
        'date': task.date.isoformat(),
        'priority': task.priority,
        'category': task.category,
        'status': task.status,
        'is_completed': task.is_completed,
        'estimated_duration': task.estimated_duration,
        'tags': task.tags,
        'subtasks': [{
            'id': st.id,
            'title': st.title,
            'is_completed': st.is_completed
        } for st in subtasks],
        'notes': [{
            'id': n.id,
            'content': n.content,
            'created_at': n.created_at.isoformat()
        } for n in notes]
    })


@login_required
@csrf_exempt
def add_subtask(request, parent_id):
    """Add subtask to a parent task"""
    if request.method == "POST":
        parent = get_object_or_404(Routine, id=parent_id, user=request.user)
        data = json.loads(request.body)
        
        subtask = Routine.objects.create(
            user=request.user,
            title=data.get('title'),
            time=parent.time,
            date=parent.date,
            parent_task=parent,
            priority=data.get('priority', parent.priority),
            category=parent.category,
            order=parent.subtasks.count() + 1
        )
        
        return JsonResponse({
            'success': True,
            'subtask': {
                'id': subtask.id,
                'title': subtask.title,
                'is_completed': subtask.is_completed
            }
        })
    
    return JsonResponse({'success': False}, status=400)


@login_required
@csrf_exempt
def add_note(request, task_id):
    """Add note to a task"""
    if request.method == "POST":
        task = get_object_or_404(Routine, id=task_id, user=request.user)
        data = json.loads(request.body)
        
        note = TaskNote.objects.create(
            task=task,
            content=data.get('content')
        )
        
        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,
                'content': note.content,
                'created_at': note.created_at.isoformat()
            }
        })
    
    return JsonResponse({'success': False}, status=400)


@login_required
def productivity_stats(request):
    """Get productivity statistics"""
    days = int(request.GET.get('days', 7))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get daily stats
    daily_stats = ProductivityLog.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')
    
    # Calculate totals
    total_created = sum(log.tasks_created for log in daily_stats)
    total_completed = sum(log.tasks_completed for log in daily_stats)
    avg_completion_rate = daily_stats.aggregate(Avg('completion_rate'))['completion_rate__avg'] or 0
    
    # Get category breakdown
    category_stats = Routine.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=end_date
    ).values('category').annotate(count=Count('id'))
    
    # Get hourly productivity
    hourly_stats = Routine.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=end_date,
        is_completed=True
    ).extra(select={'hour': 'EXTRACT(hour FROM time)'}).values('hour').annotate(count=Count('id'))
    
    return JsonResponse({
        'daily_stats': [{
            'date': log.date.isoformat(),
            'created': log.tasks_created,
            'completed': log.tasks_completed,
            'rate': log.completion_rate
        } for log in daily_stats],
        'totals': {
            'created': total_created,
            'completed': total_completed,
            'avg_completion_rate': round(avg_completion_rate, 1)
        },
        'category_breakdown': list(category_stats),
        'hourly_productivity': list(hourly_stats)
    })


# ===== CHAT SYSTEM =====
@csrf_exempt
@login_required
def chat_ai(request):
    data = json.loads(request.body)
    user_msg = data.get("message", "")

    if "chat_history" not in request.session:
        request.session["chat_history"] = []

    request.session["chat_history"].append({"sender": "user", "message": user_msg})
    request.session.modified = True

    # Enhanced prompt with context
    user_tasks = Routine.objects.filter(
        user=request.user,
        date=timezone.now().date()
    ).count()
    
    completed = Routine.objects.filter(
        user=request.user,
        date=timezone.now().date(),
        is_completed=True
    ).count()

    prompt = f"""
    You are Ashok AI, a friendly and intelligent day planner assistant.
    Current user stats: {user_tasks} tasks today, {completed} completed.
    
    Capabilities:
    - Help create tasks naturally (e.g., "remind me to call mom at 3pm tomorrow")
    - Suggest task breakdowns for complex tasks
    - Provide productivity tips
    - Answer questions about schedules
    
    User said: "{user_msg}"
    
    Reply naturally and concisely. If they want to add a task, extract the details.
    """

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "phi3", "prompt": prompt},
            timeout=180,
            stream=True
        )

        full_text = ""
        for line in response.iter_lines():
            if line:
                obj = json.loads(line.decode("utf-8"))
                token = obj.get("response", "") or obj.get("message", "")
                full_text += token

        request.session["chat_history"].append({"sender": "bot", "message": full_text})
        request.session.modified = True

        return JsonResponse({"response": full_text})

    except Exception as e:
        err_msg = "⚠️ Failed to connect to local AI."
        request.session["chat_history"].append({"sender": "bot", "message": err_msg})
        request.session.modified = True
        return JsonResponse({"response": err_msg}, status=500)


@login_required
def chat_history(request):
    history = request.session.get("chat_history", [])
    return JsonResponse({"history": history})


@login_required
def chat_clear(request):
    request.session["chat_history"] = []
    request.session.modified = True
    return JsonResponse({"status": "cleared"})


# ===== SCHEDULER FUNCTIONS =====
@login_required
def scheduler_start(request):
    start_scheduler()
    return JsonResponse({"status": "started"})


@login_required
def scheduler_stop(request):
    stop_scheduler()
    return JsonResponse({"status": "stopped"})


@login_required
def scheduler_check(request):
    now = timezone.localtime()
    tasks = Routine.objects.filter(
        user=request.user,
        date=now.date(),
        time__hour=now.hour,
        time__minute=now.minute,
        is_completed=False
    )

    if tasks.exists():
        task = tasks.first()
        return JsonResponse({
            "due": True,
            "task": task.title,
            "priority": task.priority,
            "id": task.id
        })

    return JsonResponse({"due": False})


# ===== HELPER FUNCTIONS =====
def get_user_preferences(user):
    """Get or create user preferences"""
    prefs, created = UserPreference.objects.get_or_create(user=user)
    return prefs


def calculate_streak(user):
    """Calculate user's daily completion streak"""
    today = timezone.now().date()
    streak = 0
    check_date = today
    
    while True:
        log = ProductivityLog.objects.filter(user=user, date=check_date).first()
        if not log or log.completion_rate < 50:
            break
        streak += 1
        check_date -= timedelta(days=1)
    
    return streak


def update_productivity_log(user, action):
    """Update daily productivity log"""
    today = timezone.now().date()
    log, created = ProductivityLog.objects.get_or_create(
        user=user,
        date=today,
        defaults={
            'tasks_created': 0,
            'tasks_completed': 0
        }
    )
    
    if action == 'created':
        log.tasks_created += 1
    elif action == 'completed':
        log.tasks_completed += 1
    
    log.calculate_completion_rate()


def is_complex_task(title):
    """Determine if task should be broken down"""
    keywords = ['project', 'plan', 'organize', 'prepare', 'setup', 'create', 'build', 'develop']
    return any(keyword in title.lower() for keyword in keywords)


def breakdown_task(parent_task):
    """Use AI to break down complex tasks"""
    prompt = f"""
    Break down this task into 3-5 subtasks: "{parent_task.title}"
    Return ONLY a JSON array like: ["subtask1", "subtask2", "subtask3"]
    """
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "phi3", "prompt": prompt},
            timeout=60
        )
        
        text = ""
        for line in response.iter_lines():
            if line:
                obj = json.loads(line.decode("utf-8"))
                text += obj.get("response", "")
        
        # Extract JSON array
        import re
        match = re.search(r'\[.*?\]', text, re.DOTALL)
        if match:
            subtasks = json.loads(match.group())
            for i, subtask_title in enumerate(subtasks[:5], 1):
                Routine.objects.create(
                    user=parent_task.user,
                    title=subtask_title.strip('"'),
                    time=parent_task.time,
                    date=parent_task.date,
                    parent_task=parent_task,
                    priority=parent_task.priority,
                    category=parent_task.category,
                    order=i
                )
    except Exception as e:
        print(f"Task breakdown error: {e}")


def parse_natural_language(text):
    """Parse natural language input for task creation"""
    from manager.utills.ai_parser import parse_command
    return parse_command(text)