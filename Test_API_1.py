import requests
from uuid import uuid4
from datetime import date

url = "https://alarmsystem-hl0s.onrender.com/creerUtilisateur"
url2 = "http://127.0.0.1:8000/creerNotification"

utilisateur_id = str(uuid4())
lieu_id = str(uuid4())
appareil_id = str(uuid4())
equipement_id = str(uuid4())
notification_id = str(uuid4())

data = {
    "utilisateur": {
        "utilisateur_id": utilisateur_id,
        "email": "zaah@gmail.com",
        "motdepasse": "1235",
        "date_creation": "2025-05-21"
    },
    "lieu": {
        "lieu_id": lieu_id,
        "utilisateur_id": utilisateur_id,  # clé étrangère vers utilisateur
        "nom": "Maison",
        "adresse": "123 rue Exemple",
        "date_creation": str(date.today())
    },
    "appareil": {
        "appareil_id": appareil_id,
        "lieu_id": lieu_id,  # clé étrangère vers lieu
        "nom": "Thermostat",
        "type": "chauffage",
        "statut": "actif",
        "date_creation": str(date.today())
    },
    "equipement": {
        "equipement_id": equipement_id,
        "appareil_id": appareil_id,  # clé étrangère vers appareil
        "nom": "Capteur température",
        "type": "température",
        "statut": "actif",
        "date_creation": str(date.today())
    }
}

data1 = {
    "notification_id": notification_id, 
    "utilisateur_id" : "401eb00d-20a3-43c0-9c79-07c82b13d605",
    "evenement_id" : "e5338c49-af48-4f12-8cee-c64bb1c2d0f3",
    "statut_notification" : True, 
    "date_notification":str(date.today())
 
}

response = requests.post(url, json=data)
print("Status code:", response.status_code)
print("Response JSON:", response.json())
