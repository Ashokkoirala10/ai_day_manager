from django.contrib import admin
from django.urls import path
from manager import views
from rest_framework_simplejwt.views import TokenRefreshView
from manager.views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserProfileView,
    RoutineListCreateView,
    RoutineDetailView,
    ChatView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Authentication - Add 'api/' prefix
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    
    # Routines - Add 'api/' prefix
    path('routines/', RoutineListCreateView.as_view(), name='routine-list-create'),
    path('routines/<int:pk>/', RoutineDetailView.as_view(), name='routine-detail'),

        # ==================== CHAT ====================
    path('chat/', ChatView.as_view(), name='chat'),
]