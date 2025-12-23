from pathlib import Path
import json
import os
import time

from serveur.configuration import CONFIG

"""persistence des documents en requete post 

TODO : gestion persistence, durée suppression vidéo etc .. 
"""



def suppression_logs(duree_suppression_logs: int = 30, duree_suppression_video: int = 7):
    """
    Supprime les fichiers anciens dans les répertoires logs et vidéos.
    
    - duree_suppression_logs : Âge max des logs en jours (défaut 30).
    - duree_suppression_video : Âge max des vidéos en jours (défaut 7).
    
    Parcourt les répertoires, supprime les fichiers plus anciens que la durée spécifiée.
    Retourne un résumé des suppressions.
    """
    config = CONFIG.path_config
    maintenant = time.time()
    seuil_logs = maintenant - (duree_suppression_logs * 24 * 60 * 60)  
    seuil_videos = maintenant - (duree_suppression_video * 24 * 60 * 60)
    
    resume = {
        "logs_supprimes": 0,
        "videos_supprimes": 0,
        "erreurs": []
    }
    
    try:
        for fichier in config.logs_path.iterdir():
            if fichier.is_file() and fichier.stat().st_mtime < seuil_logs: #st_mtime attribut derniere modif ficheir
                fichier.unlink()  #suppression fichier 
                resume["logs_supprimes"] += 1
                print(f"Supprimé log: {fichier}")
    except Exception as e:
        resume["erreurs"].append(f"Erreur logs: {str(e)}")
    
    #idem pour video
    try:
        for fichier in config.videos_path.iterdir():
            if fichier.is_file() and fichier.stat().st_mtime < seuil_videos:
                fichier.unlink()
                resume["videos_supprimes"] += 1
                print(f"Supprimé vidéo: {fichier}")
    except Exception as e:
        resume["erreurs"].append(f"Erreur vidéos: {str(e)}")
    
    return resume