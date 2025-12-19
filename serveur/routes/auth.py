from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response, Query , Depends
from uuid import UUID
from jose import jwt, JWTError

from serveur.configuration import CONFIG
from serveur.models.db_models import LoginRequest
from serveur.models.db_models import Notification

from serveur.services.security import create_access_token, create_refresh_token, get_current_user
from serveur.services.authentification import authenticate_user , inscrire_user 
from serveur.services.event_publisher import creer_notification , get_notifications_from_user , get_notifications_nonlues


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/connexion")
def login(request: LoginRequest):
    """
    Endpoint de connexion pour authentifier un utilisateur et générer des tokens JWT.
    
    - **request**: Les données de connexion (email et mot de passe).
    
    Retourne un dictionnaire contenant les tokens d'accès et de rafraîchissement.
    """
    try:
        user_id = authenticate_user(request.email, request.motdepasse)
        if not user_id:
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
        access_token = create_access_token(str(user_id))
        refresh_token = create_refresh_token(str(user_id))
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la connexion: {str(e)}")


@router.post("/inscrire")
def inscrire_utilisateur(email: str, motdepasse: str, login: str, adresse: str):
    """
    Endpoint pour inscrire un nouvel utilisateur.
    
    - **email**: Adresse email.
    - **motdepasse**: Mot de passe.
    - **login**: Nom d'utilisateur.
    - **adresse**: Adresse du lieu.
    
    Retourne les IDs créés ou une erreur.
    """
    try:
        result = inscrire_user(email, motdepasse, login, adresse)
        if result:
            return {"status": "success", **result}
        else:
            raise HTTPException(status_code=500, detail="Échec de l'inscription")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'inscription: {str(e)}")
    

@router.post("/refresh")
def refresh_token(refresh_token: str):
    """
    Endpoint pour rafraîchir le token d'accès en utilisant le token de rafraîchissement.
    
    - **refresh_token**: Le token de rafraîchissement.
    
    Retourne un nouveau token d'accès.
    """
    try:
        payload = jwt.decode(
            refresh_token,
            CONFIG.securite.jwt_secret,
            algorithms=[CONFIG.securite.jwt_algorithme]
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token de rafraîchissement requis")
        
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Token invalide")        
        new_access_token = create_access_token(sub)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Token de rafraîchissement invalide ou expiré")


@router.get("/me")
def get_me(current_user: UUID = Depends(get_current_user)):  
    """
    Endpoint pour obtenir les informations de l'utilisateur actuel.
    
    Nécessite un token d'accès valide.
    """
    return {"user_id": str(current_user)}



@router.post("/creer_notification")
def creer_notification_route(data: Notification):
    """
    Route pour créer une notification via le service creer_notification.
    """
    try:
        result = creer_notification(data)
        if result:
            return {"status": "success", "data": result}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la création de la notification")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.get("/notifications")
def get_notifications(user_id: str = Query(...), filtre: bool = Query(True)):
    """
    Route pour récupérer les notifications d'un utilisateur via le service get_notifications_from_user.
    - user_id: ID de l'utilisateur (requis).
    - filtre: Si True, retourne seulement les notifications non vues. Si False, toutes.
    """
    try:
        result = get_notifications_from_user(user_id, filtre)
        if result is not None:
            return {"status": "success", "notifications": result}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la récupération des notifications")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    
    
@router.get("/notifsnonlues")
def get_notifications(utilisateur_id: str = Query(...)):
    try:
        result = get_notifications_nonlues(utilisateur_id)
        return {"status":"success","notifications":result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
