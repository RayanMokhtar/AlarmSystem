from datetime import date, datetime
from queue import Full
from fastapi import FastAPI, HTTPException
import psycopg2
from pydantic import BaseModel, EmailStr
from psycopg2.extras import RealDictCursor
from uuid import UUID, uuid4
from passlib.context import CryptContext
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException
import psycopg2
from BaseModels import Appareil, Equipement, Evenement, Lieu, Notification, Utilisateur
from ConnexionBDD import DB_HOST, DB_NAME, DB_USER, DB_PASS

app = FastAPI()

class CreationRequest(BaseModel):
    utilisateur: Utilisateur
    lieu: Lieu
    appareil: Appareil
    equipement: Equipement

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)
import bcrypt

def hasher_mot_de_passe(password: str) -> str:
    # tronquer à 72 caractères
    password = password[:72].encode('utf-8')
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    return hashed.decode('utf-8')

def inserer_utilisateur(data: Utilisateur):

    try:

        motdepasse_hache = hasher_mot_de_passe(data.motdepasse)

        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO utilisateur (utilisateur_id, email, motdepasse, date_creation, login)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s)
            RETURNING utilisateur_id
            """,
            (
                str(data.utilisateur_id),
                data.email,
                motdepasse_hache,  
                data.login
            )
        )

        utilisateur_id = cur.fetchone()["utilisateur_id"]

        conn.commit()
        cur.close()
        conn.close()

        return utilisateur_id

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def inserer_lieu(data: Lieu):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO lieu (lieu_id, utilisateur_id, nom, adresse, date_creation)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING lieu_id
            """,
            (str(data.lieu_id), str(data.utilisateur_id), data.nom, data.adresse)
        )
        lieu_id = cur.fetchone()["lieu_id"]
        conn.commit()
        cur.close()
        conn.close()
        return lieu_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def inserer_appareil(data: Appareil):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO appareil (appareil_id, lieu_id, nom, type, statut, date_creation)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING appareil_id
            """,
            (str(data.appareil_id), str(data.lieu_id), data.nom, data.type, data.statut)
        )
        appareil_id = cur.fetchone()["appareil_id"]
        conn.commit()
        cur.close()
        conn.close()
        return appareil_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def inserer_equipement(data: Equipement):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO equipement (equipement_id, appareil_id, nom, type, statut, date_creation)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING equipement_id
            """,
            (str(data.equipement_id), str(data.appareil_id), data.nom, data.type, data.statut)
        )
        equipement_id = cur.fetchone()["equipement_id"]
        conn.commit()
        cur.close()
        conn.close()
        return equipement_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




def insertion_evenement(evenement: Evenement):
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
        cur = conn.cursor()
        print("Insertion evenement app id:", evenement.appareil_id)
        # Insérer l'événement
        cur.execute(
            """
            INSERT INTO evenement (
                evenement_id, appareil_id, date_evenement, statut_alerte,
                timestamp_serveur, seuil_reponse_modele, timestamp_rasp,
                statut_camera, statut_capteur, emplacement_video_evenement, statut_boutton
            )
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s)
            RETURNING evenement_id
            """,
            (
                str(evenement.evenement_id),
                str(evenement.appareil_id),
                evenement.date_evenement,
                evenement.statut_alerte,
                evenement.seuil_reponse_modele,
                evenement.timestamp_rasp,
                evenement.statut_camera,
                evenement.statut_capteur,
                evenement.emplacement_video_evenement,
                evenement.statut_boutton
            )
        )

        evenement_id = cur.fetchone()["evenement_id"]

        # Récupérer utilisateur_id via appareil → lieu → utilisateur

        cur.execute(
            """
            SELECT l.utilisateur_id
            FROM appareil a
            JOIN lieu l ON a.lieu_id = l.lieu_id
            WHERE a.appareil_id = %s
            """,
            (str(evenement.appareil_id),)
        )

        result = cur.fetchone()
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Utilisateur introuvable pour cet appareil"
            )

        utilisateur_id = result["utilisateur_id"]

        cur.execute(
            """
            INSERT INTO notification (
                notification_id,
                utilisateur_id,
                evenement_id,
                statut_notification,
                date_notification,
                notification_vue, 
                message
            )
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s)
            """,
            (
                str(uuid4()),
                str(utilisateur_id),
                str(evenement_id),
                "Alerte intrusion",
                False,                 
                "Un intrus a été détecté chez vous !"
            )
        )

        
        conn.commit()

        cur.close()
        conn.close()

        return evenement_id

    except Exception as e:
        print("exception a ce niveua",str(e))
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

def inserer_notification(data: Notification):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
        cur = conn.cursor()
        print("data recue dans inserer notification ",data)
        cur.execute(
            """
            INSERT INTO notification (
                notification_id,
                utilisateur_id,
                evenement_id,
                statut_notification,
                date_notification,
                notification_vue, 
                message
            )
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s)
            RETURNING notification_id
            """,
            (
                str(uuid4()),
                str(data.utilisateur_id),
                str(data.evenement_id) if data.evenement_id else None,  # Gestion du None
                str(data.statut_notification),
                False,  # notification_vue forcé à False
                str(data.message)
            )
        )

        result = cur.fetchone()
        print("reultat dans fonction ",result)
        notification_id = result["notification_id"] if result else None
        conn.commit()

        cur.close()
        conn.close()

        return notification_id

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
