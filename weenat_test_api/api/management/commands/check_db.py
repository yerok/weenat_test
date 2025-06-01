from django.core.management.base import BaseCommand

from api.models import Datalogger, Measurement


class Command(BaseCommand):
    help = "Show a summmary of the DB"

    def handle(self, *args, **options):
        dataloggers = Datalogger.objects.count()
        measurements = Measurement.objects.count()

        self.stdout.write(" Database status:")
        self.stdout.write(f"  -  Dataloggers : {dataloggers}")
        self.stdout.write(f"  -  Measurements: {measurements}")
