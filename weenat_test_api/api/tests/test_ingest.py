from datetime import timedelta
from django.urls import reverse
from django.utils.timezone import now

from rest_framework.test import APITestCase

from api.models import Measurement
from .test_utils import generate_random_payload


class IngestEndPointTest(APITestCase):

    url = reverse('api_ingest_data')

    def test_ingest_valid_data(self):

        for _ in range(10):
            Measurement.objects.all().delete() 
            payload = generate_random_payload()
            response = self.client.post(self.url, payload, format='json')

            datalogger_id = payload['datalogger']
            expected_data = sorted(
                payload['measurements'], key=lambda m: m['label'])
            expected_data_count = len(expected_data)

            self.assertEqual(response.status_code, 201)
            measurements = Measurement.objects.filter(
                datalogger=datalogger_id).order_by('label')
            self.assertEqual(measurements.count(), expected_data_count)

            for measurement, expected in zip(measurements, expected_data):
                self.assertEqual(measurement.label, expected['label'])
                self.assertAlmostEqual(
                    measurement.value, expected['value'], places=2)

    def test_ingest_invalid_label(self):
        payload = generate_random_payload()
        payload["measurements"][0]["label"] = "invalid_label"
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ingest_invalid_temp_value(self):
        payload = generate_random_payload()
        payload["measurements"][0] = {"label": "temp", "value": 60.52}  
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ingest_invalid_temp_step(self):
        payload = generate_random_payload()
        payload["measurements"] = [{"label": "temp", "value": 10.5234}]  
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ingest_invalid_hum_value(self):
        payload = generate_random_payload()
        payload["measurements"] = [{"label": "hum", "value": 240.52}]  
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ingest_invalid_hum_step(self):
        payload = generate_random_payload()
        payload["measurements"][0] = {"label": "hum", "value": 40.3443}  
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ingest_invalid_rain_value(self):
        payload = generate_random_payload()
        payload["measurements"] = [{"label": "rain", "value": 23}]  
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ingest_invalid_rain_step(self):
        payload = generate_random_payload()
        payload["measurements"] = [{"label": "rain", "value": 0.1}]  
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ingest_invalid_datetime_format(self):

        payload = generate_random_payload()
        payload['at'] = '2021/01/02 05:46:22'  # Not ISO-8601
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ingest_invalid_lat_lng(self):

        payload = generate_random_payload()

        payload['location']['lat'] = 120.0  
        payload['location']['lng'] = -200.0  

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ingest_future_datetime(self):
        payload = generate_random_payload()
        payload['at'] = (now() + timedelta(days=1) 
                         ).isoformat(timespec='seconds')
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ingest_missing_required_field(self):
        payload = generate_random_payload()
        del payload['at'] 
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ingest_empty_measurements(self):
        payload = generate_random_payload()
        payload['measurements'] = []

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ingest_wrong_uuid(self):
        payload = generate_random_payload()
        payload['datalogger'] = 4
        
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)
