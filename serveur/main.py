from fastapi import FastAPI
import uvicorn
from serveur.routes.routes import router
from serveur.routes.auth import router as authentification_router
from serveur.configuration import CONFIG

app = FastAPI(title="Alarm Server")
app.include_router(router, prefix="/api/serveur_calcul")
app.include_router(authentification_router, prefix="/api/serveur_calcul")

def lancer_serveur() -> None:
    """
    lancer serveur 
    """
    uvicorn.run(
        "serveur.main:app",
        host=CONFIG.api_config.host,
        port=CONFIG.api_config.port,
        reload=False
    )


if __name__ == "__main__":
    lancer_serveur()
