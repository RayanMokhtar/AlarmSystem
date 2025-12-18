import json
import os
import shutil
from uuid import uuid4
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from Gestion_Video import enregistrer_video
from Insertions import Appareil, CreationRequest, Equipement, Evenement, Lieu, Notification, Utilisateur, inserer_appareil, inserer_equipement, inserer_lieu, inserer_notification, inserer_utilisateur, insertion_evenement
from Stats import *
from selection import *

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- AJOUT POUR ADAPTER L'APP MOBILE ---
@app.get("/health")
async def health():
    return {"status": "healthy", "database": "connected"}

@app.post("/auth/login")
async def auth_login(request: dict):
    try:
        login_or_email = request.get("login_or_email")
        password = request.get("password")
        
        from selection import DB_HOST, DB_NAME, DB_USER, DB_PASS, verifier_motdepasse
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT utilisateur_id, email, login, motdepasse FROM utilisateur WHERE email = %s OR login = %s", (login_or_email, login_or_email))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user or not verifier_motdepasse(password, user["motdepasse"]):
            return {"success": False, "message": "Identifiants incorrects"}

        return {
            "success": True,
            "message": "Connexion réussie",
            "user": {
                "id": str(user["utilisateur_id"]),
                "email": user["email"],
                "login": user["login"]
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/auth/register")
async def auth_register(request: dict):
    try:
        email = request.get("email")
        login = request.get("login")
        password = request.get("password")
        
        from Insertions import inserer_utilisateur, Utilisateur
        from datetime import date
        
        user_id = uuid4()
        new_user = Utilisateur(
            utilisateur_id=user_id,
            email=email,
            login=login,
            motdepasse=password,
            date_creation=date.today()
        )
        
        inserer_utilisateur(new_user)
        
        return {
            "success": True,
            "message": "Inscription réussie",
            "user": {
                "id": str(user_id),
                "email": email,
                "login": login
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
# ---------------------------------------

@app.post("/creerUtilisateur")
def creer_Compte_utilisateur(utilisateur: Utilisateur):
    user_id = inserer_utilisateur(utilisateur)
    return {
        "status": "success",
        "utilisateur_id": str(user_id)
    }

@app.post("/creer_Compte_utilisateur")
def creer_compte(data: CreationRequest):
     
    utilisateur_id = str(uuid4())
    lieu_id = str(uuid4())
    appareil_id = str(uuid4())
    equipement_id = str(uuid4())

    data.utilisateur.utilisateur_id = utilisateur_id
    data.lieu.lieu_id = lieu_id
    data.lieu.utilisateur_id = utilisateur_id
    data.appareil.appareil_id = appareil_id
    data.appareil.lieu_id = lieu_id
    data.equipement.equipement_id = equipement_id
    data.equipement.appareil_id = appareil_id

    try:
        user_id = inserer_utilisateur(data.utilisateur)
        lieu_id = inserer_lieu(data.lieu)
        appareil_id = inserer_appareil(data.appareil)
        equipement_id = inserer_equipement(data.equipement)

        return {
            "status": "success",
            "utilisateur_id": str(user_id),
            "lieu_id": str(lieu_id),
            "appareil_id": str(appareil_id),
            "equipement_id": str(equipement_id)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/creerLieu")
def create_lieu(data : Lieu):
    lieu_id = inserer_lieu(data)
    return {"status": "success", "utilisateur_id": lieu_id}

@app.post("/creerAppareil")
def create_appareil(data : Appareil):
    appareil_id = inserer_appareil(data)
    return {"status": "success", "appareil_id": appareil_id}

@app.post("/creerEquipement")
def create_equipement(data : Appareil):
    equipement_id = inserer_equipement(data)
    return {"status": "success", "equipement_id": equipement_id}

@app.post("/creerEvenement")
async def create_evenement(evenement: str = Form(...),video: UploadFile = File(...)):
    # Convertir la string JSON en dict, puis en modèle Pydantic
    try : 
        evenement_data = json.loads(evenement)
        try : 
            evenement_obj = Evenement(**evenement_data)
        except Exception as e : 
            print("erreur ici", str(e))
        
        evenement_obj.evenement_id = str(uuid4())
        print("evenement_obj",evenement_obj)
        evenement_id = insertion_evenement(evenement_obj)
        print("partie video : ")
        out_path = f"videos_engistrées/{video.filename}"
        with open(out_path, "wb") as f:
            while chunk := await video.read(1024 * 1024):
                f.write(chunk)

        return {
            "status": "success",
            "evenement_id": evenement_id,
            "status_vid": "ok",
            "saved_as": str(out_path)
        }
    except Exception as e : 
        raise HTTPException(status_code=500,detail=f"erreur interne de serveur{str(e)}")

@app.post("/creerNotification")
def create_notification(notif : Notification): 
    notification_id= inserer_notification(notif)
    return{"status": "success", "notification_id": notification_id}


@app.get("/chercher_utilisateur/{utilisateur_id}")
def get_utilisateur(utilisateur_id: str):
    utilisateur = select_utilisateur(utilisateur_id)

    if utilisateur is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    return utilisateur

@app.get("/chercher_lieu/{utilisateur_id}")
def get_lieu(utilisateur_id: str):
    lieu = select_lieu(utilisateur_id)

    if lieu is None:
        raise HTTPException(status_code=404, detail="lieu introuvable")

    return lieu

@app.get("/chercher_notification/{utilisateur_id}")
def get_notification(utilisateur_id: str):
    lieu = select_notification(utilisateur_id)

    if lieu is None:
        raise HTTPException(status_code=404, detail="lieu introuvable")

    return lieu

@app.post("/Connexion")
def vérif_Connexion(data: LoginRequest):
    reponse = connexion_utilisateur(data)
    return reponse

@app.get("/Stats_total_system")
def nombreUtiliasteur():
    nb = calculer_Nb_lieu()
    return nb

@app.get("/Stats_total_equipement")
def nombreEquipement():
    nb = calculer_Nb_equipement()
    return nb

@app.get("/nombreEquipementEnPanne")
def nombreEquipementEnPanne():
    nb = calculerEquipementEnPanne()
    return nb 


@app.get("/equipement_le_plus_en_panne")
def nombreEquipementEnPanne():
    nb = Trouver_equip_le_plus_en_panne()
    return nb 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8040)