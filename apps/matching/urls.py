from django.urls import path 
from .views import (
    discover_view, 
    create_swipe, 
    recieved_requests, 
    accept_request, 
    reject_request
)

urlpatterns = [
    path("discover/profile/", discover_view, name="disocver-profile"), 
    path("swipe/", create_swipe, name="create-swipe"), 
    path("chat-requests/recieved/", recieved_requests, name="recieved-requests"), 
    path('chat-requests/<int:pk>/accept/', accept_request, name='accept-request'),
    path('chat-requests/<int:pk>/reject/', reject_request, name='reject-request'),
]