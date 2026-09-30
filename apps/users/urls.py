from django.urls import path 
from .views import *
from apps.users.api.views.auth_views import (
    email_login, email_register, phone_login_request_code,
    phone_login_verify_code, phone_register_request_code,
    phone_register_verify_code,
)
from apps.users.api.views.presence_view import heartbeat

urlpatterns = [
    path("profile/", user_profile, name="profile"), 
    path("auth/register/email/", email_register, name="user-register-email"),
    path("auth/login/email/", email_login, name="user-login-email"),
    path("auth/register/phone/request-code/", phone_register_request_code, name="user-register-phone-request-code"),
    path("auth/register/phone/verify-code/", phone_register_verify_code, name="user-register-phone-verify-code"),
    path("auth/login/phone/request-code/", phone_login_request_code, name="user-login-phone-request-code"),
    path("auth/login/phone/verify-code/", phone_login_verify_code, name="user-login-phone-verify-code"),
    path("presence/heartbeat/", heartbeat, name="presence-heartbeat"),
    path("update/", update_profile, name="update-profile"), 
    path("delete/", delete_account, name="delete-account"),
    path("auth/logout/", logout, name="logout"),
]
