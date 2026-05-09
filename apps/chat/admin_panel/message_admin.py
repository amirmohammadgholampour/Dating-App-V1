# apps/chat/admin.py
from django.contrib import admin
from apps.chat.models import Message 

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'content_preview', 'sent_at']
    list_filter = ['sent_at', 'is_edited']
    search_fields = ['content', 'sender__phone_number']
    readonly_fields = ['sent_at', 'read_at', 'is_edited', 'edited_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content"