from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from django.utils.timezone import now
from rest_framework import serializers

from .models import Datalogger, Measurement


class LocationSerializer(serializers.Serializer[Any]):
    lat = serializers.FloatField()
    lng = serializers.FloatField()

    def validate_lat(self, value: float) -> float:
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_lng(self, value: float) -> float:
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value


class MeasurementSerializer(serializers.Serializer[Any]):
    measurement_label = serializers.ChoiceField(choices=[c[0] for c in Measurement.LABEL_CHOICES])
    value = serializers.FloatField()

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
    # def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        label = attrs["label"]
        value = attrs["value"]

        if label == "temp":
            if not (-20 <= value <= 40):
                raise serializers.ValidationError(
                    {"value": "Temperature must be between -20 and 40."}
                )
            if round((value * 10) % 1, 5) != 0:
                raise serializers.ValidationError(
                    {"value": "Temperature must be in steps of 0.1."}
                )

        elif label == "hum":
            if not (20 <= value <= 100):
                raise serializers.ValidationError(
                    {"value": "Humidity must be between 20 and 100."}
                )
            if round((value * 10) % 1, 5) != 0:
                raise serializers.ValidationError(
                    {"value": "Humidity must be in steps of 0.1."}
                )

        elif label == "rain":
            if not (0 <= value <= 2):
                raise serializers.ValidationError(
                    {"value": "Rain must be between 0 and 2."}
                )
            if round((value * 5) % 1, 5) != 0:
                raise serializers.ValidationError(
                    {"value": "Rain must be in steps of 0.2."}
                )

        return attrs


class DataRecordRequestSerializer(serializers.Serializer[Any]):
    datalogger = serializers.CharField()
    location = LocationSerializer()
    measurements = MeasurementSerializer(many=True, required=True, allow_null=False)
    at = serializers.DateTimeField()

    # if we use serializers.UUIDField() it would convert an int for instane to an UUID,
    # we do not want that so we check that it's a correct uuid
    def validate_datalogger(self, value: str) -> str:
        try:
            return str(UUID(value))  # On vérifie que c'est bien une UUID
        except ValueError as err:
            raise serializers.ValidationError(
                "'datalogger' field must be a valid UUID."
            ) from err

    def validate_measurements(self, value: List[Measurement]) -> List[Measurement]:
        if not value:
            raise serializers.ValidationError("Measurements cannot be empty.")
        return value

    def validate_at(self, value: datetime) -> datetime:
        if value > now():
            raise serializers.ValidationError(
                "The 'at' datetime cannot be in the future."
            )
        return value

    def create(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        location_data = validated_data["location"]
        measurement_data = validated_data["measurements"]
        
        datalogger: Datalogger
        datalogger, _ = Datalogger.objects.get_or_create(
            defaults={
                "location_lat": location_data["lat"],
                "location_lng": location_data["lng"],
            }
        )

        measurement_instances : List[Measurement] = []
        for m in measurement_data:
            measurement = Measurement.objects.create(
                datalogger=datalogger, value=m["value"], at=m["at"]
            )
            measurement_instances.append(measurement)

        return {
            "datalogger": str(datalogger.id),
            "location": {
                "lat": datalogger.lat,
                # "lat": datalogger.location_lat,
                "lng": datalogger.lng,
                # "lng": datalogger.location_lng,
            },
            "measurements": measurement_data,
        }


class DataRecordResponseSerializer(serializers.ModelSerializer):
    measured_at = serializers.DateTimeField(source="at")

    class Meta: 
        model = Measurement
        fields = ["label", "measured_at", "value"]


class DataRecordAggregateResponseSerializer(serializers.Serializer): 
    label = serializers.CharField()
    time_slot = serializers.DateTimeField()
    value = serializers.FloatField()


# We need a serializer for /api/summary because the span is not handled natively with APIView / DRF / django_filters /
class SummaryQueryParamsSerializer(serializers.Serializer):
    since = serializers.DateTimeField(required=False)
    before = serializers.DateTimeField(required=False)
    datalogger = serializers.UUIDField(required=True)
    span = serializers.ChoiceField(choices=["day", "hour"], required=False)
