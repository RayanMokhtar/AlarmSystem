"""
HomeSecure WebRTC Server - FastAPI Edition
Serveur vidéo WebRTC pour surveillance caméra avec contrôles directionnels
"""
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from uvicorn import run as uvicorn_run

from webrtc_core import SharedWebcam, WebRTCManager


# Configuration
APP_HOST = os.getenv("HOST", "0.0.0.0")
APP_PORT = int(os.getenv("PORT", "8090"))
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
WIDTH = int(os.getenv("WIDTH", "1280"))
HEIGHT = int(os.getenv("HEIGHT", "720"))
FPS = float(os.getenv("FPS", "20"))
DEBUG = os.getenv("DEBUG", "0") == "1"


# HTML WebRTC Client
WEBRTC_HTML = """<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>Live Feed (WebRTC)</title>
    <style>
      html,body{height:100%;margin:0;background:#000;overflow:hidden}
      .wrap{position:fixed;inset:0;display:flex;align-items:center;justify-content:center}
      video{width:100vw;height:100vh;object-fit:contain;background:#000}
      .hud{position:fixed;left:12px;right:12px;bottom:12px;color:#fff;font:12px system-ui,Segoe UI,Roboto,Arial,sans-serif;
           background:rgba(0,0,0,.55);border:1px solid rgba(255,255,255,.12);border-radius:12px;padding:10px 12px}
      .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;justify-content:space-between}
      button{appearance:none;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.08);color:#fff;padding:8px 10px;border-radius:10px}
      code{background:rgba(0,0,0,.25);padding:2px 6px;border-radius:8px;border:1px solid rgba(255,255,255,.12)}
    </style>
  </head>
  <body>
    <div class="wrap">
      <video id="v" autoplay playsinline muted></video>
    </div>
    <div class="hud">
      <div class="row">
        <div>
          Mode: <strong>WebRTC</strong> · Signaling: <code>/offer</code>
        </div>
        <div>
          <button id="btn">Reconnexion</button>
        </div>
      </div>
      <div id="status" style="margin-top:8px;color:#bbb">Initialisation…</div>
    </div>

    <script>
      const statusEl = document.getElementById('status');
      const videoEl = document.getElementById('v');
      const btn = document.getElementById('btn');

      let pc;

      function setStatus(msg){ statusEl.textContent = msg; }

      window.addEventListener('error', (e) => {
        setStatus('Erreur JS: ' + (e.message || 'inconnue'));
      });
      window.addEventListener('unhandledrejection', (e) => {
        const msg = (e && e.reason && e.reason.message) ? e.reason.message : String(e.reason || e);
        setStatus('Promise rejetée: ' + msg);
      });

      async function waitIceComplete(pc, timeoutMs = 2500) {
        if (pc.iceGatheringState === 'complete') return;
        await new Promise((resolve) => {
          const t = setTimeout(() => {
            try { pc.onicegatheringstatechange = null; } catch(e) {}
            resolve();
          }, timeoutMs);
          pc.onicegatheringstatechange = () => {
            if (pc.iceGatheringState === 'complete') {
              clearTimeout(t);
              resolve();
            }
          };
        });
      }

      async function start() {
        if (pc) {
          try { pc.close(); } catch(e) {}
        }

        if (!window.RTCPeerConnection) {
          throw new Error('WebRTC non supporté par ce WebView (RTCPeerConnection manquant)');
        }

        setStatus('Connexion au serveur…');
        // NO STUN (mode test) - force uniquement candidats locaux / host
        // Utilise: iceServers: []
        pc = new RTCPeerConnection({
          iceServers: [],
          iceCandidatePoolSize: 10,
          iceTransportPolicy: 'all' // Accepte tous types de candidats
        });

        // Filtre les candidats ICE pour éviter mDNS (.local)
        let candidateCount = 0;
        let hasRealCandidate = false;
        pc.onicecandidate = (ev) => {
          if (ev.candidate) {
            const c = ev.candidate.candidate;
            console.log('ICE candidate (client):', c);
            
            // Détecte si c'est un candidat mDNS (.local)
            if (c.includes('.local')) {
              console.warn('⚠️ Candidat mDNS ignoré (Chrome obfuscation)');
            } else {
              hasRealCandidate = true;
              candidateCount++;
            }
          } else {
            console.log('ICE gathering complete (client) - ' + candidateCount + ' candidats utilisables');
            if (!hasRealCandidate) {
              console.error('❌ AUCUN candidat utilisable! Tous sont mDNS (.local)');
              setStatus('Erreur: Chrome obfusque les IPs. Utilise 127.0.0.1 ou désactive mDNS dans chrome://flags');
            }
          }
        };

        pc.ontrack = (ev) => {
          setStatus('Flux reçu');
          const [stream] = ev.streams;
          videoEl.srcObject = stream;
          const p = videoEl.play();
          if (p && typeof p.catch === 'function') {
            p.catch(err => setStatus('Lecture bloquée: ' + (err && err.message ? err.message : err)));
          }
        };

        pc.oniceconnectionstatechange = () => {
          setStatus('ICE: ' + pc.iceConnectionState);
        };

        // We are recv-only
        pc.addTransceiver('video', { direction: 'recvonly' });

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        setStatus('Préparation ICE…');
        await waitIceComplete(pc);

        setStatus('Négociation SDP…');
        const offerUrl = new URL('/offer', window.location.href);
        const resp = await fetch(offerUrl.toString(), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sdp: pc.localDescription.sdp, type: pc.localDescription.type })
        });
        if (!resp.ok) {
          const text = await resp.text();
          throw new Error('Offer failed: ' + resp.status + ' ' + text);
        }
        const answer = await resp.json();
        await pc.setRemoteDescription(answer);

        setStatus('Connecté, attente du flux…');
      }

      // À la rotation / reload WebView, on ferme pour libérer vite le serveur.
      window.addEventListener('pagehide', () => {
        try { if (pc) pc.close(); } catch(e) {}
      });
      window.addEventListener('beforeunload', () => {
        try { if (pc) pc.close(); } catch(e) {}
      });

      btn.addEventListener('click', () => start().catch(e => setStatus('Erreur: ' + e.message)));

      start().catch(e => setStatus('Erreur: ' + e.message));
    </script>
  </body>
</html>"""


