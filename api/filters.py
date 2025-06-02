from django_filters import rest_framework as filters

from .models import Measurement


class MeasurementFilter(filters.FilterSet):
    """
    FilterSet for filtering raw Measurement data based on date range
    and datalogger UUID.

    This filter is used exclusively by the '/api/data' endpoint

    It leverages django_filters library to provide these filtering capabilities.
    """

    since = filters.IsoDateTimeFilter(field_name="at", lookup_expr="gte")
    before = filters.IsoDateTimeFilter(field_name="at", lookup_expr="lte")
    datalogger = filters.UUIDFilter(field_name="datalogger__id")

    class Meta:
        model = Measurement
        fields = ["since", "before", "datalogger"]
