from django.urls import path 
from .views import (
    discover_view, 
    create_swipe, 
    recieved_requests
)

urlpatterns = [
    path("discover/profile/", discover_view, name="disocver-profile"), 
    path("swipe/", create_swipe, name="create-swipe"), 
    path("chat-requests/recieved/", recieved_requests, name="recieved-requests"), 
]
