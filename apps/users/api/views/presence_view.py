from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class PresenceResponseSerializer(serializers.Serializer):
    is_online = serializers.BooleanField()
    last_seen_at = serializers.DateTimeField()


@extend_schema(
    summary="Update online presence",
    description="Call periodically while the app is active. Users are online for five minutes after their last heartbeat.",
    responses={200: PresenceResponseSerializer},
    tags=["Users"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def heartbeat(request):
    request.user.last_seen_at = timezone.now()
    request.user.save(update_fields=["last_seen_at"])
    return Response({"is_online": request.user.is_online, "last_seen_at": request.user.last_seen_at}, status=status.HTTP_200_OK)
