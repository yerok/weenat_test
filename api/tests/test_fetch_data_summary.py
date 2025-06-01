from typing import Optional
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APITestCase

from api.models import Datalogger, Measurement
from api.tests.test_utils import aggregate


class FetchDataSummaryTest(APITestCase):
    url: str
    datalogger: Datalogger
    measurements: list

    @classmethod
    def setUpTestData(cls) -> None:
        """
        we need to populate db first to test this endpoint
        Here we create 1 datalogger with 50 measurements
        """
        cls.url = reverse("api_fetch_data_aggregates")
        call_command("populate_db", dataloggers=1, measurements=50)
        datalogger = Datalogger.objects.first()
        
        if datalogger is None:
            raise RuntimeError("populate_db n'a pas créé de Datalogger, arrêt des tests.")
        cls.datalogger = datalogger
        cls.measurements = list(
            Measurement.objects.filter(datalogger=cls.datalogger).order_by("at")
        )

    def test_summary_filter_without_datalogger(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)

    def test_summary_filter_by_datalogger(self) -> None:
        response = self.client.get(self.url, {"datalogger": str(self.datalogger.id)})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 50)

    def test_summary_filter_by_date_range(self) -> None:
        # We arbitrarily pick 2 values representing the time range we will be testing
        # They are sorted by time so we know how many values we should have
        since = self.measurements[20].at.isoformat()
        before = self.measurements[40].at.isoformat()

        expected = [m for m in self.measurements if since <= m.at.isoformat() <= before]
        response = self.client.get(
            self.url,
            {"since": since, "before": before, "datalogger": str(self.datalogger.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(expected))

    def test_summary_invalid_span(self) -> None:
        response = self.client.get(
            self.url, {"datalogger": str(self.datalogger.id), "span": "minute"}
        )
        self.assertEqual(response.status_code, 400)

    def test_summary_response_structure(self) -> None:
        response = self.client.get(
            self.url, {"datalogger": str(self.datalogger.id), "span": "hour"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

        first = response.data[0]
        self.assertIn("label", first)
        self.assertIn("time_slot", first)
        self.assertIn("value", first)

    def test_summary_hourly_aggregation(self) -> None:
        response = self.client.get(
            self.url, {"datalogger": str(self.datalogger.id), "span": "hour"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

        expected = aggregate(self.measurements, "hour")

        for expected_item in expected:
            found = False
            for record in response.data:
                if (
                    record["label"] == expected_item["label"]
                    # ignore tz
                    and record["time_slot"].startswith(expected_item["time_slot"])
                    # float tolerance
                    and abs(record["value"] - expected_item["value"]) < 0.0001
                ):
                    found = True
                    break

            self.assertTrue(found, f"Item not found in response: {expected_item}")

    def test_summary_daily_aggregation(self) -> None:
        response = self.client.get(
            self.url, {"datalogger": str(self.datalogger.id), "span": "day"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

        expected = aggregate(self.measurements, "day")

        for expected_item in expected:
            found = False
            for record in response.data:
                if (
                    record["label"] == expected_item["label"]
                    # ignore tz
                    and record["time_slot"].startswith(expected_item["time_slot"])
                    # float tolerance
                    and abs(record["value"] - expected_item["value"]) < 0.0001
                ):
                    found = True
                    break

            self.assertTrue(found, f"Item not found in response: {expected_item}")
