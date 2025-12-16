# Service caméra (mock PC)

Objectif: exposer la webcam du PC en HTTP (MJPEG) pour simuler un flux "Raspberry".

## Prérequis
- Python 3.10+ recommandé

## Installation
```powershell
cd "c:\Users\darkf\Desktop\service caméra"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancer
```powershell
python server.py
```

Si le port 8080 est indisponible sur ta machine Windows, lance par exemple en 8090:
```powershell
$env:PORT=8090; python server.py
```

## Accès
- Page de preview: `http://IP_DU_PC:8080/`
- Page mobile plein écran: `http://IP_DU_PC:8080/mobile`
- Flux MJPEG: `http://IP_DU_PC:8080/video_feed`
- Santé: `http://IP_DU_PC:8080/health`

## Mode WebRTC (optionnel, faible latence)
Le WebRTC est plus proche d'un "vrai" live feed (latence plus faible), mais il demande plus de dépendances.

Installation (dans le même venv):
```powershell
pip install -r requirements.txt
```

Lancer en WebRTC:
```powershell
$env:PORT=8090; python webrtc_server.py
```

Accès WebRTC:
- Page WebRTC: `http://IP_DU_PC:8090/webrtc`
- Signaling: `POST http://IP_DU_PC:8090/offer`

Si tu changes le port (ex: 8090), adapte les URLs.

## Variables d'environnement (optionnel)
- `PORT` (défaut 8080)
- `CAMERA_INDEX` (défaut 0)
- `WIDTH` (défaut 1280)
- `HEIGHT` (défaut 720)
- `FPS` (défaut 15)
- `JPEG_QUALITY` (défaut 80)

## Notes
- Le téléphone et le PC doivent être sur le même Wi‑Fi.
- Windows Firewall peut bloquer le port 8080; autoriser Python/port si besoin.
- La webcam du PC est ouverte uniquement quand au moins un client consulte `/video_feed` (elle se libère à la déconnexion du dernier client).

## Accès depuis internet (ngrok)

Si tu veux accéder au flux **depuis n'importe quel réseau** (pas juste le réseau local), utilise ngrok.

### Installation ngrok
1. Télécharge ngrok: https://ngrok.com/download
2. Extrais `ngrok.exe` dans ce dossier (ou ajoute-le au PATH)
3. (Optionnel) Crée un compte gratuit sur ngrok.com et configure ton authtoken:
   ```powershell
   ngrok config add-authtoken TON_TOKEN
   ```

### Lancement avec ngrok
Double-clique sur `run_public.bat` ou exécute:
```powershell
.\run_public.ps1
```

ngrok affichera une URL publique (ex: `https://abc123.ngrok.io`).
Utilise cette URL pour accéder au flux depuis n'importe où:
```
https://abc123.ngrok.io/webrtc
```

### Lancement manuel
```powershell
# Terminal 1: Lance le serveur
$env:PORT=8090; .\.venv\Scripts\python.exe webrtc_server.py

# Terminal 2: Lance ngrok
ngrok http 8090
```

## Commandes rapides

Lancement local (même réseau):
```powershell
cd "C:\Users\darkf\Desktop\service caméra"
.\run.bat
```

Lancement public (internet via ngrok):
```powershell
cd "C:\Users\darkf\Desktop\service caméra"
.\run_public.bat
```
