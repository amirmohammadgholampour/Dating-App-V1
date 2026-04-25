from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username',
        'first_name',
        'last_name',
        'age',
        'city',
        'gender',
        'is_active',
        'is_staff',
    ]
    list_display_links = ['username', 'first_name', 'last_name']

    list_filter = [
        'gender',
        'city',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
    ]

    search_fields = [
        'username',
        'first_name',
        'last_name',
        'city',
    ]

    ordering = ['-date_joined']

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'date_of_birth',
                'gender',
                'bio',
                'profile_picture',
            )
        }),
        ('Location', {
            'fields': ('city',)
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'password1',
                'password2',
                'date_of_birth',
                'gender',
                'city',
                'bio',
                'profile_picture',
            ),
        }),
    )