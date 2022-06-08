import requests
import json

data = {'data': 'hello brosdfdsfds'}
r = requests.post('http://127.0.0.1:8000/set_data', data=json.dumps(data))

print(r.text)