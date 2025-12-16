from pathlib import Path
import json
import requests
import datetime 
from typing import Literal
from pydantic import ValidationError

from serveur.configuration import CONFIG
from serveur.services.utils import YOLO_MODELE , _sanitize_filename
from serveur.models.schemas import EventDataPublisher , AlerteRaspberry

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

    #remarque si model_validate => Casting automatique fait
    try  : 
        event_publisher = EventDataPublisher(
        event_id = donnes_raspberry.event_id,
        appareil_id = donnes_raspberry.device_id,
        timestamp_serveur = resultat.get("timestamp_serveur"),
        statut_alerte = resultat.get("dictionnaire_analyse").get("statut_alerte"),
        seuil_reponse_model = (resultat.get("dictionnaire_analyse").get("nombre_occurrence_personne") / resultat.get("dictionnaire_analyse").get("nombre_frames")), 
        statut_raspberry = donnes_raspberry.data.equipements.alerte_potentielle,
        statut_camera = donnes_raspberry.data.equipements.camera.statut,
        statut_bouton = donnes_raspberry.data.equipements.bouton.statut,
        statut_capteur = donnes_raspberry.data.equipements.capteure_temperature.statut,
        video_path= video_path
        )
        return event_publisher
    except ValidationError  as e : 
        print("erreur de validation pydantic dans la construction de l'évenement : ", str(e))   
        raise 


def envoyer_cloud_data(event_data:EventDataPublisher,video_path:str):
    route_cloud = f"{CONFIG.serveur_cloud.base_url}/creerEvenement"
    print("endpoint cloud = ",route_cloud)
    with open(video_path, "rb") as f:
        files = {"video": ("event.mp4", f, "video/mp4")}
        data = {"metadata": json.dumps(event_data)}
        r = requests.post(url = route_cloud, files=files, data=data, timeout=120)
        r.raise_for_status()
        return r.json()

    
    
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



def envoyer_raspberry_data(resultat_prediction):
    data = {
        "alerte_statut":resultat_prediction.get("dictionnaire_analyse").get("statut_alerte"),
        "algorithme": resultat_prediction.get("algorithme")
    }
    try :
        response = requests.post(url = CONFIG.serveur_raspberry.base_url , json = data , timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e :
        print("erreur envoi serveur :", e)
        return None
