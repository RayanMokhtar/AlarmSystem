import requests
from uuid import uuid4
from datetime import date

url = "http://127.0.0.1:8000/creerUtilisateur"

utilisateur_id = str(uuid4())
lieu_id = str(uuid4())
appareil_id = str(uuid4())
equipement_id = str(uuid4())

data = {
    "utilisateur": {
        "utilisateur_id": utilisateur_id,
        "email": "zah@gmail.com",
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

response = requests.post(url, json=data)
print("Status code:", response.status_code)
print("Response JSON:", response.json())
