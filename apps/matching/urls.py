from django.urls import path 
from .views import (
    discover_view, 
    create_swipe, 
    recieved_requests, 
    accept_request, 
    reject_request
)
from apps.matching.api.views.discovery_suggestion_view import save_discovery_suggestions

urlpatterns = [
    path("discover/profile/", discover_view, name="disocver-profile"), 
    path("discover/suggestions/save/", save_discovery_suggestions, name="save-discovery-suggestions"),
    path("swipe/", create_swipe, name="create-swipe"), 
    path("chat-requests/recieved/", recieved_requests, name="recieved-requests"), 
    path('chat-requests/<int:pk>/accept/', accept_request, name='accept-request'),
    path('chat-requests/<int:pk>/reject/', reject_request, name='reject-request'),
]
