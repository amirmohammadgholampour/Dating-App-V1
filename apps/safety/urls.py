from django.urls import path

from apps.safety.api.views.block_views import blocks, unblock_user


urlpatterns = [
    path("blocks/", blocks, name="blocks"),
    path("blocks/<int:user_id>/", unblock_user, name="unblock-user"),
]
