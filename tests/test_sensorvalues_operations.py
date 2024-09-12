import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from sensorvalues_operations import read_sensorvalues

STATION_ID = 1

class TestReadSensorValue(unittest.IsolatedAsyncioTestCase):

    @patch('asyncio.sleep', return_value=None)
    @patch('database_operations.save_sensor_values_to_database')
    async def test_read_sensorvalues(self, save_sensor_values_to_database, sleep_mock):

        connection_request = MagicMock()
        BleakClient = AsyncMock()

        connection_request.done.side_effect = [False, True]
        BleakClient.is_connected.return_value = True

        # mock reading characteristic of BleakClient
        BleakClient.read_gatt_char.return_value=int(10).to_bytes(2,byteorder='little')

        # call function with mock client
        await read_sensorvalues(BleakClient, STATION_ID, connection_request)

        # assert that saveSensorValuesToDatabase was called once with the expected arguments
        save_sensor_values_to_database.assert_called_once_with(STATION_ID, 10, 10, 10, 10, 10, 10)
