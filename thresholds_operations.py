import common
from bleak import BleakError
import database_operations
from rest_operations import send_warning_to_backend, clear_warning_on_backend
import asyncio
from logging_operations import log_local_and_remote

async def check_values_for_thresholds(sensorstation_client, sensorstation_id, session):
    try:
        thresholds_dict = database_operations.get_sensorstation_thresholds(sensorstation_id)
        averages_dict = database_operations.get_sensor_data_averages(sensorstation_id)

        if thresholds_dict is None:
            raise ValueError('Received None value for thresholds.')
        if averages_dict is None:
            raise ValueError('Received None value for averages.')

        for sensor, average_value in averages_dict.items():
            max_threshold = thresholds_dict.get(sensor+'_max')
            min_threshold = thresholds_dict.get(sensor+'_min')

            should_warn = False
            if min_threshold is not None and average_value < min_threshold:
                should_warn = True
            if max_threshold is not None and average_value > max_threshold:
                should_warn = True

            if should_warn:
                await send_warning_to_sensorstation(sensorstation_client, sensorstation_id, sensor, session)
                await send_warning_to_backend(sensorstation_id, session)
    except Exception as e:
        log_local_and_remote('WARN', f'Error in threshold check for station {sensorstation_id}: {e}', entity_type='SENSOR_STATION', entity_id=str(sensorstation_id))
        
                        
async def send_warning_to_sensorstation(sensorstation_client, sensorstation_id, sensor, session):
    error_code = 1
    error_code_byte_array = error_code.to_bytes(1, byteorder='little')
    try:
        sensor_uuid = common.failure_uuids[sensor]
        await sensorstation_client.write_gatt_char(sensor_uuid, error_code_byte_array)
        log_local_and_remote('DEBUG', f'Set warning for {sensor} on station {sensorstation_id}', entity_type='SENSOR_STATION', entity_id=str(sensorstation_id))
        
        # clear warning if characteristic value was updated to 0
        await sensorstation_client.start_notify(
            common.warning_active_uuid,
            lambda _, data: 
                asyncio.create_task(clear_warning_on_backend(sensorstation_id, session))
                    if int.from_bytes(data, 'little', signed=False) == 0
                    else False
        )
    except BleakError as e:
        log_local_and_remote('ERROR', f'Failed to set warning for {sensor} on station {sensorstation_id}: {e}', entity_type='SENSOR_STATION', entity_id=str(sensorstation_id))
           
