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

from configuration import CONFIG



def load_image_from_bytes(image_bytes , afficher = True):
    image = Image.open(io.BytesIO(image_bytes))
    if afficher : 
        image.show()
    image.close()

def image_to_file(image_bytes , nom_fichier : Optional[str] , extension=".png"):
    if nom_fichier is None:
        nom_fichier = f"image_{datetime.datetime.now()}{extension}"
    fichier_sortie = f"{CONFIG.path_config.images_path}/{nom_fichier}"
    image = Image.open(io.BytesIO(image_bytes))
    image.save(fichier_sortie)
    image.close()



def traiter_image(image_path : str): 
    """traiter l'image selon un algorithme précis """
    pass