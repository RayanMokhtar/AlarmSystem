import requests
from uuid import uuid4
from datetime import date, datetime

url = "http://127.0.0.1:8000/chercher_notification/401eb00d-20a3-43c0-9c79-07c82b13d6b4"
response = requests.get(url)

print(response.status_code)
print(response.json())