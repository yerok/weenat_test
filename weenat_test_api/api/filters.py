from django_filters import rest_framework as filters
from .models import Measurement


class MeasurementFilter(filters.FilterSet):

    since = filters.IsoDateTimeFilter(field_name="at", lookup_expr="gte")
    before = filters.IsoDateTimeFilter(field_name="at", lookup_expr="lte")
    datalogger = filters.UUIDFilter(field_name="datalogger__id")
    

    class Meta:
        model = Measurement
        fields = ['since', 'before', 'datalogger']