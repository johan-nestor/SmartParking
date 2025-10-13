import cv2
from threading import Thread

class VideoCamera:
    def __init__(self):
        # Usa la cámara 
        self.video = cv2.VideoCapture(0)
        (self.grabbed, self.frame) = self.video.read()
        self.running = True

        # Hilo para capturar los frames continuamente
        Thread(target=self.update, args=()).start()

    def update(self):
        while self.running:
            self.grabbed, self.frame = self.video.read()

    def get_frame(self):
        ret, jpeg = cv2.imencode('.jpg', self.frame)
        return jpeg.tobytes()

    def __del__(self):
        self.running = False
        self.video.release()
