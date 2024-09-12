import common
import asyncio
import aiohttp
import json
import database_operations
import functools
from datetime import datetime
import logging_operations

sensorstation_html = '/api/sensor-stations/'
accesspoint_html = '/api/access-points/'

# This function makes it so that each rest call retries 5 times before raising an ClientConnectionError
def retry_connection_error(retries=5, interval=3):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    return await func(*args, **kwargs)
                except aiohttp.ClientConnectionError:
                    await asyncio.sleep(interval)
                    logging_operations.log_local('WARN', f'Retrying in {func.__name__}. Attempt {i+1} out of {retries}')
            raise aiohttp.ClientConnectionError(f'ClientConnectionError in function \'{func.__name__}\'')
        return wrapper  # Moved outside the for loop
    return decorator

@retry_connection_error(retries = 3, interval = 5)
async def initialize_accesspoint(session):
    data = {'name': common.access_point_name, 'serverAddress': common.web_server_address}
    try:
        async with session.post('/api/access-points', json=data) as response:
            json_data = await response.json()
            auth_token = json_data['token'] 
            session.headers.add('Authorization', f'Bearer {auth_token}')
            logging_operations.log_local_and_remote('INFO', f'Initialized access point for remote address: {common.web_server_address}')
    except aiohttp.ClientResponseError as e:
        if 'Authorization' in session.headers:
            session.headers.pop('Authorization')
        raise e

@retry_connection_error(retries = 3, interval = 5)
async def get_ap_status(session):
    async with session.get(accesspoint_html + common.access_point_name) as response:
        try:
            data = await response.json()
            status = data['status']
            logging_operations.log_local_and_remote('DEBUG', f'Retrieved access point status: {status}')
            return status
        except json.decoder.JSONDecodeError as e:
            logging_operations.log_local_and_remote('ERROR', f'Could not parse json in get_ap_status. Error: {e}')
            return None

@retry_connection_error(retries = 3, interval = 5)
async def get_sensorstation_instructions(session):
    paired_stations = {}
    async with session.get(accesspoint_html + common.access_point_name + '/sensor-stations') as response:
        try:
            json_data = await response.json()
            for station in json_data:
                ss_id = station['ssID']
                ss_status = station['status']
                if ss_status != 'AVAILABLE':
                    paired_stations[ss_id] = ss_status

        except json.decoder.JSONDecodeError as e:
            logging_operations.log_local_and_remote('ERROR', f'Could not parse json in get_sensorstation_instructions. Error: {e}')
            return paired_stations
        except KeyError as e:
            logging_operations.log_local_and_remote('ERROR', f'KeyError in get_sensorstation_instructions. Error: {e}')
            return paired_stations
    logging_operations.log_local_and_remote('DEBUG', f'Retrieved sensorstation instructions. SS: {paired_stations}')
    return paired_stations

@retry_connection_error(retries = 3, interval = 5)
async def send_sensorstations_to_backend(session, sensorstations):
    ss_avail = list(map(lambda id: { 'ssID': id, 'status': 'AVAILABLE' }, sensorstations))
    async with session.post(accesspoint_html + common.access_point_name + '/sensor-stations', json=ss_avail):
        logging_operations.log_local_and_remote('DEBUG', f'Available sensorstations sent to web server. Sensorstations: {ss_avail}')

@retry_connection_error(retries = 3, interval = 5)
async def send_sensorstation_connection_status(session, sensorstation_id, status):
    ss_status = {
        'ssID': sensorstation_id,
        'apName': common.access_point_name,
        'status': status
    }
    async with session.put(sensorstation_html + str(sensorstation_id), json=ss_status):
        logging_operations.log_local_and_remote('DEBUG', f'Set status for station {sensorstation_id} to {status}',entity_type='SENSOR_STATION', entity_id=str(sensorstation_id))

@retry_connection_error(retries = 3, interval = 5)
async def send_warning_to_backend(sensorstation_id, session):
    await send_sensorstation_connection_status(session, sensorstation_id, 'WARNING')

@retry_connection_error(retries = 3, interval = 5)
async def clear_warning_on_backend(sensorstation_id, session):
    await send_sensorstation_connection_status(session, sensorstation_id, 'OK')

@retry_connection_error(retries = 3, interval = 5)
async def get_thresholds_update_db(sensorstation_id, session):
    async with session.get(sensorstation_html + str(sensorstation_id)) as response:
        json_data = await response.json()
        database_operations.update_sensorstation(json_data)
        logging_operations.log_local_and_remote('DEBUG', f'Updated thresholds for sensorstation: {sensorstation_id}. Thresholds: {json_data}', entity_type='SENSOR_STATION', entity_id=str(sensorstation_id))

@retry_connection_error(retries = 3, interval = 5)
async def send_sensorvalues_to_backend(sensorstation_id, session):
    averages_dict = database_operations.get_sensor_data_averages(sensorstation_id)
    if averages_dict:
        averages_dict['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        async with session.post(sensorstation_html + str(sensorstation_id) + '/measurements', json=averages_dict):
            database_operations.clear_sensor_data(sensorstation_id)
            logging_operations.log_local_and_remote('DEBUG', f'Sent sensor values to web server for sensorstation: {sensorstation_id}. Values: {averages_dict}', entity_type='SENSOR_STATION', entity_id=str(sensorstation_id))
    else:
        logging_operations.log_local_and_remote('ERROR', f'Could not accumulate sensor values for sensorstation: {sensorstation_id}', entity_type='SENSOR_STATION', entity_id=str(sensorstation_id))

@retry_connection_error(retries = 3, interval = 5)
async def send_logs(session, logging_data):
    async with session.post(accesspoint_html + common.access_point_name + '/logs', json=logging_data):
        logging_operations.clear_log_data()
        logging_operations.log_local_and_remote('DEBUG', f'Sent logs to web server')
