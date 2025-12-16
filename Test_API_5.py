import requests
from uuid import uuid4
from datetime import date, datetime
from requests_toolbelt.multipart.encoder import MultipartEncoder
import json

url = "http://127.0.0.1:8000/creerEvenement"

evenement_dict = {
    "evenement_id": str(uuid4()),
    "appareil_id": "43c6cf82-a8ef-41d3-9cbc-104d12eb1be8",
    "date_evenement": str(date.today()),
    "statut_alerte": False,
    "timestamp_serveur": str(datetime.now()),
    "seuil_reponse_modele": 0.75,
    "timestamp_rasp": str(datetime.now()),
    "statut_camera": True,
    "statut_capteur": True,
    "emplacement_video_evenement": "/videos/test.mp4"
}

notif_dict = {
    "notification_id": str(uuid4()),
    "utilisateur_id": "401eb00d-20a3-43c0-9c79-07c82b13d6b4",
    "evenement_id": evenement_dict["evenement_id"],
    "statut_notification": True,
    "date_notification": str(date.today())
}

m = MultipartEncoder(
    fields={
        "evenement": json.dumps(evenement_dict),
        "notif": json.dumps(notif_dict),
        "video": ("video_test2.mp4", open("video_test.mp4", "rb"), "video/mp4")
    }
)

response = requests.post(url, data=m, headers={"Content-Type": m.content_type})

print(response.status_code)
try:
    print(response.json())
except Exception as e:
    print("Erreur JSON:", e, response.text)
