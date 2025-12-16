from fastapi import FastAPI
import uvicorn
from serveur.routes.routes import router

app = FastAPI(title="Alarm Server")
app.include_router(router, prefix="/api/serveur_calcul")


def lancer_serveur() -> None:
    """
    lancer serveur 
    """
    uvicorn.run(
        "serveur.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    lancer_serveur()
