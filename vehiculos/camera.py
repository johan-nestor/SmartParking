import cv2
import time
import os
from threading import Thread
from django.conf import settings


def _try_open(indices=(0, 1, 2), backends=(cv2.CAP_DSHOW, cv2.CAP_MSMF, 0)):
    """Try to open a camera using several indices and backends. Returns (video_capture, index, backend) or (None, None, None)."""
    for backend in backends:
        for idx in indices:
            try:
                if backend and backend != 0:
                    cap = cv2.VideoCapture(1)
                else:
                    cap = cv2.VideoCapture(idx)

                # small delay to allow backend init
                time.sleep(0.2)
                if cap is None:
                    continue
                ok, _ = cap.read()
                if ok:
                    return cap, idx, backend
                else:
                    cap.release()
            except Exception:
                # backend might not be supported; try next
                try:
                    if 'cap' in locals() and cap is not None:
                        cap.release()
                except Exception:
                    pass
                continue
    return None, None, None

class VideoCamera:
    def __init__(self):
        # If a CAMERA_SOURCE is configured (env or Django setting), try it first
        cam_source = os.environ.get('CAMERA_SOURCE') or getattr(settings, 'CAMERA_SOURCE', None)
        self.source_used = None
        self.video = None
        self.index = None
        self.backend = None

        if cam_source:
            try:
                print(f"[VideoCamera] trying CAMERA_SOURCE={cam_source}")
                cap = cv2.VideoCapture(cam_source)
                time.sleep(0.3)
                ok, _ = cap.read()
                if ok:
                    self.video = cap
                    self.index = cam_source
                    self.backend = 'URL'
                    self.source_used = cam_source
                else:
                    try:
                        cap.release()
                    except Exception:
                        pass
                    print(f"[VideoCamera] CAMERA_SOURCE opened but no frames - it may not be the direct stream endpoint")
            except Exception as e:
                print(f"[VideoCamera] error opening CAMERA_SOURCE: {e}")

        # If no valid CAM source, fall back to local device probing
        if self.video is None:
            # Try common camera indices and Windows backends (CAP_DSHOW is often more stable)
            self.video, self.index, self.backend = _try_open(indices=range(0, 4), backends=(cv2.CAP_DSHOW, cv2.CAP_MSMF, 0))

        # Log what was selected (helpful for debugging)
        try:
            print(f"[VideoCamera] opened video: index={self.index} backend={self.backend} video_obj={'yes' if self.video is not None else 'no'} source_used={getattr(self,'source_used', None)}")
        except Exception:
            pass

        if self.video is None:
            # No camera available: create placeholder frame
            self.grabbed = False
            # small black image
            import numpy as np

            self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
            self.running = False
        else:
            self.grabbed, self.frame = self.video.read()
            self.running = True
            # Hilo para capturar los frames continuamente
            Thread(target=self.update, args=(), daemon=True).start()

    def update(self):
        while self.running:
            try:
                self.grabbed, self.frame = self.video.read()
                if not self.grabbed:
                    # small backoff to avoid busy loop if camera disconnects
                    time.sleep(0.1)
            except Exception:
                # On error, stop running and release
                self.running = False
                break

    def get_frame(self):
        # Ensure we always return a valid jpeg bytes
        try:
            ret, jpeg = cv2.imencode('.jpg', self.frame)
            if ret:
                return jpeg.tobytes()
        except Exception:
            pass

        # Fallback: return a tiny 1x1 black jpeg
        import numpy as np

        black = np.zeros((2, 2, 3), dtype=np.uint8)
        ret, jpeg = cv2.imencode('.jpg', black)
        return jpeg.tobytes()

    def __del__(self):
        try:
            self.running = False
            if hasattr(self, 'video') and self.video is not None:
                self.video.release()
        except Exception:
            pass
