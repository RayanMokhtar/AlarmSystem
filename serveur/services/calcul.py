import io
import os
import base64
import cv2
import uuid
import datetime 

from typing import Optional
from ultralytics import YOLO
from PIL import Image
from collections import Counter


from serveur.services.stockage import load_event_metadata, get_event_video_path
from serveur.configuration import CONFIG



def videos_bytes_to_file(video_bytes: bytes, nom_fichier : Optional[str] , extension = ".mp4" , lancer_video : bool = True):
    if filename is None:
        filename = f"temp_video_{datetime.datetime.now()}{extension}"
    video_path = f"{CONFIG.path_config.videos_path}/{nom_fichier}"
    print("video path",video_path)
    with open(video_path,"wb") as f : 
        f.write(video_bytes)
    if lancer_video : 
        os.startfile(video_path)
    return video_path 
 


def analyser_media(image_bytes: bytes | None, video_bytes: bytes | None) -> dict:
    result = {"image": None, "video": None}
    if image_bytes is not None:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.show()
            result["image"] = {
                "format": image.format,
                "size": image.size,
                "mode": image.mode,
                "taille_bytes": len(image_bytes)
            }
            image.close()
        except Exception as e:
            result["image"] = {"erreur": f"Impossible d'analyser l'image: {e}"}

    if video_bytes is not None:
        try:
            yolo_summary = traiter_video(video_bytes)
            result["video"] = yolo_summary
        except Exception as e:
            result["video"] = {"erreur": f"Impossible d'afficher la vidéo: {e}"}
        return result



def generer_video_annotee_yolo(video_path: str,
                               model_path: str = "yolov8n.pt",
                               conf: float = 0.25,
                               iou: float = 0.45) -> str:
    """
    Lit la vidéo `video_path`, applique YOLO sur chaque frame,
    dessine les boxes, écrit une nouvelle vidéo MP4 annotée,
    et renvoie le chemin de sortie.
    """
    model = YOLO(model_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Impossible d'ouvrir la vidéo: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps is None or fps <= 0:
        fps = 25  # fallback

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, conf=conf, iou=iou, verbose=False)

        # plot() dessine boxes + labels sur l'image
        annotated = results[0].plot()#un element donc liste 

        writer.write(annotated)

    cap.release()
    writer.release()

    return out_path


def traiter_video(videos_bytes, conf=CONF, model_path=MODEL_PATH, iou=IOU):

    video_path = video_show(videos_bytes)
    annotated_path = generer_video_annotee_yolo(
        video_path=video_path,
        model_path=model_path,
        conf=conf,
        iou=iou
    )
    os.startfile(annotated_path)
    model = YOLO(model_path)
    results_iter = model.predict(source=video_path, conf=conf, iou=iou, stream=True, verbose=False)

    nb_frames = 0
    classes_counter = Counter()
    max_conf_seen = 0.0

    for r in results_iter:
        nb_frames += 1
        if r.boxes is not None and len(r.boxes) > 0:
            for cls_id in r.boxes.cls.tolist():
                classes_counter[model.names[int(cls_id)]] += 1
            frame_max = float(r.boxes.conf.max().item())
            max_conf_seen = max(max_conf_seen, frame_max)

    return {
        "temp_path_original": video_path,
        "temp_path_yolo": annotated_path,
        "frames_processed": nb_frames,
        "detections_by_class": dict(classes_counter),
        "max_conf_seen": max_conf_seen,
        "model": model_path,
        "conf": conf,
        "iou": iou
    }