from pathlib import Path
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field


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
    model_path: str = Field(default="yolov8n.pt", description="Chemin vers le modèle AI")
    device: Literal["cpu", "cuda"] = Field(default="cpu", description="Dispositif pour l'exécution du modèle")
    input_size: tuple[int, int] = Field(default=(640, 640), description="Taille d'entrée du modèle (largeur, hauteur)")

class YoloConfig(AIModelConfig):
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="P(objet présent) fois la P(classe correcte | objet)") 
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0, description="Seuil IoU pour la suppression non maximale")
    max_detections: int = Field(default=100, ge=1, description="Nombre maximum de détections par image")
    classes: Optional[List[str]] = Field(default=None, description="Liste des classes à détecter (None pour toutes)")
    evaluation_metrics: Dict[str, float] = Field(default_factory=dict, description="Métriques d'évaluation (ex: {'mAP': 0.85})")

class Configuration(BaseModel):
    path_config: PathConfig = Field(PathConfig(), description="Configuration des chemins")
    ai_config: YoloConfig = Field(YoloConfig(), description="Configuration du modèle AI YOLO")




def get_configuration(): 
    return Configuration()

CONFIG = get_configuration()