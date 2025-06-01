from collections import defaultdict
import copy
import json
from datetime import timedelta, datetime
import random
from typing import Dict, Any, List
from uuid import uuid4
from django.utils.timezone import now, make_naive

from api.models import Measurement


LABELS: List[str] = ['temp', 'hum', 'rain']

MEASUREMENT_RANGES: Dict[str, callable] = {
    'temp': lambda: round(random.uniform(-20, 40), 1),
    'hum': lambda: round(random.uniform(20, 100), 1),
    'rain': lambda: random.choice([round(x * 0.2, 1) for x in range(11)])
}

# fixed dataloggers for testing purposes
DATALOGGERS: Dict[str, Dict[str, float]] = {
    "c2a61e2e-068d-4670-a97c-72bfa5e2a58a": {"lat": 47.56321, "lng": 1.524568},
    "e6e4ae22-f8dd-4e9e-b0e6-7e2ddbc2c4ac": {"lat": 49.56321, "lng": -1.528768},
    "a7c91fbb-1234-4abc-8d12-1234567890ab": {"lat": 48.12345, "lng": 0.98765},
}

def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def generate_random_payload() -> Dict[str, Any]:
    """
    Generates a randomized payload matching the expected structure
    for the /api/ingest/ or /api/data/ endpoints.
    
    Returns:
        Dict[str, Any]: A valid payload dictionary with datetime, datalogger UUID,
                        geolocation, and one or several measurements.
    """
    # Randomly select a datalogger and get its location
    datalogger_id: str = random.choice(list(DATALOGGERS.keys()))
    location: Dict[str, float] = copy.deepcopy(DATALOGGERS[datalogger_id])

    # Generate a datetime within the last 5 days
    base_time: datetime = now() - timedelta(days=5)
    at: datetime = base_time + timedelta(
        days=random.randint(0, 4),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    at_str: str = at.isoformat(timespec='seconds')

    # Randomly choose 1 or 3 labels to generate measurements for
    num_measures: int = random.choice([1, 3])
    chosen_labels: List[str] = random.sample(LABELS, num_measures)

    measurements: List[Dict[str, Any]] = [
        {
            "label": label,
            "value": MEASUREMENT_RANGES[label]()
        }
        for label in chosen_labels
    ]

    # Build and return the complete payload
    payload: Dict[str, Any] = {
        'at': at_str,
        'datalogger': datalogger_id,
        'location': location,
        'measurements': measurements
    }

    return payload

def aggregate(measurements : List[Measurement], span: str) -> List[Dict[str, Any]]:
    
        aggregation = defaultdict(list)
        
        for m in measurements:
                label = m.label
                naive_dt = make_naive(m.at)
                
                if span == 'hour':
                    time_slot = naive_dt.replace(minute=0, second=0, microsecond=0)
                elif span == 'day':
                    time_slot = naive_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                else:
                    raise ValueError(f"Unsupported span value: {span}")
                
                aggregation[(label, time_slot)].append(m.value)

        expected = []
        for (label, time_slot), values in aggregation.items():
            if label == "rain":
                value = sum(values)
            else:
                value = sum(values) / len(values)
            expected.append({
                'label': label,
                'time_slot': time_slot.isoformat(),
                'value': value
            })
            
        return expected