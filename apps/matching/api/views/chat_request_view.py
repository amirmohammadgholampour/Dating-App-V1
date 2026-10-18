from rest_framework.decorators import api_view, permission_classes 
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated 
from rest_framework import serializers
from django.db import transaction

from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer


from apps.matching.models import ChatRequest 
from apps.matching.api.serializers.chat_request_serializer import ReceivedRequestSerializer 
from apps.notification.models import Notification
from apps.utils.custom_rate_limit import custom_ratelimit
from apps.safety.models import Block
from apps.safety.services import users_are_blocked


@extend_schema(
    summary="Received Chat Requests",
    description="Get list of pending chat requests received by the current user.",
    responses={
        200: ReceivedRequestSerializer(many=True),
        401: OpenApiResponse(description="Authentication required"),
    },
    tags=['Matching']
)
@api_view(["GET"]) 
@permission_classes([IsAuthenticated]) 
@custom_ratelimit(key="user", rate='8/min', method="GET", block=True)
def recieved_requests(request): 
    """
    GET /api/chat-requests/received/
    Returns all pending chat requests sent TO the current user.
    """
    user = request.user 
    blocked_ids = set(Block.objects.filter(blocker=user).values_list("blocked_id", flat=True))
    blocked_ids.update(Block.objects.filter(blocked=user).values_list("blocker_id", flat=True))
    chat_requests = ChatRequest.objects.filter(
        to_user = user, 
        status = "pending" 
    ).exclude(from_user_id__in=blocked_ids).select_related("from_user", "from_user__city").order_by("-created_at")

    serializer = ReceivedRequestSerializer(chat_requests, many=True) 
    return Response({
        "message": "Recieved requests returned sucessfully.", 
        "data": serializer.data, 
        "count": chat_requests.count()
    }, status=status.HTTP_200_OK) 


@extend_schema(
    summary="Accept Chat Request",
    description="Accept a pending chat request and create a conversation.",
    request=None,
    responses={
        200: inline_serializer(
            name="AcceptChatResponse",
            fields={
                "message": serializers.CharField(),
                "conversation_id": serializers.IntegerField(),
            }
        ),
        400: OpenApiResponse(description="Request not found or already processed"),
        401: OpenApiResponse(description="Authentication required"),
        403: OpenApiResponse(description="Not your request to accept"),
    },
    tags=['Matching']
)
@api_view(["POST"]) 
@permission_classes([IsAuthenticated]) 
def accept_request(request, pk): 
    """
    POST /api/chat-requests/{id}/accept/
    Accept a pending chat request and create a conversation.
    """
    user = request.user
    try: 
        chat_request = ChatRequest.objects.get(
            id = pk, 
            to_user = user, 
            status = "pending"
        )
    except ChatRequest.DoesNotExist:
        return Response({
            "message": "Request not found or already processed."
        }, status=status.HTTP_400_BAD_REQUEST)

    if users_are_blocked(chat_request.from_user, chat_request.to_user):
        return Response(
            {"message": "This request cannot be accepted because one of these users has blocked the other."},
            status=status.HTTP_403_FORBIDDEN,
        )
    
    with transaction.atomic():
        conversation = chat_request.accept()
        Notification.objects.create(
            recipient=chat_request.from_user,
            actor=request.user,
            notification_type="chat_request_accepted",
            message=f"{request.user} accepted your chat request.",
            is_read=False,
        )

    return Response({
        "message": "Requested accepted successfully.", 
        "conversation_id": conversation.id
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Reject Chat Request",
    description="Reject a pending chat request.",
    request=None,
    responses={
        200: inline_serializer(
            name="RejectChatResponse",
            fields={"message": serializers.CharField()}
        ),
        400: OpenApiResponse(description="Request not found or already processed"),
        401: OpenApiResponse(description="Authentication required"),
        403: OpenApiResponse(description="Not your request to reject"),
    },
    tags=['Matching']
)
@api_view(["POST"]) 
@permission_classes([IsAuthenticated]) 
def reject_request(request, pk): 
    """
    POST /api/chat-requests/{id}/reject/
    Reject a pending chat request.
    """
    try:
        chat_request = ChatRequest.objects.get(
            id=pk,
            to_user=request.user,
            status='pending'
        )
    except ChatRequest.DoesNotExist:
        return Response(
            {"message": "Request not found or already processed."},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        chat_request.reject()
        Notification.objects.create(
            recipient=chat_request.from_user,
            actor=request.user,
            notification_type="chat_request_rejected",
            message=f"{request.user} rejected your chat request.",
            is_read=False,
        )

    return Response(
        {"message": "Request rejected successfully."},
        status=status.HTTP_200_OK
    )
