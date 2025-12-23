import secrets
from uuid import UUID , uuid4

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

from serveur.configuration import CONFIG


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/connexion")


def generer_jwt_secret(nbr_octets = 32):
    cle = secrets.token_hex(nbr_octets)
    return cle #32octers => 64 hex caracteres 


#sub c'est userid ... 
def create_access_token(user_id: str) -> str:
    now = datetime.now()
    exp = now + timedelta(days=CONFIG.securite.duree_token)
    payload = {
        "sub": user_id, 
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, CONFIG.securite.jwt_secret, algorithm=CONFIG.securite.jwt_algorithme)


def create_refresh_token(user_id: str) -> str:
    now = datetime.now()
    exp = now + timedelta(days=CONFIG.securite.duree_refresh_token)

    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    return jwt.encode(
        payload,
        CONFIG.securite.jwt_secret,
        algorithm=CONFIG.securite.jwt_algorithme
    )


def get_current_user(token: str = Depends(oauth2_scheme)) -> UUID:
    try:
        payload = jwt.decode(
            token,
            CONFIG.securite.jwt_secret,
            algorithms=[CONFIG.securite.jwt_algorithme]
        )

        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Access token est requis")

        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Token invalide (id/sub manquant)")
        return UUID(sub)

    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")


