from django.urls import path 
from .views import * 

urlpatterns = [
    path("profile/", user_profile, name="profile"), 
    path("register/", login_or_register, name="user-register"),
    path("update/", update_profile, name="update-profile"), 
    path("delete/", delete_account, name="delete-account")
]
