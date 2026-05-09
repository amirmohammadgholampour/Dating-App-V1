from django.contrib import admin 
from apps.safety.models import Report 

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'reporter',
        'reported',
        'reason',
        'created_at'
    ]
    list_filter = [
        'reason',
        'created_at',
    ]
    search_fields = [
        'reporter__phone_number',
        'reporter__first_name',
        'reporter__last_name',
        'reported__phone_number',
        'reported__first_name',
        'reported__last_name',
        'description',
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        (None, {
            'fields': ('reporter', 'reported', 'reason', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['reporter', 'reported', 'reason', 'description']
        return self.readonly_fields