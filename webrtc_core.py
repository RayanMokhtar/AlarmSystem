"""
WebRTC Core Module
Gère la webcam, les tracks vidéo, et les peer connections WebRTC
"""
import asyncio
import time
from fractions import Fraction
from threading import Lock

import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration
from aiortc.mediastreams import VideoStreamTrack
from av import VideoFrame


class SharedWebcam:
    """Gestion partagée de la webcam avec compteur d'utilisateurs"""
    
    def __init__(self, camera_index: int, width: int, height: int, fps: float):
        self._lock = Lock()
        self._cap = None
        self._active_users = 0
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps

    def acquire(self):
        """Ouvre la caméra si nécessaire et incrémente le compteur"""
        with self._lock:
            self._active_users += 1
            if self._cap is None or not self._cap.isOpened():
                cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                cap.set(cv2.CAP_PROP_FPS, self.fps)
                self._cap = cap

    def release(self):
        """Décrémente le compteur et ferme la caméra si plus d'utilisateurs"""
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
        """Lit une frame de la caméra"""
        with self._lock:
            if self._cap is None or not self._cap.isOpened():
                return None
            ok, frame = self._cap.read()
            if not ok:
                return None
            return frame


class WebcamVideoTrack(VideoStreamTrack):
    """Track vidéo WebRTC utilisant la webcam partagée"""
    
    def __init__(self, webcam: SharedWebcam, fps: float, debug: bool = False):
        super().__init__()
        self._webcam = webcam
        self._fps = fps
        self._debug = debug
        self._started = False
        self._frame_index = 0

    async def recv(self):
        """Envoie une frame vidéo encodée en RTP"""
        if not self._started:
            self._webcam.acquire()
            self._started = True
            if self._debug:
                print("WebcamVideoTrack started", flush=True)

        # Pacing pour respecter le framerate
        await asyncio.sleep(1.0 / max(self._fps, 1.0))

        # Lecture de la frame
        frame = self._webcam.read()
        if frame is None:
            await asyncio.sleep(0.05)
            frame = self._webcam.read()
        if frame is None:
            # Fallback: frame noire
            frame = np.zeros((self._webcam.height, self._webcam.width, 3), dtype=np.uint8)

        # Conversion en VideoFrame
        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")

        # Horloge RTP 90kHz
        self._frame_index += 1
        if self._frame_index == 1 and self._debug:
            print("WebcamVideoTrack sending frames", flush=True)
        
        video_frame.pts = int(self._frame_index * (90000 / max(self._fps, 1.0)))
        video_frame.time_base = Fraction(1, 90000)
        return video_frame

    def stop(self):
        """Arrête le track et libère la webcam"""
        try:
            super().stop()
        finally:
            if self._started:
                self._webcam.release()
                self._started = False


class WebRTCManager:
    """Gestionnaire des peer connections WebRTC"""
    
    def __init__(self, webcam: SharedWebcam, fps: float, debug: bool = False):
        self.webcam = webcam
        self.fps = fps
        self.debug = debug
        self.pcs = set()
        self.pcs_by_remote = {}

    async def create_peer_connection(self, remote_ip: str) -> RTCPeerConnection:
        """Crée une nouvelle peer connection pour un client"""
        # Fermer l'ancienne connexion si elle existe
        old_pc = self.pcs_by_remote.get(remote_ip)
        if old_pc is not None:
            try:
                await old_pc.close()
            except Exception:
                pass
            self.pcs.discard(old_pc)
            self.pcs_by_remote.pop(remote_ip, None)

        # Créer nouvelle peer connection sans STUN (LAN seulement)
        config = RTCConfiguration(iceServers=[])
        pc = RTCPeerConnection(configuration=config)
        self.pcs.add(pc)
        self.pcs_by_remote[remote_ip] = pc

        # Logging des candidats ICE
        if self.debug:
            @pc.on("icecandidate")
            def on_icecandidate(candidate):
                if candidate:
                    print(f"ICE candidate (server): {candidate.candidate}", flush=True)

        # Ajouter le track vidéo
        video_track = WebcamVideoTrack(self.webcam, self.fps, self.debug)
        pc.addTrack(video_track)

        # Gestion des événements de connexion
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            if self.debug:
                print(f"pc.connectionState={pc.connectionState}", flush=True)
            if pc.connectionState in ("failed", "closed", "disconnected"):
                await pc.close()
                self.pcs.discard(pc)
                if self.pcs_by_remote.get(remote_ip) is pc:
                    self.pcs_by_remote.pop(remote_ip, None)

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            if self.debug:
                print(f"pc.iceConnectionState={pc.iceConnectionState}", flush=True)

        return pc

    async def handle_offer(self, pc: RTCPeerConnection, offer_sdp: str, offer_type: str) -> dict:
        """Traite une offre WebRTC et retourne la réponse SDP"""
        # Définir la description distante
        offer_desc = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
        await pc.setRemoteDescription(offer_desc)

        # Créer la réponse
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        # Attendre la fin du gathering ICE
        await self._wait_for_ice_gathering_complete(pc)

        if self.debug:
            print(f"answer ready iceGatheringState={pc.iceGatheringState} pcs={len(self.pcs)}", flush=True)

        return {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }

    async def _wait_for_ice_gathering_complete(self, pc: RTCPeerConnection, timeout: float = 3.0):
        """Attend que le gathering ICE soit terminé"""
        if pc.iceGatheringState == "complete":
            return

        fut = asyncio.get_event_loop().create_future()

        @pc.on("icegatheringstatechange")
        def _on_ice_gathering_state_change():
            if pc.iceGatheringState == "complete" and not fut.done():
                fut.set_result(None)

        try:
            await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            return

    async def close_all(self):
        """Ferme toutes les peer connections"""
        coros = [pc.close() for pc in self.pcs]
        if coros:
            await asyncio.gather(*coros, return_exceptions=True)
        self.pcs.clear()
        self.pcs_by_remote.clear()
