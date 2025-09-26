"""
Configuración específica para el sistema SmartParking
"""

# Configuración de YOLO y detección de placas
PLATE_DETECTION_CONFIG = {
    'model_path': 'yolov8n.pt',  # Modelo por defecto, se puede entrenar uno específico
    'confidence_threshold': 0.5,  # Umbral de confianza para detecciones
    'image_size': 640,  # Tamaño de imagen para YOLO
    'max_detections': 10,  # Máximo número de detecciones por imagen
}

# Configuración de cámara
CAMERA_CONFIG = {
    'default_index': 0,  # Índice de cámara por defecto
    'resolution_width': 1280,
    'resolution_height': 720,
    'fps': 30,
}

# Patrones de placas por región/país (ajustar según necesidad)
PLATE_PATTERNS = [
    r'^[A-Z]{3}[0-9]{3}$',     # ABC123 (Colombia viejo)
    r'^[A-Z]{3}[0-9]{2}[A-Z]$', # ABC12D (Colombia nuevo)
    r'^[A-Z]{3}[0-9]{4}$',     # ABC1234 (Genérico)
    r'^[A-Z]{2}[0-9]{4}$',     # AB1234 (Genérico)
    r'^[0-9]{3}[A-Z]{3}$',     # 123ABC (Genérico)
]

# Configuración de OCR
OCR_CONFIG = {
    'tesseract_config': '--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    'enable_preprocessing': True,
    'gaussian_blur_kernel': (5, 5),
}

# Configuración de almacenamiento
STORAGE_CONFIG = {
    'detection_images_path': 'detecciones/',
    'plate_crops_path': 'placas_detectadas/',
    'access_photos_path': 'accesos/',
    'max_image_size_mb': 5,  # Tamaño máximo de imagen en MB
}

# Configuración de préstamos
LOAN_CONFIG = {
    'max_loan_duration_days': 30,  # Máximo 30 días de préstamo
    'min_loan_duration_hours': 1,  # Mínimo 1 hora
    'auto_approve_same_day': False,  # Auto-aprobar préstamos del mismo día
    'notification_before_end_hours': 2,  # Notificar 2 horas antes del fin
}

# Roles y permisos
ROLE_PERMISSIONS = {
    'administrador_general': [
        'view_all_vehicles',
        'manage_users',
        'view_all_access_logs',
        'manage_system_config',
        'view_statistics',
    ],
    'vigilante': [
        'register_access',
        'use_camera_detection',
        'view_access_logs',
        'manual_plate_entry',
        'view_statistics',
    ],
    'usuario': [
        'manage_own_vehicles',
        'create_loans',
        'approve_loans',
        'view_own_access_logs',
    ]
}

# Configuración de notificaciones (para futuras implementaciones)
NOTIFICATION_CONFIG = {
    'enable_email_notifications': True,
    'enable_sms_notifications': False,
    'notify_loan_requests': True,
    'notify_access_events': False,
    'notify_suspicious_activity': True,
}

# Configuración de seguridad
SECURITY_CONFIG = {
    'max_failed_detections': 3,  # Máximo fallos de detección antes de alerta
    'suspicious_activity_threshold': 5,  # Número de intentos sospechosos
    'auto_lock_after_hours': 22,  # Hora después de la cual alertar por accesos
    'require_photo_for_manual_entry': True,
}

# Configuración de performance
PERFORMANCE_CONFIG = {
    'enable_gpu_acceleration': True,  # Usar GPU si está disponible
    'batch_processing_size': 4,  # Tamaño de lote para procesamiento
    'cache_detection_results': True,
    'cache_duration_minutes': 30,
}