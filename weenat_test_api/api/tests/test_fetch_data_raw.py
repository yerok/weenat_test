from datetime import timedelta
from uuid import uuid4
from django.urls import reverse
from django.utils.timezone import now
from django.core.management import call_command

from rest_framework.test import APITestCase

from api.models import Datalogger, Measurement
from api.tests.old_test_ingest import print_json


class FetchDataRawTest(APITestCase):

    url: str
    datalogger: Datalogger
    measurements: Measurement

    # we need to populate db first to test this endpoint
    @classmethod
    def setUpTestData(cls) -> None:
        """
        we need to populate db first to test this endpoint
        Here we create 3 datalogger with 10 measurements each
        """
        cls.url = reverse('api_records')
        call_command('populate_db', dataloggers=3, measurements=10)
        cls.datalogger = Datalogger.objects.first()
        cls.measurements = list(Measurement.objects.order_by('at'))

        assert cls.datalogger is not None
        
    def test_returns_all_data_without_filters(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 30) 

    def test_filter_by_datalogger(self) -> None:
        response = self.client.get(self.url, {'datalogger': str(self.datalogger.id)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 10)

    def test_filter_by_date_range(self) -> None:
        
        # We arbitrarily pick 2 values representing the time range we will be testing
        # They are sorted by time so we know how many values we should have
        since = self.measurements[8].at.isoformat()
        before = self.measurements[22].at.isoformat()
        
        nbr_expected_values = 15
        
        response = self.client.get(self.url, {'since': since, 'before': before})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), nbr_expected_values)

    def test_invalid_date_filter(self) -> None:
        response = self.client.get(self.url, {'since': 'not-a-date'})
        self.assertEqual(response.status_code, 400)