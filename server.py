import os
import time
from threading import Lock
#MJPEG/snapshots HTTP server

import cv2
from flask import Flask, Response, jsonify, render_template_string


APP_HOST = os.getenv("HOST", "0.0.0.0")
APP_PORT = int(os.getenv("PORT", "8080"))
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
WIDTH = int(os.getenv("WIDTH", "1280"))
HEIGHT = int(os.getenv("HEIGHT", "720"))
FPS = float(os.getenv("FPS", "15"))
JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "80"))


class Camera:
    def __init__(self):
        self._lock = Lock()
        self._cap = None
        self._last_open_attempt = 0.0

    def _open(self):
        # On Windows, CAP_DSHOW is often more reliable.
        cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, FPS)
        return cap

    def close(self):
        with self._lock:
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception:
                    pass
            self._cap = None

    def get_frame_jpeg(self) -> bytes | None:
        with self._lock:
            if self._cap is None or not self._cap.isOpened():
                now = time.time()
                # Avoid tight retry loops if camera is busy/unavailable.
                if now - self._last_open_attempt < 1.0:
                    return None
                self._last_open_attempt = now
                self._cap = self._open()

            ok, frame = self._cap.read()
            if not ok:
                # Force re-open on next request
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
                return None

            encode_ok, buf = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY],
            )
            if not encode_ok:
                return None
            return buf.tobytes()


app = Flask(__name__)
camera = Camera()

# Track active MJPEG clients to stop the camera when nobody is watching
_stream_state_lock = Lock()
_active_stream_clients = 0


INDEX_HTML = """
<!doctype html>
<html lang=\"fr\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Live Feed (Mock PC Camera)</title>
    <style>
      body{font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;margin:0;background:#0b0b0b;color:#fff}
      header{padding:14px 16px;background:#111;border-bottom:1px solid #222}
      .wrap{padding:16px}
      .card{background:#111;border:1px solid #222;border-radius:14px;overflow:hidden}
      img{display:block;width:100%;height:auto;background:#000}
      .meta{font-size:12px;color:#bbb;padding:10px 12px;display:flex;gap:12px;flex-wrap:wrap}
      code{background:#0b0b0b;border:1px solid #222;border-radius:8px;padding:2px 6px}
    </style>
  </head>
  <body>
    <header>
      <strong>Live Feed</strong> <span style=\"color:#bbb\">(Mock webcam PC → HTTP MJPEG)</span>
    </header>
    <div class=\"wrap\">
      <div class=\"card\">
        <img src=\"/video_feed\" alt=\"live feed\" />
        <div class=\"meta\">
          <div>Endpoint: <code>/video_feed</code></div>
          <div>Résolution: <code>{{ width }}x{{ height }}</code></div>
          <div>FPS cible: <code>{{ fps }}</code></div>
        </div>
      </div>
    </div>
  </body>
</html>
"""


MOBILE_HTML = """
<!doctype html>
<html lang=\"fr\">
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\" />
        <title>Live Feed</title>
        <style>
            html,body{height:100%;margin:0;background:#000;overflow:hidden}
            .wrap{position:fixed;inset:0;display:flex;align-items:center;justify-content:center}
            img{display:block;width:100%;height:auto;max-height:100vh;background:#000}
        </style>
    </head>
    <body>
        <div class=\"wrap\">
            <img src=\"/video_feed\" alt=\"live feed\" />
        </div>
    </body>
</html>
"""


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/favicon.ico")
def favicon():
    # Avoid noisy 404s in clients (WebView/browsers may request it)
    return ("", 204)


@app.get("/")
def index():
    return render_template_string(INDEX_HTML, width=WIDTH, height=HEIGHT, fps=FPS)


@app.get("/mobile")
def mobile():
    return render_template_string(MOBILE_HTML)


@app.get("/mobile/")
def mobile_slash():
    return render_template_string(MOBILE_HTML)


def mjpeg_stream():
    global _active_stream_clients

    with _stream_state_lock:
        _active_stream_clients += 1

    frame_interval = 1.0 / max(FPS, 1.0)
    try:
        while True:
            frame = camera.get_frame_jpeg()
            if frame is None:
                time.sleep(0.1)
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(frame)).encode("ascii") + b"\r\n\r\n" + frame + b"\r\n"
            )
            time.sleep(frame_interval)
    finally:
        with _stream_state_lock:
            _active_stream_clients = max(0, _active_stream_clients - 1)
            should_close = (_active_stream_clients == 0)

        if should_close:
            camera.close()


@app.get("/video_feed")
def video_feed():
    return Response(mjpeg_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.get("/video_feed/")
def video_feed_slash():
    return Response(mjpeg_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.post("/control/<direction>")
def control_direction(direction):
    """Endpoint pour recevoir les commandes directionnelles"""
    from flask import request
    remote = request.remote_addr or "unknown"
    
    print(f"[CONTROL] Direction '{direction}' from {remote}", flush=True)
    print(f">>> Commande reçue: {direction.upper()}", flush=True)
    
    # Ici tu pourras ajouter le code pour contrôler un servo moteur, etc.
    # Pour l'instant on fait juste un print
    
    return jsonify({"status": "ok", "direction": direction})


if __name__ == "__main__":
    # Accessible depuis le téléphone sur le LAN: http://IP_DU_PC:8080/
    app.run(host=APP_HOST, port=APP_PORT, threaded=True, debug=False)
