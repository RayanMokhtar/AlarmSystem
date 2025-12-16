# Launch FastAPI WebRTC Server on Windows
# Equivalent to: python -m uvicorn webrtc_server_fastapi:app --host 0.0.0.0 --port 8090 --reload

param(
    [int]$Port = 8090,
    [string]$Host = "0.0.0.0",
    [switch]$NoReload
)

$env:HOST = $Host
$env:PORT = $Port

$args = @("webrtc_server_fastapi:app", "--host", $Host, "--port", $Port)
if (-not $NoReload) {
    $args += "--reload"
}

Write-Host "Starting FastAPI WebRTC Server..."
Write-Host "Host: $Host, Port: $Port"
Write-Host ""

& python -m uvicorn @args
