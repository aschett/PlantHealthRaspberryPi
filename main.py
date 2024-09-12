import asyncio
import aiohttp
import time
from bleak import BleakClient, BleakError
import common
import database_operations
from thresholds_operations import check_values_for_thresholds
from sensorvalues_operations import read_sensorvalues
from sensorstation_operations import search_for_sensorstations
from logging_operations import log_local, log_local_and_remote, log_sending_loop
import rest_operations

RETRY_TIME = 10

# Currently active sensor station tasks
ss_tasks = {}
async def sensor_station_manager(connection_request, session):
    global ss_tasks
    while not connection_request.done():
        new_assigned_ss = await rest_operations.get_sensorstation_instructions(session)
        #This so the program wont crash if the Webserver is down and just keeps the last sensorstation instructions if down
        if new_assigned_ss is not None:
            assigned_ss = new_assigned_ss

        for ss_id in common.known_ss:
            if ss_id in assigned_ss:
                if ss_id in ss_tasks and ss_tasks[ss_id].done():
                    log_local_and_remote('DEBUG', f'sensor_station_manager - Restarting task for {ss_id}')
                    del ss_tasks[ss_id]
                if ss_id not in ss_tasks:
                    log_local_and_remote('INFO', f'sensor_station_manager - Starting task for sensor station {ss_id}')
                    ss_status = assigned_ss[ss_id]
                    task = asyncio.create_task(sensor_station_task(connection_request, session, ss_id,
                                                                   first_time=(ss_status == 'PAIRING')))
                    ss_tasks[ss_id] = task
            
            # cancel tasks for sensor stations not assigned to this AP, if present
            else:
                if cancel_ss_task(ss_id):
                    log_local_and_remote('INFO', f'sensor_station_manager - Stopped task for sensor station {ss_id}')

        log_local_and_remote('DEBUG', 'Finished SS Manager Loop')
        await asyncio.sleep(10)

async def sensor_station_task(connection_request, session, sensorstation_id, first_time):
    sensorstation_mac = common.known_ss[sensorstation_id]
    try:
        transmission_interval = common.polling_interval
        async with BleakClient(sensorstation_mac) as client:
            log_local_and_remote('INFO', f'Connected to sensor station {sensorstation_id}')
            await rest_operations.send_sensorstation_connection_status(session, sensorstation_id, 'OK')
            database_operations.initialize_sensorstation(sensorstation_id)
            asyncio.create_task(read_sensorvalues(client, sensorstation_id, connection_request))
            while not connection_request.done() and client.is_connected:
                transmission_interval = database_operations.get_sensorstation_aggregation_period(sensorstation_id)
                await asyncio.sleep(transmission_interval)
                await rest_operations.get_thresholds_update_db(sensorstation_id, session)
                await check_values_for_thresholds(client, sensorstation_id, session)
                await rest_operations.send_sensorvalues_to_backend(sensorstation_id, session)

    except BleakError as e:
        error_status = 'PAIRING_FAILED' if first_time else 'OFFLINE'
        if error_status == 'PAIRING_FAILED':
            log_local_and_remote('ERROR', f'Failed to pair with sensor station {sensorstation_id}', 'SENSOR_STATION', sensorstation_id)
        else:
            log_local_and_remote('WARN', f'Could not find sensor station {sensorstation_id}', 'SENSOR_STATION', sensorstation_id)

        await rest_operations.send_sensorstation_connection_status(session, sensorstation_id, error_status)
        cancel_ss_task(sensorstation_id)

    except asyncio.CancelledError as e:
        database_operations.clear_sensor_data(sensorstation_id)
        database_operations.delete_sensorstation(sensorstation_id)
        log_local_and_remote('DEBUG', f'sensor_station_task ({sensorstation_id}) - Cancelled and cleaned up')

    except Exception as e:
        log_local_and_remote('ERROR', f'sensor_station_task ({sensorstation_id}) - Unexpected {e.__class__.__name__}: {e}')

def cancel_ss_task(sensorstation_id):
    global ss_tasks
    if sensorstation_id in ss_tasks:
        try:
            ss_tasks[sensorstation_id].cancel()
            del ss_tasks[sensorstation_id]
            return True
        except Exception:
            log_local_and_remote('DEBUG', f'Failed to cancel task for station {sensorstation_id}')
    
    return False


status = None
async def polling_loop(connection_request, session):
    global status
    asyncio.create_task(log_sending_loop(session, connection_request))
    while not connection_request.done():
        new_status = await rest_operations.get_ap_status(session)
        if new_status is not None and new_status != status:
            if new_status == 'SEARCHING':
                log_local_and_remote('INFO', 'Started search for sensor stations')
            if status == 'SEARCHING':
                log_local_and_remote('INFO', 'Stopped search for sensor stations')
            status = new_status

        log_local_and_remote('DEBUG', f'polling_loop - Current AP status is {status}')
        if status == 'OFFLINE':
            connection_request.set_result('Done')
        elif status == 'SEARCHING':
            sensorstations = await search_for_sensorstations()
            await rest_operations.send_sensorstations_to_backend(session, sensorstations)
        await asyncio.sleep(10)

async def main():
    while True:
        try:
            async with aiohttp.ClientSession(base_url=common.web_server_address, raise_for_status=True) as session:
                connection_request = asyncio.Future()
                await rest_operations.initialize_accesspoint(session)

                polling_loop_task = asyncio.create_task(polling_loop(connection_request, session))
                sensor_station_manager_task = asyncio.create_task(sensor_station_manager(connection_request, session))
                await asyncio.gather(polling_loop_task, sensor_station_manager_task)
                
        except aiohttp.ClientConnectionError as e:
            connection_request.set_result('Done')
            log_local('ERROR', f'Could not reach PlantHealth server. Retrying in {RETRY_TIME} seconds')
            await asyncio.sleep(RETRY_TIME)
            
        except aiohttp.ClientResponseError as e:
            log_local('WARN', f'Unauthorized to talk to PlantHealth server. Retrying in {RETRY_TIME} seconds.')
            await asyncio.sleep(RETRY_TIME)

        except Exception as e:
            log_local_and_remote('ERROR', f'Unexpected {e.__class__.__name__} occured in main: {e}')
            await asyncio.sleep(RETRY_TIME)

if __name__ == '__main__':
    asyncio.run(main())
