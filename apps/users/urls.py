from django.urls import path 
from .views import * 

urlpatterns = [
    path("profile/", user_profile, name="profile") 
]
