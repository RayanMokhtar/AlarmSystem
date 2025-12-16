import io
import os
import base64
import cv2
import uuid
import datetime 

from collections import Counter

from typing import Optional , Literal , Dict
from ultralytics import YOLO
from PIL import Image
from collections import Counter

from serveur.configuration import CONFIG
from serveur.services.utils import YOLO_MODELE , _sanitize_filename



SEUIL_YOLO = 10 #ou seuil dynamique avec présence au moins 20% du temps 0.2*fps*duree_record


def videos_bytes_to_file(video_bytes: bytes, nom_fichier = None, extension = ".mp4" , lancer_video : bool = True):
    if nom_fichier is None:
        nom_fichier = f"video_{datetime.datetime.now()}{extension}"
        nom_fichier = _sanitize_filename(nom_fichier)
    video_path = f"{CONFIG.path_config.videos_path}/{nom_fichier}"
    
    print("video path",video_path)
    with open(video_path,"wb") as f : 
        f.write(video_bytes)
    if lancer_video : 
        try: 
            os.startfile(video_path)
        except Exception as e : 
            print("pb lecture video ",str(e))
    return video_path 
 

def lancer_video(video_path : str ) -> None:
    try: 
        print("lancement video ................",video_path)
        os.startfile(video_path)
    except Exception as e : 
        print("pb lecture video ",str(e))
        

def get_video_annotee_yolo(video_path: str , fichier_sortie = "sortie_yolo.mp4") -> str:
    DEFAULT_FPS = 25
    model = YOLO_MODELE
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("erreur ouverture video ",video_path)

    fps = cap.get(cv2.CAP_PROP_FPS) or DEFAULT_FPS
    print("fps", fps)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    nom_fichier = f'{datetime.datetime.now()}/{fichier_sortie}'
    nom_fichier = _sanitize_filename(nom_fichier)
    fichier_sortie = f"{CONFIG.path_config.output_models_path}/{nom_fichier}"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v") #maniere de compresser
    writer = cv2.VideoWriter(fichier_sortie, fourcc, fps, (width, height))

    while True:
        etat , frame = cap.read()
        if not etat : 
            break
        results = model.predict(frame, conf=CONFIG.ai_config.confidence_threshold , iou=CONFIG.ai_config.iou_threshold , verbose=False)
        annotation_sur_image = results[0].plot() 
        writer.write(annotation_sur_image)

    cap.release()
    writer.release()
    return fichier_sortie



def traiter_video_avec_yolo(video_path,model):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Impossible d'ouvrir la vidéo")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, conf=CONFIG.ai_config.confidence_threshold , iou=CONFIG.ai_config.iou_threshold , verbose=False)
        yield results[0]  
    cap.release()



def agreger_stats_yolo(results_generator, model):
    nb_frames = 0
    classes_counter = {}
    best_detection_per_frame = []
    for r in results_generator:
        nb_frames += 1
        if r.boxes is not None and len(r.boxes) > 0:#existe BoundingBox et au moins un objet récupéré
            for classe in r.boxes.cls.tolist():#classes récupérées 
                class_name = model.names[int(classe)]#0 => name de la classe
                if class_name not in classes_counter.keys(): # ou faire un get / counter
                    classes_counter[class_name] = 1
                else :
                    classes_counter[class_name]+= 1

            # confidences = r.boxes.conf
            # max_idx = confidences.argmax().item()#index meilleur box
            # best_conf = float(confidences[max_idx].item())
            # best_class_id = int(r.boxes.cls[max_idx].item())
            # best_class_name = model.names[best_class_id]
            # best_box = r.boxes.xyxy[max_idx].tolist()

            # best_detection_per_frame.append({
            #     "confidence": best_conf,
            #     "class": best_class_name,
            #     "box": best_box
            # })
        else:
            best_detection_per_frame.append(None)
    return nb_frames, classes_counter, best_detection_per_frame


def seuillage_yolo(classes_counter: Dict[str,int] ,seuil_personnes = SEUIL_YOLO):
    nombre_classe_personne = classes_counter.get("person",0)
    return {
        "nombre_occurrence_personne": nombre_classe_personne,
        "statut_alerte": nombre_classe_personne >= seuil_personnes #respecter notation schéma de données que j'ai donné à Zahrou dans le cloud 
    }



def pipeline_traitement_video(videos_bytes : bytes , algorithme : Literal["YOLO","TI"]):
    video_path = videos_bytes_to_file(videos_bytes,lancer_video=False)
    model = YOLO_MODELE
    if algorithme == "YOLO" : 
        resultats_yield = traiter_video_avec_yolo(video_path,model)
        nbr_frames , compteur_classes , meilleures_detections_par_frame = agreger_stats_yolo(resultats_yield,model)
        dictionnaire_analyse = seuillage_yolo(compteur_classes)
    else : 
        print("autre algo à développer")
        dictionnaire_analyse = {}
    resultat = {
        "dictionnaire_analyse":dictionnaire_analyse, 
        "nombre_frames":nbr_frames or None, 
        # "meilleures_detections_par_frame":meilleures_detections_par_frame or None,
        "algorithme":algorithme,
        "classes_yolo":compteur_classes or None
    }
    return resultat




def visualiser_video_yolo_service(video_bytes):
    if video_bytes:
        video_path = videos_bytes_to_file(video_bytes,lancer_video=False)
        fichier_sortie_modele = get_video_annotee_yolo(video_path)
        print("ficheir sortie",fichier_sortie_modele)
        lancer_video(fichier_sortie_modele)





def analyser_media(image_bytes: bytes | None, video_bytes: bytes | None) -> dict :
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

    if video_bytes :
        resultat = pipeline_traitement_video(videos_bytes=video_bytes,algorithme="YOLO")
        return resultat




