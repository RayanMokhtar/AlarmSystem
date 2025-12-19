from pathlib import Path
import json
import requests
import datetime 
from uuid import UUID

from typing import Literal
from pydantic import ValidationError
from fastapi import HTTPException

from serveur.configuration import CONFIG
from serveur.services.utils import YOLO_MODELE , _sanitize_filename
from serveur.models.schemas import EventDataPublisher , AlerteRaspberry
from serveur.models.db_models import Notification 


"""persistence des documents en requete post 

TODO : Configurer Config pour zahrou // api et une pour adam pour les request.post facilement
"""

def construire_event_data(donnes_raspberry : AlerteRaspberry , resultat:dict,video_path:str):
    """resultat = {
        "dictionnaire_analyse":dictionnaire_analyse, 
        "nombre_frames":nbr_frames or None, 
        # "meilleures_detections_par_frame":meilleures_detections_par_frame or None,
        "algorithme":algorithme,
        "classes_yolo":compteur_classes or None
    }"""

    d = resultat.get("dictionnaire_analyse", {})
    try:
        event_id = UUID(str(donnes_raspberry.event_id))
        appareil_id = UUID(str(donnes_raspberry.device_id))
        print("appareil_id" , appareil_id)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"ID invalid: {e}") from e

    nb_personnes = d.get("nombre_occurrence_personne", 0)
    nb_frames = d.get("nombre_frames") or 1  
    seuil = float(nb_personnes) / float(nb_frames)

    statut_camera = (donnes_raspberry.data.equipements.camera.statut == "actif")
    statut_capteur = (donnes_raspberry.data.equipements.capteur_temperature.statut == "actif")
    statut_bouton = (donnes_raspberry.data.equipements.bouton.statut == "actif")
    print("statut",statut_camera,statut_capteur,statut_bouton)

    try : 
        event_publisher = EventDataPublisher(
            evenement_id=event_id,
            appareil_id=appareil_id,
            timestamp_serveur=resultat.get("timestamp_serveur"),
            statut_alerte=bool(d.get("statut_alerte", False)),
            date_evenement = datetime.datetime.now(),
            timestamp_rasp = donnes_raspberry.timestamp_raspberry,
            seuil_reponse_modele=seuil,
            statut_raspberry=donnes_raspberry.data.alerte_potentielle,
            statut_camera=statut_camera,
            statut_boutton=statut_bouton,
            statut_capteur=statut_capteur,
            emplacement_video_evenement=video_path,
        )
        return event_publisher
    except Exception as e :
        raise HTTPException(status_code=422, detail=str(e)) from e 



def envoyer_cloud_data(event_data:EventDataPublisher,video_path:str):
    try : 
        route_cloud = f"{CONFIG.serveur_cloud.base_url}/creerEvenement"
        print("endpoint cloud = ",route_cloud)
        event_data_model_verif = event_data.model_dump_json()#sérialisation directe
        with open(video_path, "rb") as f:
            files = {"video": ("event.mp4", f, "video/mp4")}
            data = {"evenement": event_data_model_verif}
            r = requests.post(url = route_cloud, files=files, data=data, timeout=120)
            r.raise_for_status()
            return r.json()
    except Exception as e : 
        print("erreur lors de l'insertion dans le cloud", str(e))
        

    
    
def stockage_local_evenement(resultat : dict , data_raspi : AlerteRaspberry , nom_fichier = None , type_log = "log_applicatif"):
    """
    stockage différents évenements dans les logs en spécifiant le type 
    
    resultat = {
        "dictionnaire_analyse":dictionnaire_analyse, 
        "nombre_frames":nbr_frames or None, 
        # "meilleures_detections_par_frame":meilleures_detections_par_frame or None,
        "algorithme":algorithme,
        "classes_yolo":compteur_classes or None
    }"""
    #data_raspi et resultat 
    combined = {
        "resultat": resultat,
        "data_raspi": data_raspi.model_dump()
    }
    if nom_fichier is None:
        nom_fichier = f"raspberry_modele_{type_log}_{datetime.datetime.now()}.json"
        nom_fichier = _sanitize_filename(nom_fichier)
    emplacement_fichier = CONFIG.path_config.logs_path / nom_fichier
    with open(emplacement_fichier, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2 , default=str)
    return emplacement_fichier    



def stockage_local_evenement_log(resultat : dict , data_raspi : AlerteRaspberry , nom_fichier = None , type_log = "log_applicatif"):
    """
    Stockage des événements en une seule ligne JSON pour Loki (mono-ligne).
    Format : 1 événement = 1 ligne JSON.
    """
    # data_raspi et resultat 
    combined = {
        "resultat": resultat,
        "data_raspi": data_raspi.model_dump()
    }
    if nom_fichier is None:
        nom_fichier = f"raspberry_modele_{type_log}_{datetime.datetime.now()}.log"
        nom_fichier = _sanitize_filename(nom_fichier)
    emplacement_fichier = CONFIG.path_config.logs_path / nom_fichier
    with open(emplacement_fichier, "a", encoding="utf-8") as f:  
        json_line = json.dumps(combined, ensure_ascii=False, default=str)
        f.write(json_line + "\n") 
    return emplacement_fichier


def envoyer_raspberry_data(resultat_prediction):
    data = {
        "alerte_statut":resultat_prediction.get("dictionnaire_analyse").get("statut_alerte"),
        "algorithme": resultat_prediction.get("algorithme")
    }
    endpoint_process_alerte = f"{CONFIG.serveur_raspberry.base_url}/process_alert"
    try :
        response = requests.post(url = endpoint_process_alerte, json = data , timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e :
        print("erreur envoi serveur :", e)
        return None



def get_last_raspberry_id_service():
    try :
        url_rpi = f"{CONFIG.serveur_cloud.base_url}/get_last_raspberry_id"
        response = requests.get(url = url_rpi , timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e : 
        print("erreur envoi serveur :", e)
        return None


def creer_notification(data: Notification):
    try:
        print("création notification avec data", data)
        url = f"{CONFIG.serveur_cloud.base_url}/creerNotification"
        print("cration de la notification")
        json_data = data.model_dump(mode="json")
        print("json_data", json_data)
        response = requests.post(
            url=url,
            json=json_data, 
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("erreur envoi serveur :", e)
        return None
    
    
def get_notifications_from_user(user_id: str , filtre : bool):
    try:
        url = f"{CONFIG.serveur_cloud.base_url}/chercher_notification"
        params = {"utilisateur_id": str(user_id)}
        response = requests.get(
            url=url,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        resultat = response.json() 
        if filtre:
            return [r for r in resultat if not r.get("notification_vue", False)]
        else:
            return resultat

    except requests.exceptions.RequestException as e:
        print("erreur récupération notifications :", e)
        return None
    

def get_notifications_nonlues(utilisateur_id: str):
    try:
        url = f"{CONFIG.serveur_cloud.base_url}/notifsnonlues"
        params = {"utilisateur_id": str(utilisateur_id)}
        response = requests.get(
            url=url,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        resultat = response.json() 
        return resultat

    except requests.exceptions.RequestException as e:
        print("erreur récupération notifications :", e)
        return None