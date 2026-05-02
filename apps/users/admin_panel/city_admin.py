# apps/users/admin.py
from django.contrib import admin
from apps.users.models import City

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['id', 'city_id', 'name', 'province']
    list_filter = ['province']
    search_fields = ['name', 'city_id', 'province__name']
    ordering = ['province__name', 'name']
    list_per_page = 50
    list_select_related = ['province']