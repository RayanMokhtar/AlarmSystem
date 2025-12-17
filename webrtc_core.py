"""
WebRTC Core Module (Raspberry Pi / Picamera2)
- Caméra partagée
- VideoTrack WebRTC
- WebRTCManager
"""

import asyncio
import time
import threading
from fractions import Fraction
from threading import Lock

import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration
from aiortc.mediastreams import VideoStreamTrack
from av import VideoFrame
from picamera2 import Picamera2

import serial


class SharedPiCamera2:
    """Caméra Picamera2 partagée avec gestion forcée de libération"""

    def __init__(self, width: int, height: int, fps: float):
        self.width = width
        self.height = height
        self.fps = fps

        self._lock = Lock()
        self._active_users = 0
        self._picam2 = None
        self._started = False

    def force_release(self):
        """Force la libération complète de la caméra (pour reconnexion)"""
        with self._lock:
            if self._picam2 is not None:
                try:
                    self._picam2.stop()
                except Exception:
                    pass
                try:
                    self._picam2.close()
                except Exception:
                    pass
                self._picam2 = None
            self._started = False
            self._active_users = 0

    def acquire(self):
        with self._lock:
            self._active_users += 1
            if self._started and self._picam2 is not None:
                return  # déjà démarrée

            # Si la caméra existe mais n'est pas started, on la nettoie
            if self._picam2 is not None:
                try:
                    self._picam2.close()
                except Exception:
                    pass
                self._picam2 = None

            self._picam2 = Picamera2()
            config = self._picam2.create_video_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"}
            )
            self._picam2.configure(config)
            self._picam2.start()
            self._started = True

    def release(self):
        with self._lock:
            self._active_users = max(0, self._active_users - 1)
            if self._active_users == 0 and self._started:
                try:
                    self._picam2.stop()
                except Exception:
                    pass
                try:
                    self._picam2.close()
                except Exception:
                    pass
                self._picam2 = None
                self._started = False

    def read(self):
        with self._lock:
            if not self._started or self._picam2 is None:
                return None
            try:
                return self._picam2.capture_array()
            except Exception:
                return None


class PiCamera2VideoTrack(VideoStreamTrack):
    """Track vidéo WebRTC basé sur Picamera2"""

    def __init__(self, cam: SharedPiCamera2, fps: float, debug: bool = False):
        super().__init__()
        self.cam = cam
        self.fps = max(fps, 1.0)
        self.debug = debug
        self._started = False
        self._frame_index = 0

    async def recv(self):
        if not self._started:
            self.cam.acquire()
            self._started = True
            if self.debug:
                print("PiCamera2VideoTrack started", flush=True)

        await asyncio.sleep(1.0 / self.fps)

        frame = self.cam.read()
        if frame is None:
            frame = np.zeros((self.cam.height, self.cam.width, 3), dtype=np.uint8)

        frame = np.ascontiguousarray(frame)
        vf = VideoFrame.from_ndarray(frame, format="rgb24")

        self._frame_index += 1
        vf.pts = int(self._frame_index * (90000 / self.fps))
        vf.time_base = Fraction(1, 90000)
        return vf

    def stop(self):
        try:
            super().stop()
        finally:
            if self._started:
                self.cam.release()
                self._started = False

class WebRTCManager:
    """1 seule connexion vidéo à la fois (recommandé sur Picamera2)"""

    def __init__(self, cam: SharedPiCamera2, fps: float, debug: bool = False):
        self.cam = cam
        self.fps = fps
        self.debug = debug

        self._lock = asyncio.Lock()
        self.current_pc: RTCPeerConnection | None = None
        self.current_track: PiCamera2VideoTrack | None = None

    async def create_peer_connection(self, remote_ip: str) -> RTCPeerConnection:
        async with self._lock:
            if self.debug:
                print(f"Nouvelle connexion depuis {remote_ip}, fermeture de l'ancienne...", flush=True)

            # ✅ Stop propre de l'ancienne connexion AVANT de recréer
            if self.current_track is not None:
                try:
                    self.current_track.stop()
                except Exception:
                    pass
                self.current_track = None

            if self.current_pc is not None:
                try:
                    await self.current_pc.close()
                except Exception:
                    pass
                self.current_pc = None

            # 🔥 Force la libération complète de la caméra avant reconnexion
            self.cam.force_release()

            # Pause pour laisser libcamera se libérer complètement
            await asyncio.sleep(0.3)

            pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=[]))
            track = PiCamera2VideoTrack(self.cam, self.fps, self.debug)
            pc.addTrack(track)

            self.current_pc = pc
            self.current_track = track

            @pc.on("connectionstatechange")
            async def on_state_change():
                if self.debug:
                    print(f"pc.connectionState={pc.connectionState}", flush=True)
                if pc.connectionState in ("failed", "closed", "disconnected"):
                    async with self._lock:
                        if self.current_track is track:
                            try:
                                track.stop()
                            except Exception:
                                pass
                            self.current_track = None
                        if self.current_pc is pc:
                            try:
                                await pc.close()
                            except Exception:
                                pass
                            self.current_pc = None

            return pc

    async def handle_offer(self, pc: RTCPeerConnection, sdp: str, type_: str) -> dict:
        offer = RTCSessionDescription(sdp=sdp, type=type_)
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

    async def close_all(self):
        async with self._lock:
            if self.current_track is not None:
                try:
                    self.current_track.stop()
                except Exception:
                    pass
                self.current_track = None
            if self.current_pc is not None:
                try:
                    await self.current_pc.close()
                except Exception:
                    pass
                self.current_pc = None
            # Force la libération complète de la caméra
            self.cam.force_release()

class ArduinoController:
    def __init__(self, port="/dev/ttyACM0", baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self._lock = threading.Lock()
        self.ser = None
        self.connect()

    def connect(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        time.sleep(2)  # reset Arduino

    def send(self, char: str):
        if not self.ser or not self.ser.is_open:
            return

        with self._lock:
            self.ser.write(char.encode("ascii"))
            self.ser.flush()

    def close(self):
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
