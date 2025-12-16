from fastapi import FastAPI, HTTPException
from Insertions import Appareil, CreationRequest, Equipement, Evenement, Lieu, Notification, Utilisateur, inserer_appareil, inserer_equipement, inserer_lieu, inserer_notification, inserer_utilisateur, insertion_evenement
from selection import *

app = FastAPI()


@app.post("/creerUtilisateur")
def creer_utilisateur(data: CreationRequest):
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
def create_evenement(evenement : Evenement):
    evenement_id = insertion_evenement(evenement)
    return {"status": "success", "utilisateur_id": evenement_id}
 

@app.post("/creerNotification")
def create_notification(notif : Notification): 
    notification_id= inserer_notification(notif)
    return{"status": "success", "utilisateur_id": notification_id}


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
