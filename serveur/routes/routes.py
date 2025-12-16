from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from datetime import datetime
import json

from serveur.models.schemas import AlerteRaspberry
from serveur.services.traitement_video import pipeline_traitement_data , visualiser_video_yolo_service
from serveur.services.event_publisher import envoyer_cloud_data , construire_event_data , envoyer_raspberry_data , stockage_local_evenement , get_healthcheck_raspberry
from serveur.configuration import CONFIG
import requests


router = APIRouter()

@router.post("/recevoir_potentielle_alerte_json")
def recevoir_potentielle_alerte_json(payload: AlerteRaspberry):
    return {"ok": True, "event_id": payload.event_id}



@router.post("/visualiser_video_yolo")
async def visualiser_video_yolo(
    video: UploadFile | None = File(None),          
):
    try : 
        video_bytes = await video.read() if video else None
        visualiser_video_yolo_service(video_bytes)
    except Exception as e : 
        raise HTTPException(status_code=500, detail=f" erreur lors visualisation {str(e)}")



@router.post("/process/raspberry_alerte")
async def process_raspberry_alerte(
    raspberry_data: str = Form(...),                
    video: UploadFile | None = File(None),          
):
    try:
        metadata_dict = json.loads(raspberry_data)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"les json entré n'est pas valide {str(e)}")
    try:
        metadata = AlerteRaspberry.model_validate(metadata_dict)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Données invalide selon la schéma doit être de forme  {str(e)}")

    video_bytes = await video.read() if video else None
    
    resultats_modele , video_path = pipeline_traitement_data(video_bytes)
    print("reponse modele  ",resultats_modele)
    vraie_alerte = resultats_modele.get("dictionnaire_analyse").get("statut_alerte")
    print("vraie_alerte",vraie_alerte)
    if vraie_alerte : 
        print("vraie alerte avérée par serveur calcul => envoi au cloud ")
        #envoi au cloud + envoi à la raspberry puis stocage local 
        print('construction event data ....')
        event_data = construire_event_data(donnes_raspberry=metadata , resultat=resultats_modele ,video_path = video_path )
        print("envoi données vers le cloud ...",event_data)
        # response = envoyer_cloud_data(event_data,video_path = video_path)
        print("reponse json ... => ")
    print("log : insertion fichier en local")
    emplacement_trace_locale = stockage_local_evenement(resultat= resultats_modele,data_raspi=metadata)
    raspberry_data_reponse = envoyer_raspberry_data(resultats_modele) #temporaire à remplacer par al versionfianle
    return {"raspberry_data_reponse": raspberry_data_reponse, 
            "emplacement_trace_locale":emplacement_trace_locale , 
            "reponse_model":resultats_modele
            }



@router.get("/healthcheck_rpi")
def get_healthcheck_rpi():
    try :
        url_rpi = f"{CONFIG.serveur_raspberry.base_url}/healthcheck"
        response = requests.get(url = url_rpi , timeout=10 , verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e :
        print("erreur envoi serveur :", e)
        return None