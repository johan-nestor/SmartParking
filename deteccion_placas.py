# ============================================================
# 🧩 DETECCION_PLACAS.PY
# ============================================================

import cv2
from ultralytics import YOLO
from pathlib import Path
import pyttsx3
import time

CLASES_ES = {
    0: "carro",
    1: "placa",
    2: "bajaj"
}

def decir(texto):
    try:
        e = pyttsx3.init()
        e.setProperty("rate", 170); e.setProperty("volume", 1.0)
        e.say(texto); e.runAndWait()
    except Exception:
        pass

def cargar_modelo():
    ruta = Path("best.pt")
    if ruta.exists():
        print("✅ Modelo personalizado:", ruta.resolve())
        m = YOLO(str(ruta))
    else:
        print("⚠️ No se encontró best.pt, usando yolov8n.pt")
        m = YOLO("yolov8n.pt")
    print("🧾 Clases del modelo:", m.names)
    return m

def iniciar_camara():
    for i in range(4):
        cam = cv2.VideoCapture(1)
        if cam.isOpened():
            return cam, i
        cam.release()
    return None, None

def main():
    print("=== DETECCIÓN EN TIEMPO REAL ===")
    model = cargar_modelo()
    cam, idx = iniciar_camara()
    if not cam:
        print("❌ No hay cámara"); return

    confianza = 0.25   # ↓ umbral más sensible
    ultimo_nombre = None
    t0 = time.time(); frames = 0

    print("Controles: [c] salir | [g] guardar | [-/+] conf | [0]=0.10, [1]=0.25, [2]=0.40")

    while True:
        ok, frame = cam.read()
        if not ok: print("⚠️ frame inválido"); break

        # Inferencia con imgsz explícito y conf variable
        res = model(frame, conf=confianza, imgsz=640, verbose=False)
        vis = res[0].plot()

        # FPS / overlay
        frames += 1
        if frames % 10 == 0:
            now = time.time(); fps = 10.0 / (now - t0); t0 = now
        else:
            fps = None

        # Mostrar conf/clases en pantalla
        txt = f"conf={confianza:.2f} | cam={idx}"
        if fps: txt += f" | fps~{fps:.1f}"
        cv2.putText(vis, txt, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (40,255,40), 2)
        cv2.putText(vis, f"classes: {list(model.names.values())}", (10, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180,255,180), 2)

        # Voz y log
        for r in res:
            for b in r.boxes:
                conf = float(b.conf[0]); cid = int(b.cls[0])
                if conf > 0.40 and cid in CLASES_ES:  # ↓ disparador de voz más bajo
                    nombre = CLASES_ES[cid]
                    if ultimo_nombre != nombre:
                        print(f"🧠 {nombre} ({conf:.2f})"); decir(f"{nombre} detectada")
                        ultimo_nombre = nombre

        cv2.imshow("🔎 Store-AI (tiempo real)", vis)
        k = cv2.waitKey(1) & 0xFF
        if k == ord('c'): break
        elif k == ord('g'):
            out = Path("capturas"); out.mkdir(exist_ok=True)
            p = out / f"cap.jpg"; cv2.imwrite(str(p), vis); print("💾 Guardado:", p)
        elif k == ord('-'):
            confianza = max(0.05, confianza - 0.05); print(f"📉 conf={confianza:.2f}")
        elif k == ord('+'):
            confianza = min(0.95, confianza + 0.05); print(f"📈 conf={confianza:.2f}")
        elif k == ord('0'):
            confianza = 0.10; print("🎯 conf=0.10")
        elif k == ord('1'):
            confianza = 0.25; print("🎯 conf=0.25")
        elif k == ord('2'):
            confianza = 0.40; print("🎯 conf=0.40")

    cam.release(); cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
