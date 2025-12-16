from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from datetime import datetime
import json

from serveur.models.schemas import AlerteRaspberry
from serveur.services.stockage import save_event
from serveur.services.traitement_video import analyser_media

router = APIRouter()

@router.post("/recevoir_potentielle_alerte_json")
def recevoir_potentielle_alerte_json(payload: AlerteRaspberry):
    return {"ok": True, "event_id": payload.event_id}




@router.post("/recevoir_potentielle_alerte")
async def recevoir_potentielle_alerte(
    metadata_json: str = Form(...),                
    image: UploadFile | None = File(None),          
    video: UploadFile | None = File(None),          
):
    try:
        metadata_dict = json.loads(metadata_json)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"les json entré n'est pas valide {str(e)}")
    try:
        metadata = AlerteRaspberry.model_validate(metadata_dict)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Données invalide selon la schéma doit être de forme  {str(e)}")

    image_bytes = await image.read() if image else None
    video_bytes = await video.read() if video else None
    
    media_details = analyser_media(image_bytes, video_bytes)
    print("medias ",media_details)
    return {
        "ok": True,
        "event_id": metadata.event_id,
        "alerte_potentielle": metadata.data.alerte_potentielle,
        "image_recue": image is not None,
        "video_recue": video is not None,
        "image_content_type": None if image is None else image.content_type,
        "video_content_type": None if video is None else video.content_type,
    }