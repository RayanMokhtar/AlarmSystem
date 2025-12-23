from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import requests
import os
from uuid import UUID , uuid4
from datetime import date
from fastapi import HTTPException
from pydantic import BaseModel, EmailStr

from serveur.configuration import CONFIG
from serveur.models.db_models import Utilisateur , Lieu , Appareil, Equipement

CLOUD_URL = CONFIG.serveur_cloud.base_url

def authenticate_user(email: str, mot_de_passe: str) -> UUID | None:
    """
    Authentifie un utilisateur en envoyant les credentials au serveur cloud.
    
    - Envoie une requête POST à {CLOUD_URL}/Connexion avec les données de connexion.
    - Si la réponse est valide, retourne l'utilisateur_id ; sinon None.
    """
    url = f"{CLOUD_URL}/Connexion"
    payload = {
        "email": email,
        "motdepasse": mot_de_passe
    }
    
    try:
        print("requete ...")
        response = requests.post(
            url,
            json=payload,  
            timeout=CONFIG.serveur_cloud.timeout, 
            headers={"Content-Type": "application/json"}  
        )
        
        response.raise_for_status()
        data = response.json()
        
        if "utilisateur_id" in data:
            return UUID(data["utilisateur_id"])
        else:
            # Si la structure est différente, ajustez ici
            print(f"Réponse inattendue du cloud: {data}")
            return None
    
    except requests.exceptions.RequestException as e:
        # Erreur de réseau ou HTTP (ex: timeout, 401, etc.)
        print(f"Erreur lors de l'appel au serveur cloud: {e}")
        return None
    except ValueError as e:
        # Erreur de parsing JSON
        print(f"Erreur de parsing de la réponse JSON: {e}")
        return None
    


def authenticate_user(email: str, mot_de_passe: str) -> UUID | None:
    """
    Authentifie un utilisateur en envoyant les credentials au serveur cloud.
    
    - Envoie une requête POST à {CLOUD_URL}/Connexion avec les données de connexion.
    - Si la réponse est valide, retourne l'utilisateur_id ; sinon None.
    """
    url = f"{CLOUD_URL}/Connexion"
    payload = {
        "email": email,
        "motdepasse": mot_de_passe
    }
    
    try:
        print("requete ...")
        response = requests.post(
            url,
            json=payload,  
            timeout=CONFIG.serveur_cloud.timeout, 
            headers={"Content-Type": "application/json"}  
        )
        
        response.raise_for_status()
        data = response.json()
        
        if "utilisateur_id" in data:
            return UUID(data["utilisateur_id"])
        else:
            # Si la structure est différente, ajustez ici
            print(f"Réponse inattendue du cloud: {data}")
            return None
    
    except requests.exceptions.RequestException as e:
        # Erreur de réseau ou HTTP (ex: timeout, 401, etc.)
        print(f"Erreur lors de l'appel au serveur cloud: {e}")
        return None
    except ValueError as e:
        # Erreur de parsing JSON
        print(f"Erreur de parsing de la réponse JSON: {e}")
        return None
    

def inscrire_user(email: str, motdepasse: str, login: str, adresse: str):
    """
    Inscrit un nouvel utilisateur en appelant l'endpoint /creer_Compte_utilisateur du cloud.
    
    - Génère IDs et objets par défaut.
    - Envoie un payload complet (CreationRequest) au cloud.
    - Retourne les IDs depuis la réponse du cloud.
    """
    try:
        #générer ids 
        utilisateur_id = str(uuid4())
        lieu_id = str(uuid4())
        appareil_id = str(uuid4())
        equipement_id = str(uuid4())
        today = date.today()

        url = f"{CLOUD_URL}/creer_Compte_utilisateur"
        
        payload = {
            "utilisateur": {
                "utilisateur_id": utilisateur_id,
                "email": email,
                "motdepasse": motdepasse,
                "date_creation": str(today),
                "login": login
            },
            "lieu": {
                "lieu_id": lieu_id,
                "utilisateur_id": utilisateur_id,
                "nom": "maison",
                "adresse": adresse,
                "date_creation": str(today)
            },
            "appareil": {
                "appareil_id": appareil_id,
                "lieu_id": lieu_id,
                "nom": "Caméra de sécurité",
                "type": "Sécurité",
                "statut": "Actif",
                "date_creation": str(today)
            },
            "equipement": {
                "equipement_id": equipement_id,
                "appareil_id": appareil_id,
                "nom": "Capteur infrarouge",
                "type": "Détection",
                "statut": "Actif",
                "date_creation": str(today)
            }
        }
        
        print(f"Requête d'inscription vers {url}")
        response = requests.post(
            url,
            json=payload,
            timeout=CONFIG.serveur_cloud.timeout,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Retourner les IDs depuis la réponse du cloud
        return {
            "utilisateur_id": data.get("utilisateur_id"),
            "lieu_id": data.get("lieu_id"),
            "appareil_id": data.get("appareil_id"),
            "equipement_id": data.get("equipement_id")
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Erreur réseau lors de l'inscription: {e}")
        return None
    except ValueError as e:
        print(f"Erreur de parsing JSON: {e}")
        return None
    except Exception as e:
        print(f"Erreur générale: {e}")
        return None
    



