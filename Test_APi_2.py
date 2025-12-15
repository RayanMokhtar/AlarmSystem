import requests
from uuid import uuid4
from datetime import date, datetime

url = "http://127.0.0.1:8000/creerEvenement"  # créer un endpoint correspondant

evenement_id = str(uuid4())
appareil_id = "43c6cf82-a8ef-41d3-9cbc-104d12eb1be8" # ce UUID correspond a un appareil existant

data = {
    "evenement_id": evenement_id,
    "appareil_id": appareil_id,
    "date_evenement": str(date.today()),
    "statut_alerte": False,
    "timestamp_serveur": str(datetime.now()),
    "seuil_reponse_modele": 0.75,
    "timestamp_rasp": str(datetime.now()),
    "statut_camera": True,
    "statut_capteur": True,
    "emplacement_video_evenement": "/videos/test.mp4"
}

response = requests.post(url, json=data)
print("Status code:", response.status_code)
print("Response JSON:", response.json())
