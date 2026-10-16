from django.db import transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notification.api.serializers.notification_serializer import (
    NotificationSerializer,
    ReadUnreadNotificationsResponseSerializer,
)
from apps.notification.models import Notification


@extend_schema(
    summary="Read unread notifications",
    description=(
        "Return all unread notifications for the authenticated user and mark them as read. "
        "The returned notifications have is_read set to true."
    ),
    request=None,
    responses={
        200: ReadUnreadNotificationsResponseSerializer,
        401: OpenApiResponse(description="Authentication required."),
    },
    tags=["Notifications"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def read_unread_notifications(request):
    """Return the current user's unread notifications and mark them as read."""
    with transaction.atomic():
        unread_notifications = list(
            Notification.objects.select_for_update()
            .filter(recipient=request.user, is_read=False)
            .select_related("actor")
            .order_by("-created_at")
        )

        if unread_notifications:
            notification_ids = [notification.id for notification in unread_notifications]
            Notification.objects.filter(id__in=notification_ids).update(is_read=True)
            for notification in unread_notifications:
                notification.is_read = True

    return Response(
        {
            "message": "Unread notifications returned and marked as read.",
            "count": len(unread_notifications),
            "data": NotificationSerializer(unread_notifications, many=True).data,
        },
        status=status.HTTP_200_OK,
    )
