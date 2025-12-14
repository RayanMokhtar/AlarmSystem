@echo off
REM Script de lancement simplifié du serveur WebRTC
REM Utilisation: double-clique ou ouvre le terminal et tapez: run.bat

setlocal enabledelayedexpansion

REM Configuration
set PORT=8090
set VENV_PATH=.venv\Scripts\python.exe
set SERVER_SCRIPT=webrtc_server.py

REM Vérifie si le venv existe
if not exist "!VENV_PATH!" (
    echo Erreur: Le venv n'existe pas à !VENV_PATH!
    echo Crée d'abord le venv avec: python -m venv .venv
    pause
    exit /b 1
)

REM Vérifie si le script serveur existe
if not exist "!SERVER_SCRIPT!" (
    echo Erreur: Le script !SERVER_SCRIPT! n'existe pas dans le dossier courant.
    pause
    exit /b 1
)

REM Tue tout process écoutant sur le port 8090 (optionnel)
echo Nettoyage du port %PORT%...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do (
    taskkill /PID %%a /F 2>nul
)
timeout /t 1 /nobreak >nul

REM Lance le serveur
echo.
echo Démarrage du serveur WebRTC sur http://0.0.0.0:%PORT%
echo Pour accéder: http://127.0.0.1:%PORT%/webrtc (PC) ou http://IP_DU_PC:%PORT%/webrtc (téléphone)
echo.
set PORT=%PORT%
"!VENV_PATH!" "!SERVER_SCRIPT!"

pause
