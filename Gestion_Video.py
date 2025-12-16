import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
import os
from uuid import uuid4

async def enregistrer_video(file: UploadFile):
    UPLOAD_DIR = "videos"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une vidéo")

    extension = os.path.splitext(file.filename)[1]
    filename = f"{uuid4()}{extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        while chunk := await file.read(1024*1024):  # lit 1 Mo à la fois
            buffer.write(chunk)

    return file_path
