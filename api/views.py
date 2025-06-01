from typing import Any
from django.db.models import Avg, Sum, QuerySet
from django.db.models.functions import TruncDay, TruncHour
from django.db.models.functions.datetime import TruncBase
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.request import Request

from rest_framework.views import APIView

from api.filters import MeasurementFilter

from .models import Datalogger, Measurement
from .serializers import (
    DataRecordAggregateResponseSerializer,
    DataRecordRequestSerializer,
    DataRecordResponseSerializer,
    SummaryQueryParamsSerializer,
)

class IngestDataView(APIView):
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        request_serializer = DataRecordRequestSerializer(data=request.data)

        if not request_serializer.is_valid():
            return Response(
                request_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        # Appelle create() du serializer
        result = request_serializer.save()  # <== appelle .create(validated_data)

        response_serializer = DataRecordResponseSerializer(
            result["measurements"], many=True
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
# class IngestDataView(APIView):
#     def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
#         request_serializer = DataRecordRequestSerializer(data=request.data)

#         if not request_serializer.is_valid():
#             return Response(
#                 request_serializer.errors, status=status.HTTP_400_BAD_REQUEST
#             )

#         validated_data = request_serializer.validated_data
#         datalogger_id = validated_data["datalogger"]

#         measurements_data = validated_data["measurements"]
#         at = validated_data["at"]
#         location = validated_data["location"]

#         datalogger, _ = Datalogger.objects.get_or_create(
#             id=datalogger_id, lat=location["lat"], lng=location["lng"]
#         )

#         # Update location if needed
#         datalogger.lat = validated_data["location"]["lat"]
#         datalogger.lng = validated_data["location"]["lng"]
#         datalogger.save()

#         created_measurements = [
#             Measurement.objects.create(
#                 datalogger=datalogger, label=m["label"], value=m["value"], at=at
#             )
#             for m in measurements_data
#         ]

#         response_serializer = DataRecordResponseSerializer(
#             created_measurements, many=True
#         )
#         return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# we use ListAPIView because we use directly the model - we can use django_filters
# no need to create custom filters or to serialize query params
class FetchRawDataView(ListAPIView):
    queryset = Measurement.objects.all()
    serializer_class = DataRecordResponseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MeasurementFilter

    def get_queryset(self) -> QuerySet :
        datalogger_id = self.request.query_params.get("datalogger")
        if not datalogger_id:
            raise ValidationError({"datalogger": "This query parameter is required."})

        return Measurement.objects.filter(datalogger_id=datalogger_id)
    
# custom view - we need to create our own filter and to serialize query params
class SummaryView(APIView):
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        query_params_serializer = SummaryQueryParamsSerializer(
            data=request.query_params
        )

        if not query_params_serializer.is_valid():
            return Response(
                query_params_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = query_params_serializer.validated_data

        datalogger_id = validated_data["datalogger"]

        since = validated_data.get("since")
        before = validated_data.get("before")
        span = validated_data.get("span")

        if not datalogger_id:
            return Response({"detail": "datalogger parameter is required."}, status=400)

        try:
            datalogger = Datalogger.objects.get(id=datalogger_id)
        except Datalogger.DoesNotExist:
            return Response({"detail": "datalogger not found."}, status=404)

        measurements = Measurement.objects.filter(datalogger=datalogger)

        if since:
            measurements = measurements.filter(at__gte=since)
        if before:
            measurements = measurements.filter(at__lte=before)

        if not span:
            from .serializers import DataRecordResponseSerializer

            raw_serializer = DataRecordResponseSerializer(measurements, many=True)
            return Response(raw_serializer.data)



        elif span in ["day", "hour"]:
            trunc_func: TruncBase
            if span == "day":
                trunc_func = TruncDay("at")
            else:
                trunc_func = TruncHour("at")

            aggregation = []
            labels = measurements.values_list("label", flat=True).distinct()

            for label in labels:
                subset = measurements.filter(label=label)
                annotated = subset.annotate(time_slot=trunc_func).values("time_slot")

                if label == "rain":
                    aggregated_data = annotated.annotate(value=Sum("value"))
                else:
                    aggregated_data = annotated.annotate(value=Avg("value"))

                for item in aggregated_data:
                    aggregation.append(
                        {
                            "label": label,
                            "time_slot": item["time_slot"],
                            "value": item["value"],
                        }
                    )

            response_serializer = DataRecordAggregateResponseSerializer(
                aggregation, many=True
            )
            return Response(response_serializer.data)

        return Response({"Invalid span value"}, status=400)
