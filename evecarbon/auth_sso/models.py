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

class Alliance(models.Model):
    alliance_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255)
    ticker = models.CharField(max_length=10, blank=True, null=True)
    blue = models.BooleanField(default=False)  # The "blue list" flag

    def __str__(self):
        return f"[{self.ticker or '???'}] {self.name} ({self.alliance_id})"
