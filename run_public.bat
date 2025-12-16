@echo off
REM Script pour exposer le serveur WebRTC sur internet via ngrok
REM Prérequis: ngrok installé et dans le PATH (ou dans ce dossier)

setlocal enabledelayedexpansion

set PORT=8090
set VENV_PATH=.venv\Scripts\python.exe
set SERVER_SCRIPT=webrtc_server.py

REM Vérifie si ngrok est disponible
where ngrok >nul 2>&1
if %ERRORLEVEL% neq 0 (
    if exist "ngrok.exe" (
        set NGROK_CMD=.\ngrok.exe
    ) else (
        echo.
        echo ============================================
        echo ERREUR: ngrok n'est pas installe ou introuvable
        echo.
        echo Telechargez ngrok depuis: https://ngrok.com/download
        echo Puis placez ngrok.exe dans ce dossier ou ajoutez-le au PATH.
        echo ============================================
        pause
        exit /b 1
    )
) else (
    set NGROK_CMD=ngrok
)

REM Vérifie le venv
if not exist "!VENV_PATH!" (
    echo Erreur: Le venv n'existe pas. Creez-le avec: python -m venv .venv
    pause
    exit /b 1
)

echo.
echo ============================================
echo Lancement du serveur WebRTC + tunnel ngrok
echo ============================================
echo.

REM Lance le serveur Python en arrière-plan
echo [1/2] Demarrage du serveur WebRTC sur le port %PORT%...
start "WebRTC Server" cmd /c "set PORT=%PORT% && !VENV_PATH! !SERVER_SCRIPT!"

REM Attend que le serveur démarre
timeout /t 2 /nobreak >nul

REM Lance ngrok
echo [2/2] Demarrage du tunnel ngrok...
echo.
echo Une fois ngrok demarre, copiez l'URL "Forwarding" (https://xxxx.ngrok.io)
echo et utilisez-la pour acceder au flux depuis n'importe ou:
echo   https://xxxx.ngrok.io/webrtc
echo.
%NGROK_CMD% http %PORT%
