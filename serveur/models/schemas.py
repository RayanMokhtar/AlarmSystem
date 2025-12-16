from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

class CameraConfig(BaseModel):
    mode: Literal["eco", "surveillance"] = "eco"
    statut: Literal["actif", "inactif"] = "actif"
    seuil: float = Field(ge=0.0, le=1.0)

class CapteurTemperatureConfig(BaseModel):
    mode: Literal["seuil", "autre"] = "seuil"
    statut: Optional[str] = ""
    seuil: float

class BoutonConfig(BaseModel):
    mode: Literal["manuel", "autre"] = "manuel"
    statut: Optional[str] = ""
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
