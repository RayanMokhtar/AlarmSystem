from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path
from uuid import UUID

class CameraConfig(BaseModel):
    mode: Literal["eco", "surveillance"] = "eco"
    statut: Literal["actif", "inactif"] = "actif"
    seuil: float

class CapteurTemperatureConfig(BaseModel):
    mode: Literal["seuil", "autre"] = "seuil"
    statut: Literal["actif", "inactif"] = "actif" 
    seuil: float

class BoutonConfig(BaseModel):
    mode: Literal["manuel", "autre"] = "manuel"
    statut: Literal["actif", "inactif"] = "actif"
    seuil: Optional[float] = None

class Equipements(BaseModel):
    camera: CameraConfig
    capteur_temperature: CapteurTemperatureConfig
    bouton: BoutonConfig

class VideoInfo(BaseModel):
    nom_fichier: str
    duree: int
    resolution: str
    fps: int

class EventData(BaseModel):
    alerte_potentielle: bool
    equipements: Equipements
    image_b64: Optional[str] = None
    video_info: Optional[VideoInfo] = None

class AlerteRaspberry(BaseModel):
    event_id: str
    timestamp_raspberry: datetime
    device_id: str
    data: EventData



class EventDataPublisher(BaseModel):
    evenement_id: UUID 
    appareil_id: UUID 
    date_evenement: datetime 
    timestamp_rasp:datetime
    timestamp_serveur: datetime 
    statut_alerte: bool 
    seuil_reponse_modele : float 
    statut_raspberry: bool
    statut_camera: bool
    statut_capteur: bool
    statut_boutton : bool
    emplacement_video_evenement: str 