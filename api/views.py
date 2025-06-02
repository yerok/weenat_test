from typing import Any
from uuid import UUID

from django.db.models import Avg, QuerySet, Sum
from django.db.models.functions import TruncDay, TruncHour
from django.db.models.functions.datetime import TruncBase
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Datalogger, Measurement
from .serializers import (
    DataQueryParamsSerializer,
    DataRecordAggregateResponseSerializer,
    DataRecordRequestSerializer,
    DataRecordResponseSerializer,
    SummaryQueryParamsSerializer,
)


def get_datalogger_or_404(datalogger_id: UUID) -> Datalogger:
    try:
        return Datalogger.objects.get(id=datalogger_id)
    except Datalogger.DoesNotExist as err:
        raise NotFound(detail=f"Datalogger with id {datalogger_id} not found.") from err


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
    """

    serializer_class = DataRecordResponseSerializer

    def get_queryset(self) -> QuerySet[Measurement]:
        serializer = DataQueryParamsSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        datalogger_id = params["datalogger"]
        if not Datalogger.objects.filter(id=datalogger_id).exists():
            raise NotFound(detail=f"Datalogger with id {datalogger_id} not found.")

        datalogger = get_datalogger_or_404(params["datalogger"])
        queryset = Measurement.objects.filter(datalogger=datalogger)

        if "since" in params:
            queryset = queryset.filter(at__gte=params["since"])
        if "before" in params:
            queryset = queryset.filter(at__lte=params["before"])

        return queryset


# custom view - we need to create our own filter and to serialize query params
class SummaryView(APIView):
    """
    This view implements the GET /api/summary endpoint to summarize measurement data over a time span.

    Supports optional filtering via 'since', 'before', and aggregation by 'span' ("hour" or "day").
    Aggregates using average for all labels except "rain", which is summed.
    """

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = SummaryQueryParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        datalogger = get_datalogger_or_404(params["datalogger"])

        measurements = Measurement.objects.filter(datalogger=datalogger)

        if "since" in params:
            measurements = measurements.filter(at__gte=params["since"])
        if "before" in params:
            measurements = measurements.filter(at__lte=params["before"])

        span = params.get("span")

        if not span:
            data_serializer = DataRecordResponseSerializer(measurements, many=True)
            return Response(data_serializer.data)

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
