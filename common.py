import yaml
import os

sensor_station_name = 'PH SensorStation'

# global constants taken out of the BLE Communication Spec
base_uuid = '0000{}-0000-1000-8000-00805f9b34fb'
device_information_uuid = base_uuid.format('180a')

air_pressure_uuid = base_uuid.format('2a6d')
temperature_uuid = base_uuid.format('2a6e')
humidity_uuid = base_uuid.format('2a6f')
illuminance_uuid = base_uuid.format('2afb')
air_quality_index_uuid = base_uuid.format('f105')
soil_moisture_uuid = base_uuid.format('f106')

# global constants for the error messages taken out of the ble communication Spec
error_service_uuid = base_uuid.format('ff00')
air_pressure_failure_uuid = base_uuid.format('ff01')
temperature_failure_uuid = base_uuid.format('ff02')
humidity_failure_uuid = base_uuid.format('ff03')
illuminance_failure_uuid = base_uuid.format('ff04')
air_quality_index_failure_uuid = base_uuid.format('ff05')
soil_moisture_failure_uuid = base_uuid.format('ff06')
warning_active_uuid = base_uuid.format('ff80')

#global dictionary failure_uuids
failure_uuids = {
    'airPressure': air_pressure_failure_uuid,
    'temperature': temperature_failure_uuid,
    'humidity': humidity_failure_uuid,
    'lightIntensity': illuminance_failure_uuid,
    'airQuality': air_quality_index_failure_uuid,
    'soilMoisture': soil_moisture_failure_uuid
}

known_ss_filename = 'known_sensorstations.yaml'
def load_known_ss():
    try:
        with open (known_ss_filename, 'r') as file:
            known_ss = yaml.safe_load(file)    
    except FileNotFoundError:
        with open (known_ss_filename, 'w') as file:
            known_ss = {}
            yaml.dump(known_ss, file)
    return known_ss

def save_known_ss():
    with open (known_ss_filename, 'w') as file:
        yaml.dump(known_ss, file)

#The decision to saves this in variables comes from the fact that it seemed kind of overkill to save at max 8 things in a sensorstation with only 2 values
#This variable exists to keep track of all the sensorstations ever found and their MAC-addresses
known_ss = load_known_ss()

# in seconds
polling_interval = 30

# Values taken from config.yaml file 
try:
    with open('conf.yaml', 'r') as f:
        config = yaml.safe_load(f)
        web_server_address = config['web_server_address']
        access_point_name = config['access_point_name']
        default_aggregation_period = config['default_transmission_interval']

except FileNotFoundError:
    print('conf.yaml not found, proceeding with default configuration.')
    with open('conf.example.yaml', 'r') as f:
        config = yaml.safe_load(f)
        web_server_address = config['web_server_address']
        access_point_name = config['access_point_name']
        access_point_address = web_server_address + '/' + access_point_name
        default_aggregation_period = config['default_transmission_interval']

if not os.path.exists('audit.log'):
    open('audit.log', 'w').close()
