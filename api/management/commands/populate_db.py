from datetime import datetime, timedelta
import random
from typing import Any
from uuid import uuid4

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from api.models import Datalogger, Measurement

LABELS = ["temp", "hum", "rain"]
RANGES = {
    "temp": lambda: round(random.uniform(-20, 40), 1),
    "hum": lambda: round(random.uniform(20, 100), 1),
    "rain": lambda: round(random.uniform(0, 2), 1),
}


class Command(BaseCommand):
    """
    Populate the database with
    random dataloggers and associated measurements.
    """

    def add_arguments(self, parser: Any) -> None:
        """
        Add command-line arguments to specify the number of dataloggers
        and measurements per datalogger to create.

        Args:
            parser: The argument parser instance.
        """
        parser.add_argument(
            "--dataloggers", type=int, default=3, help="Number of dataloggers"
        )
        parser.add_argument(
            "--measurements", type=int, default=50, help="Measurements per datalogger"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Create specified numbers of dataloggers and measurements.
        Measurement timestamps are randomly distributed over the last 5 days.

        Args:
            *args: Additional positional arguments.
            **options: Command options, expects 'dataloggers' and 'measurements'.
        """
        num_dataloggers = options["dataloggers"]
        num_measurements = options["measurements"]

        self.stdout.write(
            f"Creating {num_dataloggers} dataloggers with {num_measurements} measurements each..."
        )

        for _ in range(num_dataloggers):
            datalogger = Datalogger.objects.create(
                id=uuid4(),
                lat=round(random.uniform(-90, 90), 4),
                lng=round(random.uniform(-180, 180), 4),
            )

            for _ in range(num_measurements):
                # Generate a datetime within the last 5 days
                base_time: datetime = now() - timedelta(days=5)
                at: datetime = base_time + timedelta(
                    days=random.randint(0, 4),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                    seconds=random.randint(0, 59),
                )

                label = random.choice(LABELS)
                value = RANGES[label]()

                # Store the datetime object directly, not its ISO string
                Measurement.objects.create(
                    datalogger=datalogger, label=label, value=value, at=at
                )

            self.stdout.write(f"Created datalogger: {datalogger.id}")

        self.stdout.write(self.style.SUCCESS("Population complete."))
