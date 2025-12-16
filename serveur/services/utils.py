import re 

from ultralytics import YOLO
from serveur.configuration import CONFIG
from functools import lru_cache

@lru_cache
def load_yolo_model():
    return YOLO(CONFIG.ai_config.model_path)

YOLO_MODELE = load_yolo_model()




def _sanitize_filename(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9._-]', '_', name)
