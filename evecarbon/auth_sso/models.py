from django.conf import settings
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    character_id = models.BigIntegerField(unique=True)
    character_name = models.CharField(max_length=128)
    corporation_id = models.BigIntegerField(null=True, blank=True)
    alliance_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.character_name} ({self.character_id})"
