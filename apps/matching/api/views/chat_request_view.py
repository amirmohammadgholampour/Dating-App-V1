from rest_framework.decorators import api_view, permission_classes 
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated 
from rest_framework import serializers

from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer


from apps.matching.models import ChatRequest 
from apps.matching.api.serializers.chat_request_serializer import ReceivedRequestSerializer 
from apps.utils.custom_rate_limit import custom_ratelimit


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
    chat_requests = ChatRequest.objects.filter(
        to_user = user, 
        status = "pending" 
    ).select_related("from_user", "from_user__city").order_by("-created_at")

    serializer = ReceivedRequestSerializer(chat_requests, many=True) 
    return Response({
        "message": "Recieved requests returned sucessfully.", 
        "data": serializer.data, 
        "count": chat_requests.count()
    }, status=status.HTTP_200_OK) 


@extend_schema(
    summary="Accept Chat Request",
    description="Accept a pending chat request and create a conversation.",
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
    
    conversation = chat_request.accept() 

    return Response({
        "message": "Requested accepted successfully.", 
        "conversation_id": conversation.id
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Reject Chat Request",
    description="Reject a pending chat request.",
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

    chat_request.reject()

    return Response(
        {"message": "Request rejected successfully."},
        status=status.HTTP_200_OK
    )