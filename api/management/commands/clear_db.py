from typing import Any

from django.core.management.base import BaseCommand

from api.models import Datalogger, Measurement


class Command(BaseCommand):
    help = "Delete all dataloggers and measurements from the database"

    def handle(self, *args: Any, **options: Any) -> None:
        Measurement.objects.all().delete()
        Datalogger.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS("All dataloggers and measurements deleted")
        )