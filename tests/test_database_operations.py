import unittest
from unittest.mock import MagicMock, patch
import time

from database_operations import save_sensor_values_to_database, get_sensor_data_averages, get_sensorstation_thresholds, update_sensorstation, get_sensorstation_aggregation_period

SENSORSTATION_ID = 1
AGGREGATION_PERIOD = 300
MOCK_VALUES_TUPLE = (10,20,30,40,50,60)
MOCK_THRESHOLDS_TUPLE = (100,100,100,100,100,100,0,0,0,0,0,0)

class TestDatabaseOperations(unittest.TestCase):

    @patch('database_operations.db_conn')
    def test_save_sensor_values_to_database(self, db_conn):
        # Call the function with test input
        save_sensor_values_to_database(SENSORSTATION_ID, MOCK_VALUES_TUPLE[0], MOCK_VALUES_TUPLE[1], MOCK_VALUES_TUPLE[2], MOCK_VALUES_TUPLE[3], MOCK_VALUES_TUPLE[4], MOCK_VALUES_TUPLE[5])

        # Assert that the mock database connection was called with the correct SQL query and parameters
        db_conn.execute.assert_called_once_with('INSERT INTO sensordata (ssID, temperature, humidity, air_pressure, illuminance, air_quality_index, soil_moisture, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                        (SENSORSTATION_ID, MOCK_VALUES_TUPLE[0], MOCK_VALUES_TUPLE[1], MOCK_VALUES_TUPLE[2], MOCK_VALUES_TUPLE[3], MOCK_VALUES_TUPLE[4], MOCK_VALUES_TUPLE[5], int(time.time())))
        db_conn.commit.assert_called_once()

    # Test get_sensor_data_averages function
    @patch('database_operations.db_conn')
    def test_get_sensor_data_averages(self, db_conn):
        cursor = MagicMock()
        db_conn.cursor.return_value = cursor
        cursor.fetchone.return_value = MOCK_VALUES_TUPLE

        # Define the expected results
        expected_results = {
            'temperature': MOCK_VALUES_TUPLE[0] / 100,
            'humidity': MOCK_VALUES_TUPLE[1] / 100,
            'airPressure': MOCK_VALUES_TUPLE[2] / 1000,
            'lightIntensity': MOCK_VALUES_TUPLE[3],
            'airQuality': MOCK_VALUES_TUPLE[4],
            'soilMoisture': MOCK_VALUES_TUPLE[5]
        }
        # Call the function with the mocked parameters
        result = get_sensor_data_averages(SENSORSTATION_ID)

        # Check the results against the expected results
        self.assertEqual(result, expected_results)

    @patch('database_operations.db_conn')
    def test_get_sensorstation_aggregation_period(self, db_conn):
        cursor = MagicMock()
        db_conn.cursor.return_value = cursor
        cursor.fetchone.return_value = (AGGREGATION_PERIOD,)
       
        # Call the function with a mock sensorstation_id
        transmission_interval = get_sensorstation_aggregation_period(SENSORSTATION_ID)
        # Check that the function returned the expected value
        self.assertEqual(transmission_interval, AGGREGATION_PERIOD)

    # Test get_sensor_data_thresholds function
    @patch('database_operations.db_conn')
    def test_get_sensor_data_thresholds(self, db_conn):
        # Mock the database connection and cursor and the query
        cursor = MagicMock()
        db_conn.cursor.return_value = cursor
        cursor.fetchone.return_value = MOCK_THRESHOLDS_TUPLE

        # Define the expected results
        expected_results = {
            'temperature_max': MOCK_THRESHOLDS_TUPLE[0],
            'humidity_max': MOCK_THRESHOLDS_TUPLE[1],
            'airPressure_max': MOCK_THRESHOLDS_TUPLE[2],
            'lightIntensity_max': MOCK_THRESHOLDS_TUPLE[3],
            'airQuality_max': MOCK_THRESHOLDS_TUPLE[4],
            'soilMoisture_max': MOCK_THRESHOLDS_TUPLE[5],
            'temperature_min': MOCK_THRESHOLDS_TUPLE[6],
            'humidity_min': MOCK_THRESHOLDS_TUPLE[7],
            'airPressure_min': MOCK_THRESHOLDS_TUPLE[8],
            'lightIntensity_min': MOCK_THRESHOLDS_TUPLE[9],
            'airQuality_min': MOCK_THRESHOLDS_TUPLE[10],
            'soilMoisture_min': MOCK_THRESHOLDS_TUPLE[11]
        }

        # Call the function with the mocked parameters
        result = get_sensorstation_thresholds(SENSORSTATION_ID)

        # Check the results against the expected results
        self.assertEqual(result, expected_results)

    @patch('database_operations.db_conn')
    def test_update_sensorstation(self, db_conn):
        #set up json which is received 
        json_data = {
            'ssID': SENSORSTATION_ID,
            'status': 'OK',
            'gardeners':[
                'user1',
                'user2'
            ],
            'aggregationPeriod': AGGREGATION_PERIOD,
            'accessPoint': 'AccessPoint1',
            'lowerBound': {
                'airPressure': MOCK_THRESHOLDS_TUPLE[11],
                'airQuality': MOCK_THRESHOLDS_TUPLE[10],
                'humidity': MOCK_THRESHOLDS_TUPLE[9],
                'lightIntensity': MOCK_THRESHOLDS_TUPLE[8],
                'soilMoisture': MOCK_THRESHOLDS_TUPLE[7],
                'temperature': MOCK_THRESHOLDS_TUPLE[6]
            },
            'upperBound': {
                'airPressure': MOCK_THRESHOLDS_TUPLE[5],  
                'airQuality': MOCK_THRESHOLDS_TUPLE[4],
                'humidity': MOCK_THRESHOLDS_TUPLE[3],
                'lightIntensity': MOCK_THRESHOLDS_TUPLE[2],
                'soilMoisture': MOCK_THRESHOLDS_TUPLE[1],
                'temperature': MOCK_THRESHOLDS_TUPLE[0]
            }
        } 
        update_sensorstation(json_data)

        # check if the data is inserted correctly
        # (the indentation of the SQL string is important, don't change it)
        db_conn.execute.assert_called_once_with(
        '''INSERT OR REPLACE INTO sensorstations
        (ssID, aggregation_period,
        temperature_max, humidity_max, airPressure_max, lightIntensity_max,
        airQuality_max, soilMoisture_max,
        temperature_min, humidity_min, airPressure_min, lightIntensity_min,
        airQuality_min, soilMoisture_min)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (SENSORSTATION_ID, AGGREGATION_PERIOD, MOCK_THRESHOLDS_TUPLE[0], MOCK_THRESHOLDS_TUPLE[1], 
        MOCK_THRESHOLDS_TUPLE[2], MOCK_THRESHOLDS_TUPLE[3], MOCK_THRESHOLDS_TUPLE[4], MOCK_THRESHOLDS_TUPLE[5], 
        MOCK_THRESHOLDS_TUPLE[6], MOCK_THRESHOLDS_TUPLE[7], MOCK_THRESHOLDS_TUPLE[8], MOCK_THRESHOLDS_TUPLE[9], 
        MOCK_THRESHOLDS_TUPLE[10], MOCK_THRESHOLDS_TUPLE[11]))
