# apps/users/admin.py
from django.contrib import admin
from apps.users.models import Province

@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['id', 'province_id', 'name', 'city_count']
    search_fields = ['name', 'province_id']
    ordering = ['name']
    list_per_page = 31
    
    def city_count(self, obj):
        return obj.cities.count()
    city_count.short_description = "Number of cities"