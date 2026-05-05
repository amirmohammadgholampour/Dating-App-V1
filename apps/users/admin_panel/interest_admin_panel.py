from django.contrib import admin 
from ..models import Interest 

@admin.register(Interest) 
class InterestAdmin(admin.ModelAdmin): 
    list_display = ["id", "name"] 
    search_fields = ["name"]