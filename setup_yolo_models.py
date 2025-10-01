#!/usr/bin/env python3
"""
Script para instalar y configurar modelos de detección de placas
Ejecutar: python setup_yolo_models.py
"""

import os
import sys
import subprocess
import urllib.request
from pathlib import Path

def install_dependencies():
    """Instala las dependencias necesarias"""
    print("📦 Instalando dependencias...")
    dependencies = [
        'ultralytics',
        'easyocr', 
        'opencv-python',
        'torch',
        'torchvision',
        'Pillow',
        'numpy'
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                         check=True, capture_output=True)
            print(f"✅ {dep} instalado")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando {dep}: {e}")
            return False
    
    return True

def download_models():
    """Descarga modelos pre-entrenados"""
    print("\n🤖 Descargando modelos YOLO...")
    
    # Crear directorio para modelos
    models_dir = Path("vehiculos/models")
    models_dir.mkdir(exist_ok=True)
    
    models = {
        'yolov8n.pt': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt',
        'yolov8s.pt': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt'
    }
    
    for model_name, url in models.items():
        model_path = models_dir / model_name
        if model_path.exists():
            print(f"⏭️  {model_name} ya existe")
            continue
            
        try:
            print(f"⬇️  Descargando {model_name}...")
            urllib.request.urlretrieve(url, model_path)
            print(f"✅ {model_name} descargado")
        except Exception as e:
            print(f"❌ Error descargando {model_name}: {e}")

def setup_license_plate_model():
    """Configura modelo específico para placas"""
    print("\n🚗 Configurando modelo de placas...")
    
    try:
        from ultralytics import YOLO
        
        # Cargar modelo base
        model = YOLO('yolov8n.pt')
        print("✅ Modelo YOLO cargado correctamente")
        
        # Probar EasyOCR
        import easyocr
        reader = easyocr.Reader(['en', 'es'], gpu=False)
        print("✅ EasyOCR inicializado correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando modelos: {e}")
        return False

def test_camera_access():
    """Prueba acceso a la cámara"""
    print("\n📹 Probando acceso a cámara...")
    
    try:
        import cv2
        
        # Probar diferentes índices de cámara
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"✅ Cámara encontrada en índice {i}")
                    cap.release()
                    return True
                cap.release()
        
        print("⚠️  No se encontró cámara accesible")
        return False
        
    except Exception as e:
        print(f"❌ Error probando cámara: {e}")
        return False

def create_test_script():
    """Crea script de prueba"""
    print("\n🧪 Creando script de prueba...")
    
    test_script = """
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Script de prueba para detección de placas
Ejecutar: python test_plate_detection.py
\"\"\"

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SamrtParking.settings')
sys.path.append('.')
django.setup()

from vehiculos.plate_detection import PlateDetectionService, detect_plate_from_upload
from django.core.files.uploadedfile import SimpleUploadedFile

def test_detection():
    print("🧪 Probando detección de placas...")
    
    try:
        # Inicializar servicio
        detector = PlateDetectionService()
        print("✅ Detector inicializado")
        
        # Crear imagen de prueba (opcional)
        print("📝 Para probar con imagen real:")
        print("   1. Guarda una imagen con placa como 'test_plate.jpg'")
        print("   2. Ejecuta: detector.detect_license_plate('test_plate.jpg')")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

if __name__ == "__main__":
    print("🚗 Sistema de Detección de Placas - Prueba")
    print("=" * 50)
    
    if test_detection():
        print("\\n✅ Sistema listo para usar")
    else:
        print("\\n❌ Hay problemas con la configuración")
"""
    
    with open('test_plate_detection.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ Script de prueba creado: test_plate_detection.py")

def main():
    print("🚗 Configuración de Sistema de Detección de Placas")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('manage.py'):
        print("❌ Error: Ejecuta este script desde el directorio raíz del proyecto Django")
        return
    
    success = True
    
    # 1. Instalar dependencias
    if not install_dependencies():
        print("❌ Fallo en instalación de dependencias")
        success = False
    
    # 2. Descargar modelos
    download_models()
    
    # 3. Configurar modelos
    if not setup_license_plate_model():
        print("❌ Fallo en configuración de modelos")
        success = False
    
    # 4. Probar cámara (opcional)
    test_camera_access()
    
    # 5. Crear script de prueba
    create_test_script()
    
    # Resumen final
    print("\n" + "=" * 60)
    if success:
        print("✅ CONFIGURACIÓN COMPLETADA")
        print("\n📋 Próximos pasos:")
        print("   1. Ejecuta: python manage.py runserver")
        print("   2. Ve a: http://127.0.0.1:8000/vehiculos/vigilante/camara/")
        print("   3. Prueba la detección de placas")
        print("\n💡 Consejos:")
        print("   - Usa Chrome o Firefox para mejor compatibilidad")
        print("   - Permite acceso a cámara cuando se solicite")
        print("   - La primera detección puede tardar más (carga de modelos)")
    else:
        print("❌ CONFIGURACIÓN INCOMPLETA")
        print("\n🔧 Revisa los errores anteriores y:")
        print("   - Verifica tu conexión a internet")
        print("   - Instala Python 3.8+ si es necesario")
        print("   - Ejecuta: pip install --upgrade pip")

if __name__ == "__main__":
    main()