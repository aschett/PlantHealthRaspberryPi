import requests

base_url = 'http://localhost:5000'

response = requests.post(f'{base_url}/access-points')
print(response.json())

response = requests.get(f'{base_url}/access-points/AP1')
print(response.json())

response = requests.get(f'{base_url}/sensor-stations/101')
print(response.json())

response = requests.get(f'{base_url}/access-points/AP1/sensor-stations')
print(response.json())

response = requests.post(f'{base_url}/sensor-stations/101', json=[{'ssID': '101', 'status': 'AVAILABLE'}])
print(response.json())

response = requests.put(f'{base_url}/sensor-stations/101', json=[{'ssID': '101', 'status': 'OFFLINE'}])
print(response.json())
