from uuid import uuid4
from datetime import timedelta
from django.utils.timezone import now

import os
import django
import sys
import random

# Configure Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weenat_test_api.settings")
django.setup()
from api.models import Datalogger, Measurement



#Create dummy entries
def create_test_data():
    
    NUM_DATALOGGERS = 3
    NUM_MEASUREMENTS_PER_DATALOGGER = 50
    LABELS = ['temp', 'hum', 'rain']

    RANGES = {
        'temp': lambda: round(random.uniform(-20, 40), 1),
        'hum': lambda: round(random.uniform(20, 100), 1),
        'rain': lambda: round(random.uniform(0, 2), 1)
    }
    
    for _ in range(NUM_DATALOGGERS):
        datalogger = Datalogger.objects.create(
            uuid=uuid4(),
            lat=round(random.uniform(-90, 90), 4),
            lng=round(random.uniform(-180, 180), 4)
        )
        print(f"Created datalogger: {datalogger.uuid}")

        base_time = now() - timedelta(days=1)

        for i in range(NUM_MEASUREMENTS_PER_DATALOGGER):
            label = random.choice(LABELS)
            value = RANGES[label]()
            at = base_time + timedelta(minutes=i * 10)

            Measurement.objects.create(
                datalogger=datalogger,
                label=label,
                value=value,
                at=at
            )
            
        print("Population complete")

def delete_all_data():
    
    print("Deleting all data...")
    Measurement.objects.all().delete()
    Datalogger.objects.all().delete()
    print("🗑️ All data deleted.")


if __name__ == "__main__":
    
    if len(sys.argv) < 2:
            print("Usage: python manage.py shell < populate_db.py [populate|delete]")
    else:
        command = sys.argv[1].lower()
        if command == "populate":
            create_test_data()
        elif command == "delete":
            delete_all_data()
        else:
            print("Unknown command. Use 'populate' or 'delete'.")