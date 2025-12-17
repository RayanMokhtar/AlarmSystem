from pathlib import Path
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

class PathConfig(BaseModel):
    data_dir: Path = Field(
        default=DATA_DIR,
        description="Répertoire de base absolu pour les données (Serveur/data)"
    )

    videos_path: Path = Field(
        default=DATA_DIR / "videos",
        description="Chemin vers le répertoire des vidéos"
    )

    images_path: Path = Field(
        default=DATA_DIR / "images",
        description="Chemin vers le répertoire des images"
    )

    logs_path: Path = Field(
        default=DATA_DIR / "logs",
        description="Chemin vers le répertoire des logs"
    )

    models_path: Path = Field(
        default=DATA_DIR / "models",
        description="Chemin vers le répertoire des modèles"
    )

    output_models_path: Path = Field(
        default=DATA_DIR / "output_models",
        description="Chemin vers le répertoire des modèles de sortie"
    )



class AIModelConfig(BaseModel):
    model_path: Path = Field(default=Path(PathConfig().models_path / "yolov8n.pt"), description="Chemin vers le modèle AI")
    device: Literal["cpu", "cuda"] = Field(default="cpu", description="Dispositif pour l'exécution du modèle")
    input_size: tuple[int, int] = Field(default=(640, 640), description="Taille d'entrée du modèle (largeur, hauteur)")

class YoloConfig(AIModelConfig):
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="P(objet présent) fois la P(classe correcte | objet)") 
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0, description="Seuil IoU pour la suppression non maximale")
    max_detections: int = Field(default=100, ge=1, description="Nombre maximum de détections par image")
    classes: Optional[List[str]] = Field(default=None, description="Liste des classes à détecter (None pour toutes)")
    evaluation_metrics: Dict[str, float] = Field(default_factory=dict, description="Métriques d'évaluation (ex: {'mAP': 0.85})")


class ApiConfig(BaseModel):
    host: str = Field(default="0.0.0.0", description="Adresse d'écoute api")
    description: Optional[str] = Field(default=None, description="Description courte du service/API")
    port : int = Field(default=8080, description="port d'exposition de l'api")  
    
class ExternalApiConfig(BaseModel):
    base_url: str = Field(default="https://api_adam:8000", description="URL de base de l'API externe")
    auth_token: Optional[str] = Field(default=None, description="Token d'authentification si besoin")
    timeout: int = Field(default=10, description="Timeout en secondes pour les requêtes")
    

class Security(BaseModel):
    jwt_algorithme : str = Field(default="HS256", description="URL de base de l'API externe")
    jwt_secret : str = Field(default="some_key",description = "clé privée dans serveur seulement, sert à signer jwt et peut les vérifier")
    duree_token : int = Field(default=60,description="durée du tokens")
    duree_refresh_token : int = Field(default=120,description="durée token refresh")
                             
class Configuration(BaseModel):
    model_config = SettingsConfigDict(env_file='.env', env_nested_delimiter='__')
    path_config: PathConfig = Field(PathConfig(), description="Configuration des chemins")
    ai_config: YoloConfig = Field(YoloConfig(), description="Configuration du modèle AI YOLO")
    api_config: ApiConfig = Field(ApiConfig(), description="Config de l'API locale")
    serveur_raspberry : ExternalApiConfig = Field(ExternalApiConfig(base_url="http://192.168.1.2:5000"), description="Config d'une API externe")
    serveur_cloud : ExternalApiConfig = Field(ExternalApiConfig(base_url="http://10.231.151.22:8040"), description="Config du serveur cloud ")
    securite : Security = Field(Security(),description="classe sécurité")

def get_configuration(): 
    return Configuration()

CONFIG = get_configuration()