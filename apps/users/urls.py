from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from apps.users.api.views.auth_views import (
    email_login,
    email_register,
    phone_login_request_code,
    phone_login_verify_code,
    phone_register_request_code,
    phone_register_verify_code,
)
from apps.users.api.views.change_password_view import change_password
from apps.users.api.views.delete_account_view import delete_account
from apps.users.api.views.logout_view import logout, logout_all
from apps.users.api.views.presence_view import heartbeat
from apps.users.api.views.update_profile_view import update_profile
from apps.users.api.views.user_profile_view import user_profile
from apps.utils.custom_rate_limit import custom_ratelimit


token_refresh_view = custom_ratelimit(
    key="ip", rate="10/5m", method="POST", block=True
)(TokenRefreshView.as_view())
token_verify_view = custom_ratelimit(
    key="ip", rate="20/5m", method="POST", block=True
)(TokenVerifyView.as_view())

urlpatterns = [
    path("profile/", user_profile, name="profile"),
    path("update/", update_profile, name="update-profile"),
    path("delete/", delete_account, name="delete-account"),
    path("presence/heartbeat/", heartbeat, name="presence-heartbeat"),
    path("auth/register/email/", email_register, name="user-register-email"),
    path("auth/login/email/", email_login, name="user-login-email"),
    path("auth/register/phone/request-code/", phone_register_request_code, name="user-register-phone-request-code"),
    path("auth/register/phone/verify-code/", phone_register_verify_code, name="user-register-phone-verify-code"),
    path("auth/login/phone/request-code/", phone_login_request_code, name="user-login-phone-request-code"),
    path("auth/login/phone/verify-code/", phone_login_verify_code, name="user-login-phone-verify-code"),
    path("auth/token/refresh/", token_refresh_view, name="user-token-refresh"),
    path("auth/token/verify/", token_verify_view, name="user-token-verify"),
    path("auth/change-password/", change_password, name="user-change-password"),
    path("auth/logout/", logout, name="logout"),
    path("auth/logout/all/", logout_all, name="user-logout-all"),
]
