from rest_framework.decorators import api_view, permission_classes 
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response 
from rest_framework import status 

from drf_yasg import openapi 
from drf_yasg.utils import swagger_auto_schema 

from apps.matching.models import Swipe, ChatRequest 
from apps.matching.api.serializers.create_swipe_serializer import CreateSwipeSerializer
from apps.utils.custom_rate_limit import custom_ratelimit 


@swagger_auto_schema(
    method="POST",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['swipee', 'action'],
        properties={
            'swipee': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="ID of the user being swiped on"
            ),
            'action': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="'request' or 'reject'"
            ),
        }
    ),
    responses={
        201: openapi.Response(
            description="Swipe recorded successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'swipe_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'action': openapi.Schema(type=openapi.TYPE_STRING),
                    'chat_request_sent': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                }
            )
        ),
        400: openapi.Response(description="Validation error"),
        401: openapi.Response(description="Authentication required"),
    },
    operation_description="Swipe on a user profile (request chat or reject).",
    operation_summary="Create Swipe",
    tags=['Matching']
)
@api_view(["POST"]) 
@permission_classes([IsAuthenticated])
@custom_ratelimit(key="user", rate='30/min', method="POST", block=True)
def create_swipe(request): 
    """
    POST /api/swipe/
    Record a swipe action and create a ChatRequest if action is 'request'.
    """
    serializer = CreateSwipeSerializer(
        data = request.data, 
        context={"request": request} 
    )

    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors,}, 
            status=status.HTTP_400_BAD_REQUEST
        ) 
    
    swipe = serializer.save() 

    chat_request_sent = False 
    if swipe.action == "request": 
        ChatRequest.objects.get_or_create(
            from_user = request.user, 
            to_user = swipe.swipee, 
            defaults={"status": "pending"} 
        )
        chat_request_sent = True 
    
    return Response({
        "message": "Swipe recorded successfully.", 
        "swipe_id": swipe.id, 
        "action": swipe.action,
        "chat_request_sent": chat_request_sent
    }, status=status.HTTP_201_CREATED)