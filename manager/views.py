from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Routine
from django.contrib.auth.models import User
import json
import requests
from manager.scheduler.scheduler import start_scheduler, stop_scheduler, refresh_scheduler

from django.utils import timezone

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

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    routines = Routine.objects.filter(user=request.user)
    return render(request, "dashboard.html", {"routines": routines})


@login_required
def add_routine(request):
    if request.method == "POST":
        Routine.objects.create(
            user=request.user,
            title=request.POST["title"],
            time=request.POST["time"],
            repeat_type=request.POST.get("repeat_type", "once")
        )
        # update scheduler immediately
        from manager.scheduler.scheduler import refresh_scheduler
        refresh_scheduler()
    return redirect("dashboard")


@login_required
def delete_routine(request, id):
    Routine.objects.filter(id=id, user=request.user).delete()
    return redirect("dashboard")


# 🔹 Chat with Ollama
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def chat_ai(request):
    data = json.loads(request.body)
    user_msg = data.get("message", "")

    prompt = f"""
    You are Ashok AI, a friendly day management assistant.
    Reply naturally and concisely.
    User said: "{user_msg}"
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

        return JsonResponse({"response": full_text})

    except Exception as e:
        print("Chat Error:", e)
        return JsonResponse({"response": "⚠️ Failed to connect to local AI."}, status=500)



# 🔹 Start/stop scheduler
@login_required
def scheduler_start(request):
    start_scheduler()
    return JsonResponse({"status": "started"})


@login_required
def scheduler_stop(request):
    stop_scheduler()
    return JsonResponse({"status": "stopped"})


# 🔹 Check if a routine is due
@login_required
def scheduler_check(request):
    now = timezone.localtime().strftime("%H:%M")
    tasks = Routine.objects.filter(user=request.user, time=now)

    if tasks.exists():
        return JsonResponse({"due": True, "task": tasks.first().title})

    return JsonResponse({"due": False})


def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        email = request.POST.get("email", "")

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {"error": "Username already exists"})

        User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        return redirect("login")

    return render(request, "register.html")

