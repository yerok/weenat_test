import uuid
from django.db import models

# class DataRecord(models.Model):
#     """
#     Represents a measurement record sent by a datalogger at a specific time and location.
#     """
#     # at = models.DateTimeField(help_text="Timestamp when the metric is recorded (ISO-8601 format).")
#     datalogger = models.ForeignKey(
#         Datalogger,
#         on_delete=models.CASCADE,
#         related_name='records',
#         help_text="The datalogger device which recorded this data.")
    
#     lat = models.FloatField(help_text="Latitude in float representation.")
#     lng = models.FloatField(help_text="Latitude in float representation.")
    
#     # def __str__(self):
#     #     return f"Record at {self.at} from {self.datalogger}"

class UUIDModel(models.Model):
    """
    Abstract base model that provides a UUID field.
    All models inheriting this get a unique UUID automatically.
    """
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)


    class Meta:
        abstract = True
        
class Datalogger(UUIDModel):
    """
    Represents a datalogger device identified by a UUID.
    """
    lat = models.FloatField(help_text="Latitude in float representation.")
    lng = models.FloatField(help_text="Latitude in float representation.")

    
    # def __str__(self):
    #     return str(self.id)


class Measurement(models.Model):
    """
    Represents a single measurement attached to a DataRecord.
    For example: temperature, humidity, rain.
    """
    
    LABEL_CHOICES = [
            ('temp', 'Temperature'),
            ('rain', 'Rain'),
            ('hum', 'Humidity'),
        ]
    
    label = models.CharField(max_length=20, choices= LABEL_CHOICES)
    at = models.DateTimeField(help_text="Timestamp when the metric is recorded (ISO-8601 format).")
    value = models.FloatField()
    datalogger = models.ForeignKey(Datalogger, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.label}: {self.value}"