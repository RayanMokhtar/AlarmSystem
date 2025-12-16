# Script pour exposer le serveur WebRTC sur internet via ngrok
# Prérequis: ngrok installé et dans le PATH (ou ngrok.exe dans ce dossier)

param(
    [int]$Port = 8090
)

$VenvPath = ".\.venv\Scripts\python.exe"
$ServerScript = "webrtc_server.py"

# Vérifie ngrok
$ngrokCmd = $null
if (Get-Command ngrok -ErrorAction SilentlyContinue) {
    $ngrokCmd = "ngrok"
} elseif (Test-Path ".\ngrok.exe") {
    $ngrokCmd = ".\ngrok.exe"
} else {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "ERREUR: ngrok n'est pas installé" -ForegroundColor Red
    Write-Host ""
    Write-Host "1. Téléchargez ngrok: https://ngrok.com/download" -ForegroundColor Yellow
    Write-Host "2. Extrayez ngrok.exe dans ce dossier" -ForegroundColor Yellow
    Write-Host "   OU ajoutez-le au PATH système" -ForegroundColor Yellow
    Write-Host "============================================" -ForegroundColor Red
    exit 1
}

# Vérifie le venv
if (-not (Test-Path $VenvPath)) {
    Write-Host "Erreur: Le venv n'existe pas. Créez-le avec: python -m venv .venv" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Lancement serveur WebRTC + tunnel ngrok" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Lance le serveur en arrière-plan
Write-Host "[1/2] Démarrage du serveur WebRTC sur le port $Port..." -ForegroundColor Green
$serverJob = Start-Process -FilePath $VenvPath -ArgumentList $ServerScript -PassThru -WindowStyle Minimized
$env:PORT = $Port

# Attend que le serveur démarre
Start-Sleep -Seconds 2

# Lance ngrok
Write-Host "[2/2] Démarrage du tunnel ngrok..." -ForegroundColor Green
Write-Host ""
Write-Host "Une fois ngrok démarré, copiez l'URL 'Forwarding' (https://xxxx.ngrok.io)" -ForegroundColor Yellow
Write-Host "et utilisez-la pour accéder au flux depuis n'importe où:" -ForegroundColor Yellow
Write-Host "  https://xxxx.ngrok.io/webrtc" -ForegroundColor White
Write-Host ""

try {
    & $ngrokCmd http $Port
} finally {
    # Arrête le serveur quand ngrok se ferme
    if ($serverJob -and -not $serverJob.HasExited) {
        Stop-Process -Id $serverJob.Id -Force -ErrorAction SilentlyContinue
    }
}
