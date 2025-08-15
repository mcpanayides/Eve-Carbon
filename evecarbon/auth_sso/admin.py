from django.contrib import admin
from .models import Alliance, UserProfile

@admin.register(Alliance)
class AllianceAdmin(admin.ModelAdmin):
    list_display = ("name", "ticker", "alliance_id", "blue")
    search_fields = ("name", "ticker", "alliance_id")
    list_filter = ("blue",)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("character_name", "character_id", "corporation_id", "alliance_id")
    search_fields = ("character_name", "character_id", "corporation_id", "alliance_id")
