import sqlite3

db_conn = sqlite3.connect('sensorstations.db')

# create necessary tables on initialization
# triple quotation mark for multi line strings in python
db_conn.execute('''CREATE TABLE IF NOT EXISTS sensorstations
             (ssID INTEGER PRIMARY KEY UNIQUE,
              aggregation_period INTEGER,
              temperature_max REAL,
              humidity_max REAL,
              airPressure_max REAL,
              lightIntensity_max REAL,
              airQuality_max REAL,
              soilMoisture_max REAL,
              temperature_min REAL,
              humidity_min REAL,
              airPressure_min REAL,
              lightIntensity_min REAL,
              airQuality_min REAL,
              soilMoisture_min REAL)''')

db_conn.execute('''CREATE TABLE IF NOT EXISTS sensordata
             (ssID INTEGER,
              temperature REAL,
              humidity REAL,
              air_pressure REAL,
              illuminance REAL,
              air_quality_index REAL,
              soil_moisture REAL,
              timestamp INTEGER)''')
