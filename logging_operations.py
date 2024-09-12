import logging
import datetime
import asyncio
from common import access_point_name
import rest_operations

SENDING_INTERVAL = 60

## Configure logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
# log to file
file_handler = logging.FileHandler('audit.log')
file_handler.setFormatter(log_formatter)
root_logger.addHandler(file_handler)
# log to stderr
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

class BleakLogFilter(logging.Filter):
    def filter(self, rec):
        return 'bleak' not in rec.name and 'asyncio' not in rec.name
log_filter = BleakLogFilter()
root_logger.addFilter(log_filter)
file_handler.addFilter(log_filter)
console_handler.addFilter(log_filter)


log_data = []

def log_local(level, message):
    logging.log(getattr(logging, level), message)

def log_local_and_remote(level, message, entity_type='ACCESS_POINT', entity_id=access_point_name):
    timestamp = datetime.datetime.utcnow().isoformat()

    log_entry = {
        'timestamp': timestamp+'Z',  # For backend reasons
        'level': level,
        'message': message,
        'origin': {
            'type': entity_type,        # 'ACCESS_POINT'/'SENSOR_STATION'
            'id': entity_id             # access_point_name or sensor_station.ssID
        }
    }

    log_local(level, message)

    log_data.append(log_entry)

def clear_log_data():
    global log_data
    log_data.clear()

async def log_sending_loop(session, connection_request):
    while not connection_request.done():
        await asyncio.sleep(SENDING_INTERVAL)
        await rest_operations.send_logs(session, log_data)
