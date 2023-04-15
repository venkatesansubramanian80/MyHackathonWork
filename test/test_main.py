import unittest
from unittest.mock import patch, Mock
import urllib.request
import subprocess
import os
from main import financial_strength_retreival

class MainTestCase(unittest.TestCase):

    influx_frendly_data = lambda measurement_name, time_value, field_values, tag_values: {
        "measurement": measurement_name,
        "time": time_value,
        "fields": field_values,
        "tags": tag_values
    }
    @patch('requests.get')
    def test_financial_strength_retreival(self, mock_get):
        os.environ['Fin_Stren_Provider'] = ''
        os.environ['Fin_BalSheet_Function'] = ''
        os.environ['Fin_BalSheet_Provider'] = ''
        os.environ['Fin_Stren_Table'] = ''

        mock_data1 = {}
        mock_data2 = {}

        mock_response1 = Mock()
        mock_response1.content = mock_data1
        mock_response1.status_code = 200

        mock_response2 = Mock()
        mock_response2.content = mock_data2
        mock_response2.status_code = 200
        mock_get.side_effect = [mock_response1, mock_response2]

        expected_response = {}
        financial_strength_results = financial_strength_retreival('Test_Symbol', self.influx_frendly_data, 'api_key', 'function', 'current_date')
        self.assertEquals(financial_strength_results, expected_response)