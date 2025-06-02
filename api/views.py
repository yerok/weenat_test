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
    """
    This view implements the POST /api/ingest endpoint to ingest new data records into the system.

    Accepts a payload validated by DataRecordRequestSerializer and saves
    the related measurements.
    """
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        request_serializer = DataRecordRequestSerializer(data=request.data)
        
        if not request_serializer.is_valid():
            return Response(
                request_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        result = request_serializer.save() 

        response_serializer = DataRecordResponseSerializer(
            result["measurements"], many=True
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    

# we use ListAPIView because we use directly the model - we can use django_filters
# no need to create custom filters or to serialize query params
class FetchRawDataView(ListAPIView):
    """
    This view implements the GET /api/data endpoint to fetch raw measurements filtered by query parameters.

    Uses DjangoFilterBackend and a MeasurementFilter to filter by datalogger and  date range
    """
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
    """
    This view implements the GET /api/summary endpoint to summarize measurement data over a time span.

    Supports optional filtering via 'since', 'before', and aggregation by 'span' ("hour" or "day").
    Aggregates using average for all labels except "rain", which is summed.
    """
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
            serializer = DataRecordResponseSerializer(measurements, many=True)
            return Response(serializer.data)

        if span not in ["day", "hour"]:
            return Response({"detail": "Invalid span value."}, status=400)

        trunc_func: TruncBase = TruncDay("at") if span == "day" else TruncHour("at")

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

