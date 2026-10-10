import time
import threading
import logging
from typing import Optional, Tuple
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

logger = logging.getLogger("RTSPWorker")

class RTSPStreamWorker:
    """
    Background worker asinkron untuk menangkap frame dari Industrial IP Camera (RTSP / HTTP MJPEG)
    dengan frame-buffer non-blocking (zero lag).
    """

    def __init__(self, rtsp_url: Optional[str] = None):
        self.rtsp_url = rtsp_url
        self.is_running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.latest_frame: Optional[np.ndarray] = None
        self.lock = threading.Lock()
        self.last_update_ts = 0.0
        self.connected = False

    def connect(self, rtsp_url: str):
        """Memulai thread penangkap stream RTSP."""
        if cv2 is None:
            logger.warning("[RTSP Worker] OpenCV tidak terpasang, mode simulasi RTSP aktif.")
            self.connected = True
            return

        self.disconnect()
        self.rtsp_url = rtsp_url
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info(f"[RTSP Worker] Connecting to stream: {rtsp_url}")

    def disconnect(self):
        """Menghentikan thread RTSP."""
        self.is_running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.5)
        self.connected = False
        self.latest_frame = None
        logger.info("[RTSP Worker] Disconnected from stream.")

    def _capture_loop(self):
        """Loop internal dengan frame buffer dropping untuk mencegah latency buffering."""
        if cv2 is None or not self.rtsp_url:
            return

        cap = cv2.VideoCapture(self.rtsp_url)
        # Kurangi buffer capture internal
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            logger.error(f"[RTSP Worker] Gagal membuka stream: {self.rtsp_url}")
            self.connected = False
            return

        self.connected = True
        logger.info("[RTSP Worker] Stream berhasil terhubung.")

        while self.is_running:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            with self.lock:
                self.latest_frame = frame
                self.last_update_ts = time.time()

        cap.release()
        self.connected = False

    def get_latest_frame_jpeg(self) -> Optional[bytes]:
        """Mengembalikan frame terbaru yang di-encode ke JPEG."""
        if not self.connected:
            return None

        with self.lock:
            if self.latest_frame is None:
                return None
            frame_copy = self.latest_frame.copy()

        if cv2 is not None:
            ret, jpeg = cv2.imencode('.jpg', frame_copy, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if ret:
                return jpeg.tobytes()
        return None

# Singleton global instance
global_rtsp_worker = RTSPStreamWorker()
