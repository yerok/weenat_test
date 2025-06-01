import uuid
from typing import Any
from django.db.models import Model

class UUIDModel(Model):
    id: uuid.UUID

class Datalogger(UUIDModel):
    lat: float
    lng: float

class Measurement(Model):
    label: str
    at: Any  # idéalement datetime.datetime, mais Django utilise ses propres objets DateTimeField
    value: float
    datalogger: Datalogger