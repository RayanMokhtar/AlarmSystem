# FastAPI WebRTC Server Migration

## Qu'est-ce qui a changé ?

La version précédente utilisait **aiohttp** pour le serveur HTTP. La nouvelle version utilise **FastAPI + uvicorn**, qui offre:

✅ **Meilleure DX** - Décoration simple avec `@app.get`, `@app.post`
✅ **Documentation auto** - Swagger UI disponible sur `/docs`
✅ **Type hints** - Meilleure validation et IDE support
✅ **Performance** - Uvicorn est plus rapide qu'aiohttp
✅ **Async native** - Même support des coroutines asynchrones

## Installation

```powershell
pip install -r requirements.txt
```

## Lancement

### Option 1: Python script
```powershell
python webrtc_server_fastapi.py
```

### Option 2: PowerShell script (recommandé)
```powershell
.\run_fastapi.ps1
```

Ou avec options:
```powershell
.\run_fastapi.ps1 -Port 8090 -Host 0.0.0.0
.\run_fastapi.ps1 -NoReload  # Sans hot-reload
```

### Option 3: Commande directe
```powershell
python -m uvicorn webrtc_server_fastapi:app --host 0.0.0.0 --port 8090 --reload
```

## Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Info serveur |
| `/health` | GET | Health check |
| `/webrtc` | GET | Page WebRTC HTML |
| `/offer` | POST | Signaling WebRTC (SDP negotiation) |
| `/control/{direction}` | POST | Commandes directionnelles (up/down/left/right) |
| `/docs` | GET | **Swagger UI** (bonus FastAPI) |
| `/redoc` | GET | **ReDoc** (bonus FastAPI) |

## Variables d'environnement

```powershell
$env:HOST = "0.0.0.0"      # Host (défaut: 0.0.0.0)
$env:PORT = 8090            # Port (défaut: 8090)
$env:CAMERA_INDEX = 0       # Index caméra (défaut: 0)
$env:WIDTH = 1280           # Largeur (défaut: 1280)
$env:HEIGHT = 720           # Hauteur (défaut: 720)
$env:FPS = 20               # FPS (défaut: 20)
$env:DEBUG = "1"            # Debug mode (défaut: "0")
```

## Comparaison aiohttp ↔ FastAPI

### aiohttp (ancien)
```python
from aiohttp import web

async def health(_request):
    return web.json_response({"status": "ok"})

app = web.Application()
app.router.add_get("/health", health)
web.run_app(app, host=APP_HOST, port=APP_PORT)
```

### FastAPI (nouveau)
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

# Lancer avec uvicorn
```

**Plus simple et plus lisible !**

## Accès à la webcam

### Depuis le PC local
- WebRTC: http://127.0.0.1:8090/webrtc
- MJPEG (port 8080): http://127.0.0.1:8080/mobile

### Depuis un téléphone sur le LAN
- WebRTC: http://192.168.X.X:8090/webrtc
- MJPEG (port 8080): http://192.168.X.X:8080/mobile

### Documentation interactive
- Swagger: http://127.0.0.1:8090/docs
- ReDoc: http://127.0.0.1:8090/redoc

## Que reste inchangé ?

- ✅ Logique WebRTC (aiortc, candidats ICE)
- ✅ Streaming vidéo via WebcamVideoTrack
- ✅ Endpoints de contrôle (`/control/{direction}`)
- ✅ Configuration par variables d'environnement

## Fichiers

- `webrtc_server_fastapi.py` - Serveur FastAPI principal
- `webrtc_server.py` - Ancienne version (aiohttp) - conservée pour référence
- `server.py` - Serveur MJPEG (Flask) - inchangé
- `run_fastapi.ps1` - Script de lancement PowerShell
- `run_fastapi.py` - Script de lancement Python

Bonne migration ! 🚀
