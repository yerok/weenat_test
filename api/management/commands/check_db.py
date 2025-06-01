from typing import Any
from django.core.management.base import BaseCommand

from api.models import Datalogger, Measurement


class Command(BaseCommand):
    help = "Show a summary of the database status"

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Output a summary of the current database state
        counts the number of Datalogger and Measurement records and prints them.
        """
        dataloggers = Datalogger.objects.count()
        measurements = Measurement.objects.count()

        self.stdout.write("Database status:")
        self.stdout.write(f"  - Dataloggers : {dataloggers}")
        self.stdout.write(f"  - Measurements: {measurements}")