from django.urls import path

from apps.notification.api.views.notification_view import read_unread_notifications


urlpatterns = [
    path("unread/read/", read_unread_notifications, name="read-unread-notifications"),
]
