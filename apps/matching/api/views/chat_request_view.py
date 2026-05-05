from rest_framework.decorators import api_view, permission_classes 
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated 

from drf_yasg.utils import swagger_auto_schema 
from drf_yasg import openapi 

from apps.matching.models import ChatRequest 
from apps.chat.models import Conversation 
from apps.matching.api.serializers.chat_request_serializer import ReceivedRequestSerializer 


@swagger_auto_schema(
    method="GET",
    responses={
        200: ReceivedRequestSerializer(many=True),
        401: openapi.Response(description="Authentication required"),
    },
    operation_description="Get list of pending chat requests received by the current user.",
    operation_summary="Received Chat Requests",
    tags=['Matching']
)
@api_view(["GET"]) 
@permission_classes([IsAuthenticated]) 
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