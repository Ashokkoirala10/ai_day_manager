from django.http import JsonResponse
from django.contrib.auth import authenticate
from .models import Routine, ChatMessage
from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserSerializer, 
    RegisterSerializer, 
    RoutineSerializer, 
    RoutineCreateSerializer,
    ChatMessageSerializer,
    ChatRequestSerializer
)

from django.utils import timezone

class RegisterView(generics.CreateAPIView):
    """
    Register a new user
    POST /api/auth/register/
    Body: {username, email, password, password2, first_name, last_name}
    """
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    """
    Login user
    POST /api/auth/login/
    Body: {username, password}
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Please provide both username and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )



class LogoutView(APIView):
    """
    Logout user (blacklist refresh token)
    POST /api/auth/logout/
    Body: {"refresh": "token_here"}
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        # Validate token is provided
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create RefreshToken instance and blacklist it
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'message': 'Logout successful'},
                status=status.HTTP_200_OK  # Changed from 205 to 200
            )
            
        except TokenError as e:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except AttributeError:
            # This happens if token blacklisting is not enabled
            return Response(
                {'error': 'Token blacklisting is not enabled. Add "rest_framework_simplejwt.token_blacklist" to INSTALLED_APPS'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        except Exception as e:
            # Log the actual error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Logout error: {str(e)}")
            
            return Response(
                {'error': 'An error occurred during logout'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR  # Changed from 400
            )
class UserProfileView(APIView):
    """
    Get current user profile
    GET /api/auth/profile/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Routine
from .serializers import RoutineSerializer, RoutineCreateSerializer
import logging

logger = logging.getLogger(__name__)


class RoutineListCreateView(generics.ListCreateAPIView):
    """
    List all routines or create new routine
    GET /api/routines/
    POST /api/routines/
    Body: {title, time, repeat_type, is_completed}
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RoutineCreateSerializer
        return RoutineSerializer
    
    def get_queryset(self):
        # Only return routines for the authenticated user
        if self.request.user.is_authenticated:
            return Routine.objects.filter(user=self.request.user)
        return Routine.objects.none()
    
    def perform_create(self, serializer):
        # Automatically set the user to the logged-in user
        if not self.request.user.is_authenticated:
            raise ValueError("User must be authenticated")
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        try:
            # Log request details for debugging
            logger.info(f"User: {request.user}")
            logger.info(f"User authenticated: {request.user.is_authenticated}")
            logger.info(f"Request data: {request.data}")
            logger.info(f"Headers: {request.headers.get('Authorization', 'No auth header')}")
            
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Authentication required. Please login.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            # Get the created routine and return full details
            routine = Routine.objects.get(id=serializer.instance.id)
            output_serializer = RoutineSerializer(routine)
            
            logger.info(f"Routine created successfully: {routine.id}")
            
            return Response(
                output_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except ValueError as e:
            logger.error(f"ValueError: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        except Exception as e:
            # Log detailed error for debugging
            logger.error(f"Error creating routine: {str(e)}", exc_info=True)
            
            return Response(
                {
                    'error': 'Failed to create routine',
                    'detail': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )




class RoutineDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a routine
    GET /api/routines/{id}/
    PUT /api/routines/{id}/
    PATCH /api/routines/{id}/
    DELETE /api/routines/{id}/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return RoutineCreateSerializer
        return RoutineSerializer
    
    def get_queryset(self):
        # Only allow access to user's own routines
        return Routine.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Handle PUT/PATCH updates"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            # Return full routine details using RoutineSerializer
            output_serializer = RoutineSerializer(instance)
            return Response(output_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating routine: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to update routine', 'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """Handle DELETE with custom response"""
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {'message': 'Routine deleted successfully'},
                status=status.HTTP_200_OK  # Changed from 202 to 200
            )
        except Exception as e:
            logger.error(f"Error deleting routine: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to delete routine', 'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def perform_destroy(self, instance):
        """Actually delete the instance (called by destroy method)"""
        instance.delete()

import requests
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status


class ChatView(APIView):
    """
    POST /api/chat/
    Body: {"message": "your message"}
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_message = serializer.validated_data['message']
        
        # Generate AI response using Ollama
        ai_response = self.generate_ai_response(user_message, request.user)
        
        # Handle error case
        if ai_response.get('error'):
            return Response(
                {'response': ai_response['message']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Save chat message
        chat_message = ChatMessage.objects.create(
            user=request.user,
            message=user_message,
            response=ai_response['message']
        )
        
        return Response({
            'message': user_message,
            'response': ai_response['message'],
            'timestamp': chat_message.created_at
        })
    
    def generate_ai_response(self, message, user):
        """
        Generate AI response using Ollama local AI
        """
        # Get user's routines context
        routine_count = Routine.objects.filter(user=user).count()
        active_routines = Routine.objects.filter(user=user, is_active=True).count()
        
        # Build context-aware prompt
        prompt = f"""
        You are Ashok AI, a friendly day management assistant.
        
        User Context:
        - Name: {user.first_name or user.username}
        - Total routines: {routine_count}
        - Active routines: {active_routines}
        
        Reply naturally and concisely to help them manage their daily routines.
        
        User said: "{message}"
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
            
            return {"message": full_text.strip(), "error": False}
        
        except requests.exceptions.Timeout:
            return {
                "message": "⚠️ AI response timed out. Please try again.",
                "error": True
            }
        except requests.exceptions.ConnectionError:
            return {
                "message": "⚠️ Failed to connect to local AI. Make sure Ollama is running.",
                "error": True
            }
        except Exception as e:
            print(f"Chat Error: {e}")
            return {
                "message": "⚠️ An error occurred while generating response.",
                "error": True
            }