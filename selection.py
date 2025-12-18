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

    


def select_notification(utilisateur_id: str):
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
            SELECT
            e.*,
            n.*
            FROM utilisateur u
            LEFT JOIN notification n 
            ON n.utilisateur_id = u.utilisateur_id
            LEFT JOIN evenement e 
            ON e.evenement_id = n.evenement_id
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

