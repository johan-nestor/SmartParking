"""
Servicio de detección de placas usando YOLO + EasyOCR
Requiere: pip install ultralytics easyocr opencv-python torch
"""

import cv2
import numpy as np
from ultralytics import YOLO
import easyocr
import re
from pathlib import Path
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)


class PlateDetectionService:
    def __init__(self):
        """
        Inicializa el servicio de detección de placas
        """
        self.model = None
        self.ocr_reader = None
        self.confidence_threshold = 0.25
        self.initialize_model()
        self.initialize_ocr()
    
    def initialize_model(self):
        """
        Inicializa el modelo YOLO para detección de placas
        """
        try:
            # Usar modelo YOLOv8 optimizado
            self.model = YOLO('yolov8n.pt')  # Modelo ligero para detección
            logger.info("Modelo YOLO inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar modelo YOLO: {e}")
            raise
    
    def initialize_ocr(self):
        """
        Inicializa EasyOCR para reconocimiento de texto
        """
        try:
            # Inicializar EasyOCR con idiomas español e inglés
            self.ocr_reader = easyocr.Reader(['en', 'es'], gpu=False)  # gpu=True si tienes GPU
            logger.info("EasyOCR inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar EasyOCR: {e}")
            self.ocr_reader = None
    
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
            
            # Ejecutar detección (buscar vehículos primero)
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
                        class_id = int(box.cls[0]) if box.cls is not None else -1
                        
                        # Filtrar solo vehículos (car=2, truck=7, bus=5, motorcycle=3 en COCO)
                        if class_id in [2, 3, 5, 7]:  # Solo vehículos
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                            confidence = float(box.conf[0])
                            
                            if confidence >= self.confidence_threshold:
                                # Buscar placa en la región del vehículo
                                vehicle_region = image[y1:y2, x1:x2]
                                plate_results = self.find_license_plate_in_vehicle(vehicle_region)
                                
                                if plate_results:
                                    for plate_info in plate_results:
                                        # Ajustar coordenadas al frame completo
                                        px1, py1, px2, py2 = plate_info['bbox']
                                        global_x1 = x1 + px1
                                        global_y1 = y1 + py1
                                        global_x2 = x1 + px2
                                        global_y2 = y1 + py2
                                        
                                        plates_info['plates_detected'].append(plate_info['text'])
                                        plates_info['confidence_scores'].append(plate_info['confidence'])
                                        plates_info['bounding_boxes'].append((global_x1, global_y1, global_x2, global_y2))
            
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
    
    def find_license_plate_in_vehicle(self, vehicle_region):
        """
        Busca placas específicamente en la región de un vehículo
        
        Args:
            vehicle_region: Región de la imagen con el vehículo
            
        Returns:
            list: Lista de placas encontradas con sus datos
        """
        try:
            plates_found = []
            
            # Preprocesar imagen para mejorar detección
            processed_region = self.preprocess_for_plate_detection(vehicle_region)
            
            # Usar EasyOCR para encontrar texto
            if self.ocr_reader is not None:
                results = self.ocr_reader.readtext(processed_region)
                
                for (bbox, text, confidence) in results:
                    # Limpiar y validar texto
                    clean_text = self.clean_plate_text(text)
                    
                    if self.validate_plate_format(clean_text) and confidence > 0.3:
                        # Convertir bbox a formato estándar
                        points = np.array(bbox)
                        x1, y1 = np.min(points, axis=0).astype(int)
                        x2, y2 = np.max(points, axis=0).astype(int)
                        
                        plates_found.append({
                            'text': clean_text,
                            'confidence': confidence,
                            'bbox': (x1, y1, x2, y2)
                        })
            
            return plates_found
            
        except Exception as e:
            logger.error(f"Error en búsqueda de placa en vehículo: {e}")
            return []
    
    def preprocess_for_plate_detection(self, image):
        """
        Preprocesa imagen para mejorar detección de placas
        """
        try:
            # Convertir a escala de grises
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Aplicar filtros
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Mejorar contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            return gray
            
        except Exception as e:
            logger.error(f"Error en preprocesamiento: {e}")
            return image
    
    def clean_plate_text(self, text):
        """
        Limpia el texto extraído de una placa
        """
        # Eliminar espacios y caracteres especiales
        clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Correcciones comunes OCR
        corrections = {
            '0': 'O',  # En contexto de letras
            '1': 'I',  # En contexto de letras
            '5': 'S',  # En contexto de letras
        }
        
        # Aplicar correcciones contextuales
        if len(clean_text) >= 6:
            # Primeras 3 posiciones suelen ser letras
            for i in range(min(3, len(clean_text))):
                if clean_text[i] in corrections:
                    clean_text = clean_text[:i] + corrections[clean_text[i]] + clean_text[i+1:]
        
        return clean_text
    
    def validate_plate_format(self, text):
        """
        Valida si el texto extraído tiene formato de placa válido
        Incluye formatos de diferentes países latinoamericanos
        
        Args:
            text: Texto a validar
            
        Returns:
            bool: True si es válido
        """
        if not text or len(text) < 5 or len(text) > 8:
            return False
        
        # Patrones comunes de placas (diferentes países)
        patterns = [
            # Formato argentino/chileno
            r'^[A-Z]{3}[0-9]{3}$',     # ABC123
            r'^[A-Z]{2}[0-9]{3}[A-Z]{2}$',  # AB123CD
            
            # Formato mexicano
            r'^[A-Z]{3}[0-9]{4}$',     # ABC1234
            r'^[0-9]{3}[A-Z]{3}$',     # 123ABC
            
            # Formato colombiano
            r'^[A-Z]{3}[0-9]{2}[A-Z]$',   # ABC12D
            
            # Formato peruano
            r'^[A-Z]{2}[0-9]{4}$',     # AB1234
            r'^[0-9]{4}[A-Z]{2}$',     # 1234AB
            
            # Formato brasileiro
            r'^[A-Z]{3}[0-9]{4}$',     # ABC1234
            r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$', # Mercosul ABC1D23
            
            # Formato general
            r'^[A-Z0-9]{6,8}$',       # Cualquier combinación de 6-8 caracteres
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
    NOTA: Para uso web, la cámara se maneja desde JavaScript/WebRTC
    Esta clase es para procesamiento del lado del servidor
    """
    
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.plate_detector = PlateDetectionService()
    
    def initialize_camera(self):
        """Inicializa la cámara del sistema (no navegador)"""
        try:
            # Intentar diferentes backends de OpenCV
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
            
            for backend in backends:
                try:
                    self.cap = cv2.VideoCapture(self.camera_index, backend)
                    if self.cap.isOpened():
                        # Configurar propiedades
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                        self.cap.set(cv2.CAP_PROP_FPS, 30)
                        
                        # Probar captura
                        ret, frame = self.cap.read()
                        if ret and frame is not None:
                            logger.info(f"Cámara inicializada con backend {backend}")
                            return True
                        else:
                            self.cap.release()
                except Exception as e:
                    if self.cap:
                        self.cap.release()
                    continue
            
            raise ValueError("No se pudo inicializar ninguna cámara")
            
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
    
    def detect_from_camera(self):
        """
        Método para detección desde cámara del sistema
        Para cámara web usar detect_plate_from_upload con imagen del navegador
        """
        try:
            if not self.cap or not self.cap.isOpened():
                if not self.initialize_camera():
                    return {
                        'success': False,
                        'error': 'No se pudo acceder a la cámara del sistema',
                        'plates_detected': []
                    }
            
            frame = self.capture_frame()
            if frame is not None:
                result = self.plate_detector.detect_license_plate(frame)
                return {
                    'success': True,
                    'plates_detected': result['plates_detected'],
                    'confidence_scores': result['confidence_scores']
                }
            else:
                return {
                    'success': False,
                    'error': 'No se pudo capturar imagen de la cámara',
                    'plates_detected': []
                }
                
        except Exception as e:
            logger.error(f"Error en detección desde cámara: {e}")
            return {
                'success': False,
                'error': str(e),
                'plates_detected': []
            }
    
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