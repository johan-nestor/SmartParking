"""
Servicio de detección de placas usando YOLO v12
Requiere: pip install ultralytics opencv-python torch
"""

import cv2
import numpy as np
from ultralytics import YOLO
import re
from pathlib import Path
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class PlateDetectionService:
    def __init__(self):
        """
        Inicializa el servicio de detección de placas
        """
        self.model = None
        self.confidence_threshold = 0.5
        self.initialize_model()
    
    def initialize_model(self):
        """
        Inicializa el modelo YOLO para detección de placas
        """
        try:
            # Usar modelo preentrenado de YOLO o entrenar uno específico para placas
            # Por ahora usamos el modelo general, pero se puede entrenar uno específico
            self.model = YOLO('yolov8n.pt')  # Modelo ligero para detección
            logger.info("Modelo YOLO inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar modelo YOLO: {e}")
            raise
    
    def detect_license_plate(self, image_path_or_array, save_result=False):
        """
        Detecta placas en una imagen
        
        Args:
            image_path_or_array: Ruta de la imagen o array numpy
            save_result: Si guardar la imagen con detecciones
            
        Returns:
            dict: {
                'plates_detected': List[str],
                'confidence_scores': List[float],
                'bounding_boxes': List[tuple],
                'processed_image': np.array (si save_result=True)
            }
        """
        try:
            # Cargar imagen
            if isinstance(image_path_or_array, (str, Path)):
                image = cv2.imread(str(image_path_or_array))
            else:
                image = image_path_or_array
            
            if image is None:
                raise ValueError("No se pudo cargar la imagen")
            
            # Ejecutar detección
            results = self.model(image, conf=self.confidence_threshold)
            
            plates_info = {
                'plates_detected': [],
                'confidence_scores': [],
                'bounding_boxes': [],
                'processed_image': None
            }
            
            # Procesar resultados
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extraer región de la placa
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        confidence = float(box.conf[0])
                        
                        if confidence >= self.confidence_threshold:
                            # Extraer región de la placa
                            plate_region = image[y1:y2, x1:x2]
                            
                            # Reconocer texto de la placa
                            plate_text = self.extract_text_from_plate(plate_region)
                            
                            if plate_text:
                                plates_info['plates_detected'].append(plate_text)
                                plates_info['confidence_scores'].append(confidence)
                                plates_info['bounding_boxes'].append((x1, y1, x2, y2))
            
            # Dibujar detecciones si se solicita
            if save_result and plates_info['plates_detected']:
                processed_image = self.draw_detections(
                    image, 
                    plates_info['bounding_boxes'], 
                    plates_info['plates_detected'],
                    plates_info['confidence_scores']
                )
                plates_info['processed_image'] = processed_image
            
            return plates_info
            
        except Exception as e:
            logger.error(f"Error en detección de placas: {e}")
            return {
                'plates_detected': [],
                'confidence_scores': [],
                'bounding_boxes': [],
                'processed_image': None,
                'error': str(e)
            }
    
    def extract_text_from_plate(self, plate_region):
        """
        Extrae texto de una región de placa usando OCR
        
        Args:
            plate_region: Región de la imagen con la placa
            
        Returns:
            str: Texto de la placa limpio
        """
        try:
            # Preprocesamiento de la imagen
            gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
            
            # Aplicar filtros para mejorar OCR
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Usar pytesseract para OCR (requiere instalación separada)
            try:
                import pytesseract
                # Configuración específica para placas
                config = '--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                text = pytesseract.image_to_string(gray, config=config)
                
                # Limpiar texto
                text = re.sub(r'[^A-Z0-9]', '', text.upper())
                
                # Validar formato de placa (ajustar según país/región)
                if self.validate_plate_format(text):
                    return text
                
            except ImportError:
                logger.warning("pytesseract no está instalado, usando reconocimiento básico")
                # Fallback sin OCR externo
                return self.basic_text_recognition(gray)
                
        except Exception as e:
            logger.error(f"Error en extracción de texto: {e}")
            
        return None
    
    def validate_plate_format(self, text):
        """
        Valida si el texto extraído tiene formato de placa válido
        
        Args:
            text: Texto a validar
            
        Returns:
            bool: True si es válido
        """
        if not text or len(text) < 5 or len(text) > 8:
            return False
        
        # Patrones comunes de placas (ajustar según región)
        patterns = [
            r'^[A-Z]{3}[0-9]{3}$',     # ABC123
            r'^[A-Z]{3}[0-9]{4}$',     # ABC1234
            r'^[A-Z]{2}[0-9]{4}$',     # AB1234
            r'^[0-9]{3}[A-Z]{3}$',     # 123ABC
        ]
        
        return any(re.match(pattern, text) for pattern in patterns)
    
    def basic_text_recognition(self, gray_image):
        """
        Reconocimiento básico sin OCR externo (limitado)
        """
        # Implementación básica - en producción usar OCR real
        return None
    
    def draw_detections(self, image, boxes, texts, confidences):
        """
        Dibuja las detecciones en la imagen
        """
        result_image = image.copy()
        
        for (x1, y1, x2, y2), text, conf in zip(boxes, texts, confidences):
            # Dibujar rectángulo
            cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Dibujar texto
            label = f"{text} ({conf:.2f})"
            cv2.putText(result_image, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        return result_image
    
    def process_camera_frame(self, frame):
        """
        Procesa un frame de cámara en tiempo real
        
        Args:
            frame: Frame de la cámara (numpy array)
            
        Returns:
            dict: Información de placas detectadas
        """
        return self.detect_license_plate(frame, save_result=True)


class CameraManager:
    """
    Gestor de cámara para captura en tiempo real
    """
    
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.plate_detector = PlateDetectionService()
    
    def initialize_camera(self):
        """Inicializa la cámara"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                raise ValueError(f"No se pudo abrir la cámara {self.camera_index}")
            
            # Configurar resolución
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            logger.info("Cámara inicializada correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al inicializar cámara: {e}")
            return False
    
    def capture_frame(self):
        """Captura un frame de la cámara"""
        if self.cap is None:
            if not self.initialize_camera():
                return None
        
        ret, frame = self.cap.read()
        if ret:
            return frame
        return None
    
    def detect_plates_in_frame(self):
        """Detecta placas en el frame actual"""
        frame = self.capture_frame()
        if frame is not None:
            return self.plate_detector.process_camera_frame(frame)
        return None
    
    def release(self):
        """Libera recursos de la cámara"""
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()


# Funciones de utilidad para Django
def save_detection_image(image_array, filename):
    """
    Guarda una imagen de detección en MEDIA_ROOT
    """
    try:
        import os
        from django.core.files.base import ContentFile
        from io import BytesIO
        
        # Convertir a bytes
        is_success, buffer = cv2.imencode(".jpg", image_array)
        if is_success:
            image_bytes = BytesIO(buffer)
            return ContentFile(image_bytes.getvalue(), name=filename)
    except Exception as e:
        logger.error(f"Error al guardar imagen: {e}")
    
    return None


def detect_plate_from_upload(image_file):
    """
    Detecta placas desde un archivo subido
    
    Args:
        image_file: Archivo de imagen de Django
        
    Returns:
        dict: Información de detección
    """
    try:
        # Convertir archivo a array numpy
        import numpy as np
        from PIL import Image
        
        # Abrir imagen
        pil_image = Image.open(image_file)
        
        # Convertir a array numpy (OpenCV usa BGR)
        image_array = np.array(pil_image)
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        # Detectar placas
        detector = PlateDetectionService()
        return detector.detect_license_plate(image_array, save_result=True)
        
    except Exception as e:
        logger.error(f"Error al procesar imagen subida: {e}")
        return {
            'plates_detected': [],
            'confidence_scores': [],
            'bounding_boxes': [],
            'processed_image': None,
            'error': str(e)
        }