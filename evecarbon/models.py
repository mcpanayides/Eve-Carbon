# models.py

from django.contrib.auth.models import User
from django.db import models

class EveProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    character_id = models.CharField(max_length=50)
    character_name = models.CharField(max_length=100)
    corporation_name = models.CharField(max_length=100, blank=True, null=True)

class Ships(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name