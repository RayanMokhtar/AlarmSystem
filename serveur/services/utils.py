import re 

from ultralytics import YOLO
from serveur.configuration import CONFIG
from functools import lru_cache

from serveur.models.schemas import AlerteRaspberry , EventDataPublisher
from pydantic import ValidationError


@lru_cache
def load_yolo_model():
    return YOLO(CONFIG.ai_config.model_path)

YOLO_MODELE = load_yolo_model()



def _sanitize_filename(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9._-]', '_', name)



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
