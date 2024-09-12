import database_operations
from bleak import BleakError
import asyncio
import common
import logging_operations

READ_SENSOR_INTERVAL = 5

async def read_sensorvalues(client, sensorstation_id, connection_request):
    while not connection_request.done() and client.is_connected:
        try:
            temperature = int.from_bytes(await client.read_gatt_char(common.temperature_uuid), 'little', signed=False)
            humidity = int.from_bytes(await client.read_gatt_char(common.humidity_uuid), 'little', signed=False)
            air_pressure = int.from_bytes(await client.read_gatt_char(common.air_pressure_uuid), 'little', signed=False)
            illuminance = int.from_bytes(await client.read_gatt_char(common.illuminance_uuid), 'little', signed=False)
            air_quality_index = int.from_bytes(await client.read_gatt_char(common.air_quality_index_uuid), 'little', signed=False)
            soil_moisture = int.from_bytes(await client.read_gatt_char(common.soil_moisture_uuid), 'little', signed=False)        
            database_operations.save_sensor_values_to_database(sensorstation_id, temperature, humidity, air_pressure, illuminance, air_quality_index, soil_moisture)
            await asyncio.sleep(READ_SENSOR_INTERVAL)
        except BleakError as e:
            log_local_and_remote('ERROR', f'BleakError while retreiving sensorvalues from sensorstation: {sensorstation_id}. Error: {e}', entity_type='SENSOR_STATION', entity_id=str(sensorstation_id))
        
