# apps/chat/admin.py
from django.contrib import admin
from apps.chat.models import Message, Conversation

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['sent_at', 'read_at', 'is_edited', 'edited_at']
    fields = ['sender', 'content', 'sent_at', 'read_at', 'is_edited']
    ordering = ['-sent_at']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user1', 'user2', 'created_at', 'updated_at', 'message_count']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user1__phone_number', 'user2__phone_number']
    inlines = [MessageInline]
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = "Messages"