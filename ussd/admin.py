from django.contrib import admin
from .models import USSDSession


@admin.register(USSDSession)
class USSDSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "phone_number", "current_step", "feeling", "reason")
    list_filter = ("current_step", "feeling", "reason")
    search_fields = ("session_id", "phone_number")
    readonly_fields = ("session_id", "user_id", "phone_number")