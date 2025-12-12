"""
Vistas para gestión básica de vehículos (CRUD)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Vehiculo
from ..forms import VehiculoForm
from django.http import JsonResponse
from ..models import Vehiculo, PrestamoVehiculo
from vehiculos.models import RegistroAcceso
from django.utils.timezone import localdate, make_aware
from datetime import datetime, time
from django.utils import timezone




@login_required
def lista_vehiculos(request):
    """Lista todos los vehículos del usuario."""
    vehiculos = request.user.vehiculos.all()
    return render(request, 'vehiculos/lista_vehiculos.html', {'vehiculos': vehiculos})

@login_required
def agregar_vehiculo(request):
    """Añade un nuevo vehículo."""
    if request.method == 'POST':
        form = VehiculoForm(request.POST, request.FILES)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.usuario = request.user
            vehiculo.save()
            messages.success(request, "Vehículo agregado correctamente ✅")
            return redirect('lista_vehiculos')
    else:
        form = VehiculoForm()
    return render(request, 'vehiculos/agregar_vehiculo.html', {'form': form})

@login_required
def editar_vehiculo(request, vehiculo_id):
    """Edita un vehículo existente."""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, usuario=request.user)
    if request.method == 'POST':
        form = VehiculoForm(request.POST, request.FILES, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo actualizado correctamente ✅")
            return redirect('lista_vehiculos')
    else:
        form = VehiculoForm(instance=vehiculo)
    return render(request, 'vehiculos/editar_vehiculo.html', {'form': form})

@login_required
def eliminar_vehiculo(request, vehiculo_id):
    """Elimina un vehículo."""
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, usuario=request.user)
    if request.method == 'POST':
        vehiculo.delete()
        messages.success(request, "Vehículo eliminado correctamente ✅")
        return redirect('lista_vehiculos')
    return render(request, 'vehiculos/eliminar_vehiculo.html', {'vehiculo': vehiculo})

"""
Vista para registrar accesos manuales desde el formulario del vigilante
"""
@login_required
def registrar_acceso_manual(request):
    print("👉 Vista registrar_acceso_manual se llamó")  # DEBUG

    if request.method == "POST":
        print("👉 Se recibió un POST")
        placa = request.POST.get("placa_detectada", "").strip()
        tipo_acceso = request.POST.get("tipo_acceso")
        observaciones = request.POST.get("observaciones", "")
        confianza = request.POST.get("confianza_deteccion", 0)

        if not placa:
            # Aquí puedes redirigir mostrando mensaje con Django messages si quieres
            return redirect("dashboard_vigilante")

        # Buscar vehículo por placa
        try:
            vehiculo = Vehiculo.objects.get(placa__iexact=placa)
        except Vehiculo.DoesNotExist:
            return redirect("dashboard_vigilante")

        # Buscar préstamo activo
        prestamo_activo = PrestamoVehiculo.objects.filter(
            vehiculo=vehiculo,
            estado="activo"
        ).first()

        # Usuario autorizado
        if prestamo_activo:
            usuario_autorizado = prestamo_activo.prestatario
        else:
            usuario_autorizado = vehiculo.usuario

        # Crear registro
        RegistroAcceso.objects.create(
            vehiculo=vehiculo,
            usuario_autorizado=usuario_autorizado,
            vigilante=request.user,
            tipo_acceso=tipo_acceso,
            metodo='manual'
        )


        # 🔥 Redirige al dashboard del vigilante
        return redirect("dashboard_vigilante")

    # Si no es POST
    return redirect("dashboard_vigilante")


"""
Vista para buscar por medio de placas desde el formulario del vigilante
"""

@login_required
def buscar_vehiculo_vigilante(request):

    # aceptar ambos nombres de parámetro (q o placa)
    raw_query = request.GET.get("q", "").strip() or request.GET.get("placa", "").strip()
    query = raw_query or ""   # seguro no nulo
    vehiculo = None

    # normalizar función
    def normalizar(s: str) -> str:
        if not s:
            return ""
        return s.replace(" ", "").replace("-", "").upper()

    # --- BUSCAR VEHÍCULO con normalización ---
    if query:
        placa_normalizada = normalizar(query)

        # debug: lista de placas normalizadas (para mostrar en template si quieres)
        debug_plates = []
        # recorrer en Python para asegurar coincidencia (ignorando formato)
        for v in Vehiculo.objects.all():
            placa_db_norm = normalizar(v.placa or "")
            debug_plates.append({"id": v.id, "orig": v.placa, "norm": placa_db_norm})
            # imprimir en consola para depuración
            print(f"[DEBUG BUSCAR] query_norm='{placa_normalizada}' vs db_norm='{placa_db_norm}' (id={v.id})")
            if placa_db_norm == placa_normalizada:
                vehiculo = v
                print(f"[DEBUG BUSCAR] >> COINCIDENCIA encontrada: Vehiculo id={v.id} placa='{v.placa}'")
                break

        # fallback: buscar por icontains sobre placa si aún no encontrado
        if not vehiculo:
            vehiculo = Vehiculo.objects.filter(placa__icontains=query).first()
            if vehiculo:
                print(f"[DEBUG BUSCAR] fallback icontains encontró: id={vehiculo.id} placa='{vehiculo.placa}'")

    else:
        debug_plates = [ {"id": v.id, "orig": v.placa, "norm": normalizar(v.placa)} for v in Vehiculo.objects.all() ]

    # --- RESUMEN DEL DÍA (rango horario para evitar problemas TZ) ---
    hoy = localdate()

    registros_hoy = RegistroAcceso.objects.filter(timestamp__date=hoy)
    total_entradas = registros_hoy.filter(tipo_acceso="entrada").count()
    total_salidas = registros_hoy.filter(tipo_acceso="salida").count()

    # buscar préstamo activo si se encontró vehiculo (opcional)
    prestamo_activo = None
    if vehiculo:
        prestamo_activo = PrestamoVehiculo.objects.filter(vehiculo=vehiculo, estado="activo").first()

    context = {
        "vehiculo": vehiculo,
        "query": query,
        "total_entradas": total_entradas,
        "total_salidas": total_salidas,
        # datos de depuración que puedes quitar luego:
        "debug_plates": debug_plates,
        "debug_query_norm": normalizar(query),
        "prestamo_activo": prestamo_activo,
    }
    return render(request, "vehiculos/buscar_vehiculo.html", context)

def buscar_vehiculo_por_placa(request, placa):
    try:
        vehiculo = Vehiculo.objects.get(placa=placa)
        # Puedes incluir datos del usuario propietario
        data = {
            "usuario": {
                "username": vehiculo.usuario.username,
                "email": vehiculo.usuario.email,
            },
            "vehiculo": {
                "marca": vehiculo.marca,
                "modelo": vehiculo.modelo,
                "placa": vehiculo.placa,
                "color": vehiculo.color,
                "foto_vehiculo": vehiculo.foto_vehiculo.url if vehiculo.foto_vehiculo else None,
                "foto_placa": vehiculo.foto_placa.url if vehiculo.foto_placa else None,
            }
        }
        return JsonResponse(data)
    except Vehiculo.DoesNotExist:
        return JsonResponse({"error": "Vehículo no encontrado"}, status=404)