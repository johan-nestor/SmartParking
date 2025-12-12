
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from usuarios.views import role_required

import cv2
import easyocr
from ultralytics import YOLO
from collections import deque, Counter
import re
import time
import os
import json
from pathlib import Path
import logging

from vehiculos.models import Vehiculo, RegistroAcceso
from usuarios.models import Perfil

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt


logger = logging.getLogger(__name__)

# ==================== CONFIGURACIÓN ====================
MODEL_PATH = "best.pt"
CONF_THRESHOLD = 0.28
reader = easyocr.Reader(['en'], gpu=True)

# Estado global
ocr_buffer = deque(maxlen=15)
ultima_placa_confirmada = None
last_confirm_time = 0
detected_count = 0

# Archivo JSON temporal
DETECCIONES_FILE = Path("placas_detectadas.json")

# ==================== NORMALIZACIÓN PERÚ ====================
def normalize_plate(s: str) -> str:
    s = re.sub(r'[^A-Z0-9]', '', s.upper())
    s = s.replace('I','T').replace('1','T').replace('L','T')
    s = s.replace('2','Z').replace('7','Z')
    s = s.replace('O','0').replace('Q','0')
    s = s.replace('B','8')
    if len(s) >= 6:
        return f"{s[:3]}-{s[3:6]}"
    return s

# ==================== CARGA DEL MODELO ====================
model = YOLO(MODEL_PATH)
try:
    model.to("cuda")
    print("GPU (CUDA) activada para YOLO")
except:
    print("CUDA no disponible, usando CPU")
    model.to("cpu")

# ==================== GENERADOR DE VIDEO CON REGISTRO AUTOMÁTICO ====================
def gen_video(request):
    global ultima_placa_confirmada, last_confirm_time, detected_count
    vigilante = request.user

    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        vis = frame.copy()
        results = model(frame, conf=CONF_THRESHOLD, verbose=False, imgsz=640)

        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            crop = frame[y1:y2, x1:x2]
            if crop.shape[0] < 40 or crop.shape[1] < 100:
                continue

            try:
                gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                ocr_results = reader.readtext(gray, detail=1)
                if not ocr_results:
                    ocr_results = reader.readtext(crop, detail=1)

                height = crop.shape[0]
                upper_texts = [
                    (text, conf) for (bbox, text, conf) in ocr_results
                    if ((bbox[0][1] + bbox[2][1]) / 2) < height*0.6 and conf > 0.3
                ]
                if not upper_texts:
                    continue

                best_text = max(upper_texts, key=lambda x: x[1])[0]
                placa = normalize_plate(best_text)

                if len(placa) == 7 and placa[3] == '-' and placa[:3].isalpha() and placa[4:].isdigit():
                    cv2.rectangle(vis, (x1, y1), (x2, y2), (0,255,0), 4)
                    cv2.putText(vis, placa, (x1, y1-20), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0,255,0), 4)
                    ocr_buffer.append(placa)

            except Exception as e:
                logger.error(f"Error OCR: {e}")
                continue

        # CONFIRMACIÓN + REGISTRO AUTOMÁTICO
        if ocr_buffer and time.time() - last_confirm_time > 0.8:
            placa_final, count = Counter(ocr_buffer).most_common(1)[0]
            if count >= 4 and placa_final != ultima_placa_confirmada:
                ultima_placa_confirmada = placa_final
                last_confirm_time = time.time()
                detected_count += 1

                limpia = placa_final.replace("-", "")
                print(f"\nPLACA CONFIRMADA → {placa_final} (confianza: {count}/15)")

                # REGISTRO AUTOMÁTICO EN BD
                vehiculo = Vehiculo.objects.filter(
                    placa__iregex=rf"^{placa_final}$|^{limpia}$"
                ).first()

                if vehiculo:
                    os.makedirs("media/accesos/fotos", exist_ok=True)
                    foto_path = f"accesos/fotos/{limpia}_{int(time.time())}.jpg"
                    cv2.imwrite(f"media/{foto_path}", frame)

                    usuario_autorizado = vehiculo.usuario
                    prestamo = vehiculo.prestamos.filter(
                        estado='activo',
                        fecha_inicio__lte=timezone.now(),
                        fecha_fin__gte=timezone.now()
                    ).first()
                    if prestamo:
                        usuario_autorizado = prestamo.prestatario

                    RegistroAcceso.objects.create(
                        vehiculo=vehiculo,
                        usuario_autorizado=usuario_autorizado,
                        vigilante=vigilante,
                        tipo_acceso='entrada',
                        metodo='automatico',
                        placa_detectada=placa_final,
                        confianza_deteccion=round(count/15, 2),
                        foto_capturada=foto_path,
                        placa_coincide=True,
                        prestamo_relacionado=prestamo,
                        observaciones="Entrada automática"
                    )
                    nombre = vehiculo.usuario.get_full_name().strip() or vehiculo.usuario.username or "Sin nombre"
                    print(f"ENTRADA REGISTRADA → {nombre} | {vehiculo.marca} {vehiculo.modelo}")

        ret, buffer = cv2.imencode('.jpg', vis, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    cap.release()


# ==================== VISTAS ====================
@login_required
@role_required('vigilante')
def video_feed(request):
    return StreamingHttpResponse(gen_video(request), content_type='multipart/x-mixed-replace; boundary=frame')


@login_required
@csrf_exempt
@never_cache
def camera_status(request):
    global ultima_placa_confirmada, detected_count

    propietario = {
        "nombre": "Esperando placa...",
        "dni": "—",
        "telefono": "—",
        "marca": "—",
        "modelo": "—",
        "autorizado": False
    }

    if ultima_placa_confirmada:
        placa_raw = ultima_placa_confirmada
        limpia = placa_raw.replace("-", "")

        vehiculo = (
            Vehiculo.objects.filter(placa__iexact=placa_raw).first() or
            Vehiculo.objects.filter(placa__iexact=limpia).first() or
            Vehiculo.objects.filter(placa__icontains=limpia).first()
        )

        if vehiculo and vehiculo.usuario:
            user = vehiculo.usuario
            perfil = Perfil.objects.filter(user=user).first()
            propietario = {
                "nombre": user.get_full_name().strip() or user.username or "Sin nombre",
                "dni": getattr(perfil, 'dni', '—') if perfil else '—',
                "telefono": getattr(perfil, 'telefono', '—') if perfil else '—',
                "marca": vehiculo.marca or '—',
                "modelo": vehiculo.modelo or '—',
                "autorizado": True
            }

    return JsonResponse({
        "placa_confirmada": ultima_placa_confirmada,
        "propietario": propietario,
        "vehicle_count": detected_count
    })


@login_required
@role_required('vigilante')
def monitor_view(request):
    return render(request, 'vehiculos/camara_vigilante.html')

@login_required
@csrf_exempt
def video_feed_status(request):
    # Esta vista redirige al estado real de la cámara
    return camera_status(request)
