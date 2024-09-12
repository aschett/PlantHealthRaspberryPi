import unittest
from unittest.mock import AsyncMock, patch
import common

from sensorstation_operations import search_for_sensorstations

class TestSearchForSensorstations(unittest.IsolatedAsyncioTestCase):

    @patch('sensorstation_operations.BleakScanner')
    @patch('sensorstation_operations.common.known_ss')
    @patch('sensorstation_operations.common.save_known_ss')
    async def test_search_for_sensorstations(self, mock_save_known_ss, common_mock, BleakScanner):
        # Set up mock devices
        mock_device_1 = AsyncMock()
        mock_device_1.name = common.sensor_station_name + '1'
        mock_device_1.details = {
            'props': {
                'ServiceData': {
                    common.device_information_uuid: b'\x01'  # Station ID encoded as a single byte == 1
                }
            }
        }
        mock_device_1.address = 'mock_address_1'

        mock_device_2 = AsyncMock()
        mock_device_2.name = common.sensor_station_name + '2'
        mock_device_2.details = {
            'props': {
                'ServiceData': {
                    common.device_information_uuid: b'\x02'  # Station ID encoded as a single byte == 2
                }
            }
        }
        mock_device_2.address = 'mock_address_2'

        mock_device_3 = AsyncMock()
        mock_device_3.name = 'other_device'
        mock_device_3.details = {}  # Mocked empty details
        mock_device_3.address = 'mock_address_3'

        mock_devices = [mock_device_1, mock_device_2, mock_device_3]

        mock_scanner = AsyncMock()
        mock_scanner.stop = AsyncMock()
        mock_scanner.discover.return_value = mock_devices

        BleakScanner.return_value.__aenter__.return_value = mock_scanner

        # Call the function being tested
        sensorstations = await search_for_sensorstations()

        # Check that the mock discover method was called
        mock_scanner.discover.assert_awaited_once()

        # Check that the function returns the correct list of sensor stations
        expected_sensorstations = [
            int.from_bytes(mock_device_1.details['props']['ServiceData'][common.device_information_uuid],
                            byteorder='little', signed=False),
            int.from_bytes(mock_device_2.details['props']['ServiceData'][common.device_information_uuid],
                            byteorder='little', signed=False)
        ]
        self.assertEqual(sensorstations, expected_sensorstations)


if __name__ == '__main__':
    unittest.main()