# Initialize shared camera and WebRTC manager
webcam = SharedWebcam(
    camera_index=CAMERA_INDEX,
    width=WIDTH,
    height=HEIGHT,
    fps=FPS
)

manager = WebRTCManager(
    webcam=webcam,
    fps=FPS,
    debug=DEBUG
)


# Create FastAPI app
app = FastAPI(title="HomeSecure WebRTC Server")


@app.get("/")
async def root():
    """Redirect to /webrtc"""
    return {"message": "WebRTC Server running. Visit /webrtc for live feed."}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/webrtc", response_class=HTMLResponse)
async def webrtc_page():
    """Serve WebRTC HTML page"""
    return WEBRTC_HTML


@app.post("/offer")
async def offer(request: Request):
    """WebRTC signaling endpoint - receive offer and send answer"""
    try:
        params = await request.json()
    except Exception as e:
        return {"error": f"invalid json: {e}"}, 400

    offer_sdp = params.get("sdp")
    offer_type = params.get("type")
    if not offer_sdp or not offer_type:
        return {"error": "missing sdp/type"}, 400

    remote_ip = request.client.host or "unknown"
    
    # Create peer connection and handle offer
    pc = await manager.create_peer_connection(remote_ip)
    answer = await manager.handle_offer(pc, offer_sdp, offer_type)
    
    return answer


@app.post("/control/{direction}")
async def control_direction(direction: str, request: Request):
    """Endpoint pour recevoir les commandes directionnelles"""
    remote_ip = request.client.host or "unknown"
    
    print(f">>> Commande reçue: {direction.upper()} from {remote_ip}", flush=True)
    
    # Ici tu pourras ajouter le code pour contrôler un servo moteur, etc.
    # Pour l'instant on fait juste un print
    
    return {"status": "ok", "direction": direction}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    await manager.close_all()


if __name__ == "__main__":
    uvicorn_run(
        app,
        host=APP_HOST,
        port=APP_PORT,
        log_level="info",
    )
