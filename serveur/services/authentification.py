from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import requests
import os
from uuid import UUID

from serveur.configuration import CONFIG


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