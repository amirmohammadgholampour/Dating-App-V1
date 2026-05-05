from django.urls import path 
from .views import (
    discover_view, 
    create_swipe
)

urlpatterns = [
    path("discover/profile/", discover_view, name="disocver-profile"), 
    path("swipe/", create_swipe, name="create-swipe")  
]
