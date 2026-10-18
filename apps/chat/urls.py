from django.urls import path 
from .views import * 
from apps.chat.api.views.message_actions import message_attachment, set_message_pinned

urlpatterns = [
    path("conversations/", my_conversations, name="my-conversation"),    
    path("conversations/<int:conversation_id>/send/", send_message, name="send-message"),
    path('conversations/<int:conversation_id>/messages/', get_messages, name='get-messages'),
    path('conversations/<int:conversation_id>/poll/', poll_messages, name='poll-messages'),
    path('conversations/<int:conversation_id>/messages/<int:message_id>/pin/', set_message_pinned, name='pin-message'),
    path('messages/<int:message_id>/media/', message_attachment, name='chat-message-media'),
]
