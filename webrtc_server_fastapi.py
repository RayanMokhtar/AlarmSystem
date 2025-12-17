"""
FastAPI WebRTC Server (Raspberry Pi)
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from uvicorn import run as uvicorn_run

from webrtc_core import SharedPiCamera2, WebRTCManager, ArduinoController

APP_HOST = os.getenv("HOST", "0.0.0.0")
APP_PORT = int(os.getenv("PORT", "8090"))
WIDTH = int(os.getenv("WIDTH", "1280"))
HEIGHT = int(os.getenv("HEIGHT", "720"))
FPS = float(os.getenv("FPS", "20"))
DEBUG = os.getenv("DEBUG", "0") == "1"

WEBRTC_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>WebRTC Live</title>
<style>
html,body{margin:0;height:100%;background:#000}
video{width:100vw;height:100vh;object-fit:contain}
</style>
</head>
<body>
<video id="v" autoplay playsinline muted></video>
<script>
(async () => {
  const pc = new RTCPeerConnection({ iceServers: [] });
  pc.addTransceiver('video', { direction: 'recvonly' });
  pc.ontrack = e => v.srcObject = e.streams[0];

  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);

  const r = await fetch('/offer', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(offer)
  });
  const answer = await r.json();
  await pc.setRemoteDescription(answer);
})();
</script>
</body>
</html>
"""

camera = SharedPiCamera2(WIDTH, HEIGHT, FPS)
manager = WebRTCManager(camera, FPS, DEBUG)
arduino = ArduinoController(port="/dev/ttyACM0", baudrate=9600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    await manager.close_all()
    arduino.close()


app = FastAPI(title="WebRTC Picamera2 Server", lifespan=lifespan)

DIRECTION_MAP = {
	"right": "3",  # était "down"
	"left":  "4",  # était "up"
	"down":  "1",  # était "right"
	"up":    "2"   # était "left"
}

@app.get("/")
async def root():
    return {"message": "Visit /webrtc"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/webrtc", response_class=HTMLResponse)
async def webrtc_page():
    return WEBRTC_HTML

@app.post("/offer")
async def offer(request: Request):
    try:
        params = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    sdp = params.get("sdp")
    type_ = params.get("type")
    if not sdp or not type_:
        raise HTTPException(400, "Missing sdp/type")

    remote_ip = request.client.host if request.client else "unknown"
    pc = await manager.create_peer_connection(remote_ip)
    return await manager.handle_offer(pc, sdp, type_)
    
@app.post("/control/{direction}")
async def control(direction: str, request: Request):
	remote_ip = request.client.host if request.client else "unknown"

	direction = direction.lower()
	if direction not in DIRECTION_MAP:
		raise HTTPException(status_code=400, detail="Invalid direction")

	char = DIRECTION_MAP[direction]
	arduino.send(char)

	print(
		f">>> COMMANDE {direction.upper()} ({char}) envoyée à l'Arduino depuis {remote_ip}",
		flush=True
	)

	return {
		"status": "ok",
		"direction": direction,
		"char": char
	}


@app.websocket("/ws/control")
async def websocket_control(websocket: WebSocket):
	"""WebSocket endpoint pour les commandes de contrôle en temps réel"""
	await websocket.accept()
	remote_ip = websocket.client.host if websocket.client else "unknown"
	print(f">>> WebSocket connecté depuis {remote_ip}", flush=True)
	
	try:
		while True:
			# Recevoir la direction depuis le client
			data = await websocket.receive_text()
			direction = data.lower().strip()
			
			if direction in DIRECTION_MAP:
				char = DIRECTION_MAP[direction]
				arduino.send(char)
				print(f">>> WS COMMANDE {direction.upper()} ({char}) depuis {remote_ip}", flush=True)
				
				# Envoyer une confirmation
				await websocket.send_text(f"ok:{direction}")
			else:
				await websocket.send_text(f"error:invalid_direction")
				
	except WebSocketDisconnect:
		print(f">>> WebSocket déconnecté depuis {remote_ip}", flush=True)
	except Exception as e:
		print(f">>> Erreur WebSocket depuis {remote_ip}: {e}", flush=True)
		try:
			await websocket.close()
		except:
			pass


if __name__ == "__main__":
    uvicorn_run(app, host=APP_HOST, port=APP_PORT, log_level="info")
