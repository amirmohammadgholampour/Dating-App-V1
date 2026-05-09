from django.urls import path 
from .views import * 

urlpatterns = [
    path("conversations/", my_conversations, name="my-conversation"),    
    path("conversations/<int:conversation_id>/send/", send_message, name="send-message"),
    path('conversations/<int:conversation_id>/messages/', get_messages, name='get-messages'),
    path('conversations/<int:conversation_id>/poll/', poll_messages, name='poll-messages'),
]
