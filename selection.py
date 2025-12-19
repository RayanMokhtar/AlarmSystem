from datetime import date, datetime
from fastapi import FastAPI, HTTPException
import psycopg2
from pydantic import BaseModel, EmailStr
from psycopg2.extras import RealDictCursor
from uuid import UUID
from passlib.context import CryptContext
from BaseModels import LoginRequest, Notification

DB_HOST = "postgresql-hammal.alwaysdata.net"
DB_NAME = "hammal_atelierrt"
DB_USER = "hammal"
DB_PASS = "Zahrdin.99"


def select_utilisateur(utilisateur_id: str):
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
            "SELECT * FROM utilisateur WHERE utilisateur_id = %s",
            (utilisateur_id,)
        )

        utilisateur = cur.fetchone()

        cur.close()
        conn.close()

        return utilisateur

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def select_lieu(utilisateur_id: str):
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
            select l.lieu_id, l.nom, l.adresse, l.date_creation,
                   a.appareil_id, a.nom, a.type, a.statut, a.date_creation,
                   e.equipement_id, e.nom, e.type, e.statut, e.date_creation 
            FROM utilisateur u
            LEFT JOIN lieu l ON l.utilisateur_id = u.utilisateur_id
            LEFT JOIN appareil a ON a.lieu_id = l.lieu_id
            LEFT JOIN equipement e ON e.appareil_id = a.appareil_id
            WHERE u.utilisateur_id = %s
            """,

            (utilisateur_id,)
        )

        lieu = cur.fetchone()  

        cur.close()
        conn.close()

        return lieu

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    


def select_notification(utilisateur_id: str, filtre: bool = False):
    print(f"DEBUG: select_notification called with utilisateur_id={utilisateur_id}, filtre={filtre}")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
        cur = conn.cursor()

        query = "SELECT * from notification WHERE utilisateur_id = %s"
        if filtre:
            query += " AND notification_vue = false"
        
        cur.execute(query, (utilisateur_id,))

        notif = cur.fetchall()
        
        # Si on filtre (uniquement les non vues), marquer seulement ces notifications comme vues
        if filtre and notif:
            print(f"DEBUG: Found {len(notif)} unread notifications to mark as viewed")
            for notification in notif:
                notification_id = notification['notification_id']
                print(f"DEBUG: Marking notification {notification_id} as viewed")
                update_query = "UPDATE notification SET notification_vue = true WHERE notification_id = %s"
                cur.execute(update_query, (notification_id,))
            conn.commit()
            print(f"DEBUG: All updates committed")
        
        cur.close()
        conn.close()

        return notif

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

def select_notification_nonlue(utilisateur_id: str):
    """
    Récupère les notifications non vues et les marque automatiquement comme vues.
    """
    return select_notification(utilisateur_id, filtre=True)
def connexion_utilisateur(data: LoginRequest):
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
            SELECT utilisateur_id, email, motdepasse
            FROM utilisateur
            WHERE email = %s
            """,
            (data.email,)
        )

        utilisateur = cur.fetchone()

        # Email inexistant
        if not utilisateur:
            raise HTTPException(
                status_code=401,
                detail="Email ou mot de passe incorrect"
            )

        # 3️⃣ Comparaison clair ↔ hash
        if not verifier_motdepasse(
            data.motdepasse,           # mot de passe EN CLAIR
            utilisateur["motdepasse"]  # hash en base
        ):
            raise HTTPException(
                status_code=401,
                detail="Email ou mot de passe incorrect"
            )

        cur.close()
        conn.close()

        # 4️⃣ Succès
        return {
            "message": "Connexion réussie",
            "utilisateur_id": utilisateur["utilisateur_id"],
            "email": utilisateur["email"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

import bcrypt

def verifier_motdepasse(motdepasse_clair: str, motdepasse_hash: str) -> bool:
    try:
        # Tentative de vérification Bcrypt
        motdepasse_clair_enc = motdepasse_clair[:72].encode("utf-8")
        motdepasse_hash_enc = motdepasse_hash.encode("utf-8")
        return bcrypt.checkpw(motdepasse_clair_enc, motdepasse_hash_enc)
    except Exception:
        # Fallback : comparaison en clair si ce n'est pas un hash Bcrypt valide
        return motdepasse_clair == motdepasse_hash

