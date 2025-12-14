import asyncio
import json
import os
import sys
import time
from fractions import Fraction
from threading import Lock

import cv2
import numpy as np
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import VideoStreamTrack
from av import VideoFrame


APP_HOST = os.getenv("HOST", "0.0.0.0")
APP_PORT = int(os.getenv("PORT", "8090"))
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
WIDTH = int(os.getenv("WIDTH", "1280"))
HEIGHT = int(os.getenv("HEIGHT", "720"))
FPS = float(os.getenv("FPS", "20"))
DEBUG = os.getenv("DEBUG", "0") == "1"


def _debug(msg: str):
  if DEBUG:
    print(msg, flush=True)


class SharedWebcam:
    def __init__(self):
        self._lock = Lock()
        self._cap = None
        self._active_users = 0

    def acquire(self):
        with self._lock:
            self._active_users += 1
            if self._cap is None or not self._cap.isOpened():
                cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
                cap.set(cv2.CAP_PROP_FPS, FPS)
                self._cap = cap

    def release(self):
        with self._lock:
            self._active_users = max(0, self._active_users - 1)
            if self._active_users == 0:
                if self._cap is not None:
                    try:
                        self._cap.release()
                    except Exception:
                        pass
                self._cap = None

    def read(self):
        with self._lock:
            if self._cap is None or not self._cap.isOpened():
                return None
            ok, frame = self._cap.read()
            if not ok:
                return None
            return frame


shared_webcam = SharedWebcam()


class WebcamVideoTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self._started = False
        self._t0 = time.time()
        self._frame_index = 0

    async def recv(self):
        if not self._started:
            shared_webcam.acquire()
            self._started = True
        _debug("WebcamVideoTrack started")

        # Target pacing
        await asyncio.sleep(1.0 / max(FPS, 1.0))

        frame = shared_webcam.read()
        if frame is None:
            # Provide a tiny delay and retry
            await asyncio.sleep(0.05)
            frame = shared_webcam.read()
        if frame is None:
            # Empty frame; create a black frame fallback
            frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")

        # 90kHz clock is typical in RTP
        self._frame_index += 1
        if self._frame_index == 1:
            _debug("WebcamVideoTrack sending frames")
        video_frame.pts = int(self._frame_index * (90000 / max(FPS, 1.0)))
        video_frame.time_base = Fraction(1, 90000)
        return video_frame

    def stop(self):
        try:
            super().stop()
        finally:
            if self._started:
                shared_webcam.release()
                self._started = False


WEbrtc_HTML = """<!doctype html>
<html lang=\"fr\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\" />
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
    <div class=\"wrap\">
      <video id=\"v\" autoplay playsinline muted></video>
    </div>
    <div class=\"hud\">
      <div class=\"row\">
        <div>
          Mode: <strong>WebRTC</strong> · Signaling: <code>/offer</code>
        </div>
        <div>
          <button id=\"btn\">Reconnexion</button>
        </div>
      </div>
      <div id=\"status\" style=\"margin-top:8px;color:#bbb\">Initialisation…</div>
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
        pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });

        pc.ontrack = (ev) => {
          setStatus('Flux reçu');
          const [stream] = ev.streams;
          videoEl.srcObject = stream;
          // Certains WebView nécessitent un play() explicite même si autoplay+muted.
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


pcs = set()

# Une seule session par IP (évite l'accumulation lors des reload/rotations)
pcs_by_remote = {}


def _log(msg: str):
    print(msg, flush=True)


async def _wait_for_ice_gathering_complete(pc: RTCPeerConnection, timeout: float = 3.0):
    if pc.iceGatheringState == "complete":
        return

    fut: asyncio.Future[None] = asyncio.get_event_loop().create_future()

    @pc.on("icegatheringstatechange")
    def _on_ice_gathering_state_change():
        if pc.iceGatheringState == "complete" and not fut.done():
            fut.set_result(None)

    try:
        await asyncio.wait_for(fut, timeout=timeout)
    except asyncio.TimeoutError:
        # Not fatal; we just return the SDP we have.
        return


async def health(_request):
    return web.json_response({"status": "ok"})


async def favicon(_request):
    return web.Response(status=204)


async def root(_request):
    raise web.HTTPFound("/webrtc")


async def webrtc_page(_request):
    return web.Response(text=WEbrtc_HTML, content_type="text/html")


async def offer(request: web.Request):
    try:
        params = await request.json()
    except Exception as e:
        return web.json_response({"error": f"invalid json: {e}"}, status=400)

    offer_sdp = params.get("sdp")
    offer_type = params.get("type")
    if not offer_sdp or not offer_type:
        return web.json_response({"error": "missing sdp/type"}, status=400)

    _log(f"/offer from {request.remote} len(sdp)={len(offer_sdp)}")

    remote = request.remote or "unknown"
    old_pc = pcs_by_remote.get(remote)
    if old_pc is not None:
      try:
        await old_pc.close()
      except Exception:
        pass
      pcs.discard(old_pc)
      pcs_by_remote.pop(remote, None)

    pc = RTCPeerConnection()
    pcs.add(pc)
    pcs_by_remote[remote] = pc

    # Add webcam track
    pc.addTrack(WebcamVideoTrack())

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        _log(f"pc.connectionState={pc.connectionState}")
        if pc.connectionState in ("failed", "closed", "disconnected"):
            await pc.close()
            pcs.discard(pc)
        if pcs_by_remote.get(remote) is pc:
          pcs_by_remote.pop(remote, None)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
      _log(f"pc.iceConnectionState={pc.iceConnectionState}")

    offer_desc = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
    await pc.setRemoteDescription(offer_desc)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    await _wait_for_ice_gathering_complete(pc)

    _log(f"answer ready iceGatheringState={pc.iceGatheringState} pcs={len(pcs)}")

    return web.json_response({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})


async def on_shutdown(app: web.Application):
    coros = [pc.close() for pc in pcs]
    if coros:
        await asyncio.gather(*coros, return_exceptions=True)
    pcs.clear()
    pcs_by_remote.clear()


def main():
    app = web.Application()
    app.router.add_get("/", root)
    app.router.add_get("/health", health)
    app.router.add_get("/favicon.ico", favicon)
    app.router.add_get("/webrtc", webrtc_page)
    app.router.add_get("/webrtc/", webrtc_page)
    app.router.add_post("/offer", offer)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host=APP_HOST, port=APP_PORT)


if __name__ == "__main__":
    main()
