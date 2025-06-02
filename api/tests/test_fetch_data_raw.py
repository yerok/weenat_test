from datetime import datetime, timedelta
from typing import List, cast

from django.core.management import call_command
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase

from api.models import Datalogger, Measurement


class FetchDataRawTest(APITestCase):
    url: str
    datalogger: Datalogger
    measurements: List[Measurement]

    @classmethod
    def setUpTestData(cls) -> None:
        """
        we need to populate db first to test this endpoint
        Here we create 1 datalogger with 50 measurements
        """
        cls.url = reverse("api_fetch_data_raw")
        call_command("populate_db", dataloggers=1, measurements=50)
        datalogger = Datalogger.objects.first()

        if datalogger is None:
            raise RuntimeError(
                "populate_db n'a pas créé de Datalogger, arrêt des tests."
            )
        cls.datalogger = datalogger
        cls.measurements = list(
            Measurement.objects.filter(datalogger=cls.datalogger).order_by("at")
        )

    def test_filter_without_datalogger(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)

    def test_filter_by_datalogger(self) -> None:
        response = self.client.get(self.url, {"datalogger": str(self.datalogger.id)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 50)

    def test_filter_by_datalogger_and_date_range(self) -> None:
        # We arbitrarily pick 2 values representing the time range we will be testing
        # They are sorted by time so we know how many values we should have
        since = cast(datetime, self.measurements[8].at).isoformat()
        before = cast(datetime, self.measurements[22].at).isoformat()

        expected = []
        for m in self.measurements:
            at = cast(datetime, m.at).isoformat()

            # Pylance error because datalogguer_id doesn't exist yet, we do not ignore it because Mypy will tell us that's useless
            if since <= at <= before and m.datalogger_id == self.datalogger.id:
                expected.append(m)

        response = self.client.get(
            self.url,
            {"datalogger": str(self.datalogger.id), "since": since, "before": before},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(expected))

    def test_invalid_date_filter(self) -> None:
        response = self.client.get(
            self.url, {"datalogger": str(self.datalogger.id), "since": "not-a-date"}
        )
        self.assertEqual(response.status_code, 400)

    def test_filter_by_datalogger_and_date_range_with_no_matching_results(self) -> None:
        since = (now() + timedelta(days=30)).isoformat()
        before = (now() + timedelta(days=40)).isoformat()

        response = self.client.get(
            self.url,
            {"datalogger": str(self.datalogger.id), "since": since, "before": before},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_invalid_datalogger_uuid(self) -> None:
        response = self.client.get(
            self.url, {"datalogger": "00000000-0000-0000-0000-000000000000"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
