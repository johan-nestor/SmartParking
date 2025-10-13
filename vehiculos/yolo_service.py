from ultralytics import YOLO
from pathlib import Path
import cv2

_MODEL = None

def get_model():
    global _MODEL
    if _MODEL is None:
        base = Path(__file__).resolve().parent.parent
        ruta = base / "best.pt"
        if ruta.exists():
            print("✅ Cargando modelo personalizado:", ruta)
            _MODEL = YOLO(str(ruta))
        else:
            print("⚠️ best.pt no encontrado, cargando yolov8n.pt desde repo")
            _MODEL = YOLO(str(base / "yolov8n.pt"))
    return _MODEL

def annotate_frame(frame, conf=0.25, imgsz=640):
    """
    Recibe frame BGR (numpy). Devuelve (vis_frame, detections).
    vis_frame: imagen BGR con cajas (lista) preparada para imencode.
    detections: lista de dicts {cls, conf, box}
    """
    model = get_model()
    # ultralytics acepta ndarray BGR
    res = model(frame, conf=conf, imgsz=imgsz, verbose=False)
    try:
        vis = res[0].plot()  # normalmente devuelve ndarray BGR
        if vis is None:
            vis = frame.copy()
    except Exception:
        vis = frame.copy()

    detections = []
    for r in res:
        for b in r.boxes:
            try:
                conf_val = float(b.conf[0])
                cls_id = int(b.cls[0])
                xyxy = None
                if hasattr(b, "xyxy"):
                    xyxy = (float(b.xyxy[0][0]), float(b.xyxy[0][1]),
                            float(b.xyxy[0][2]), float(b.xyxy[0][3]))
            except Exception:
                conf_val = 0.0; cls_id = -1; xyxy = None
            detections.append({"cls": cls_id, "conf": conf_val, "xyxy": xyxy})
    return vis, detections