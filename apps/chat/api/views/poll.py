from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from django.utils import timezone 

from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer, OpenApiParameter
from rest_framework import serializers

from apps.chat.models import Conversation, Message
from apps.chat.api.serializers.message_serializer import MessageSerializer
from apps.utils.custom_rate_limit import custom_ratelimit


@extend_schema(
    summary="Poll Messages",
    description="Poll for new messages after a timestamp.",
    parameters=[
        OpenApiParameter('after', type=str, description="ISO datetime string (e.g., 2026-05-09T10:00:00).", required=True),
    ],
    responses={
        200: inline_serializer(
            name="PollingResponse",
            fields={
                "messages": serializers.ListField(child=serializers.DictField()),
                "has_new": serializers.BooleanField(),
                "server_time": serializers.CharField(),
            }
        ),
        400: OpenApiResponse(description="Missing or invalid 'after' parameter"),
        403: OpenApiResponse(description="Not a member"),
        404: OpenApiResponse(description="Conversation not found"),
    },
    tags=['Chat']
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@custom_ratelimit(key="user", rate='20/min', method="GET", block=True)
def poll_messages(request, conversation_id):
    """
    GET /api/chat/conversations/{id}/poll/?after=2026-05-09T10:00:00
    Return messages sent after the given timestamp.
    """
    after_param = request.query_params.get('after')

    if not after_param:
        return Response(
            {"message": "Parameter 'after' is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    after_datetime = parse_datetime(after_param)
    if not after_datetime:
        return Response(
            {"message": "Invalid datetime format. Use ISO format (e.g., 2026-05-09T10:00:00)."},
            status=status.HTTP_400_BAD_REQUEST
        )

    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in [conversation.user1, conversation.user2]:
        return Response(
            {"message": "You are not a member of this conversation."},
            status=status.HTTP_403_FORBIDDEN
        )

    messages = Message.objects.filter(
        conversation=conversation,
        sent_at__gt=after_datetime
    ).exclude(
        sender=request.user
    ).select_related('sender').order_by('sent_at')

    serializer = MessageSerializer(messages, many=True)

    return Response(
        {
            "messages": serializer.data,
            "has_new": messages.exists(),
            "server_time": timezone.now().isoformat(),
        },
        status=status.HTTP_200_OK
    )