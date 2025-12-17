from argparse import OPTIONAL
from datetime import date, datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
import psycopg2
from pydantic import BaseModel, EmailStr
from psycopg2.extras import RealDictCursor
from uuid import UUID

DB_HOST = "postgresql-hammal.alwaysdata.net"
DB_NAME = "hammal_atelierrt"
DB_USER = "hammal"
DB_PASS = "Zahrdin.99"

app = FastAPI()

class Utilisateur(BaseModel):
    utilisateur_id: UUID
    email: EmailStr
    motdepasse: str
    date_creation: date
    login : str

class Lieu(BaseModel):
    lieu_id: UUID
    utilisateur_id: UUID
    nom: str
    adresse: str
    date_creation: date

class Appareil(BaseModel):
    appareil_id: UUID
    lieu_id: UUID
    nom: str
    type: str
    statut: str
    date_creation: date

class Equipement(BaseModel):
    equipement_id: UUID
    appareil_id: UUID
    nom: str
    type: str
    statut: str
    date_creation: date

class Evenement(BaseModel):
    evenement_id: UUID
    appareil_id: UUID
    date_evenement: datetime
    statut_alerte: bool
    timestamp_serveur: datetime
    seuil_reponse_modele: float
    timestamp_rasp: datetime
    statut_camera: bool
    statut_capteur: bool
    statut_boutton: bool
    emplacement_video_evenement: str

class CreationRequest(BaseModel):
    utilisateur: Utilisateur
    lieu: Lieu
    appareil: Appareil
    equipement: Equipement

class Notification(BaseModel):
    notification_id: UUID
    utilisateur_id: UUID
    evenement_id: Optional[UUID]
    statut_notification: str
    date_notification: datetime
    message: str

class LoginRequest(BaseModel):
    email: EmailStr
    motdepasse: str
