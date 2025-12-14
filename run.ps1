# Script de lancement simplifié du serveur WebRTC
# Utilisation: .\run.ps1

param(
    [int]$Port = 8090,
    [switch]$Debug = $false
)

$VenvPath = ".\.venv\Scripts\python.exe"
$ServerScript = "webrtc_server.py"

# Vérifie le venv
if (-not (Test-Path $VenvPath)) {
    Write-Host "Erreur: Le venv n'existe pas à $VenvPath" -ForegroundColor Red
    Write-Host "Crée d'abord le venv avec: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Vérifie le script serveur
if (-not (Test-Path $ServerScript)) {
    Write-Host "Erreur: Le script $ServerScript n'existe pas dans le dossier courant." -ForegroundColor Red
    exit 1
}

# Tue les anciens process sur le port
Write-Host "Nettoyage du port $Port..." -ForegroundColor Cyan
$conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($conns) {
    $conns.OwningProcess | Sort-Object -Unique | ForEach-Object {
        try {
            Stop-Process -Id $_ -Force -ErrorAction Stop
            Write-Host "Arrêt du process $_" -ForegroundColor Yellow
        } catch { }
    }
    Start-Sleep -Milliseconds 300
}

# Lance le serveur
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Démarrage du serveur WebRTC" -ForegroundColor Green
Write-Host "Port: http://0.0.0.0:$Port" -ForegroundColor Green
Write-Host "Accès PC: http://127.0.0.1:$Port/webrtc" -ForegroundColor Green
Write-Host "Accès téléphone: http://IP_DU_PC:$Port/webrtc" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$env:PORT = $Port
if ($Debug) {
    $env:DEBUG = "1"
}

& $VenvPath $ServerScript
