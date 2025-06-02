from typing import List, Tuple
import uuid

from django.db import models


class UUIDModel(models.Model):
    """
    Abstract base model that provides a UUID field.
    All models inheriting this get a unique UUID automatically.
    """

    id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, primary_key=True
    )

    class Meta:
        abstract = True


class Datalogger(UUIDModel):
    """
    Represents a datalogger device identified by a UUID.
    """

    lat = models.FloatField(help_text="Latitude in float representation.")
    lng = models.FloatField(help_text="Longitude in float representation.")


class Measurement(models.Model):
    """
    Represents a single measurement attached to a datalogger.
    For example: temperature, humidity, rain.
    """

    LABEL_CHOICES: List[Tuple[str, str]] = [
        ("temp", "Temperature"),
        ("rain", "Rain"),
        ("hum", "Humidity"),
    ]

    label = models.CharField(max_length=20, choices=LABEL_CHOICES)
    at = models.DateTimeField(
        help_text="Timestamp when the metric is recorded (ISO-8601 format)."
    )
    value = models.FloatField()
    datalogger = models.ForeignKey(Datalogger, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.label}: {self.value}"
