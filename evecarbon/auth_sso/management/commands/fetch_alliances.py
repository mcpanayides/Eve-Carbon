from django.core.management.base import BaseCommand
import requests
from evecarbon.auth_sso.models import Alliance

ESI_BASE = "https://esi.evetech.net/latest"

class Command(BaseCommand):
    help = "Fetch all alliances from ESI and update DB"

    def handle(self, *args, **options):
        alliance_ids = requests.get(f"{ESI_BASE}/alliances/").json()
        for aid in alliance_ids:
            info = requests.get(f"{ESI_BASE}/alliances/{aid}/").json()
            obj, created = Alliance.objects.update_or_create(
                alliance_id=aid,
                defaults={
                    "name": info.get("name"),
                    "ticker": info.get("ticker"),
                }
            )
            if created:
                self.stdout.write(f"Added alliance: {obj}")
        self.stdout.write(self.style.SUCCESS("Alliance list updated."))
