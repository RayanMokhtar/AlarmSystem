from pathlib import Path
import json

BASE_DIR = Path("app/data/events") # à déplacer dans la configuration 

def save_event(event_id: str, metadata: dict, video_bytes: bytes):
    event_dir = BASE_DIR / event_id
    event_dir.mkdir(parents=True, exist_ok=True)

    # Sauvegarde metadata
    with open(event_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # Sauvegarde vidéo
    with open(event_dir / "video.mp4", "wb") as f:
        f.write(video_bytes)


def load_event_metadata(event_id: str) -> dict:
    event_dir = BASE_DIR / event_id
    with open(event_dir / "metadata.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_event_video_path(event_id: str) -> Path:
    return BASE_DIR / event_id / "video.mp4"
