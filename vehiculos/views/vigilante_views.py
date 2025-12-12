"""
Vistas específicas para el rol de vigilante
"""
import logging
from ..plate_detection import CameraManager
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import date, timedelta
from usuarios.views import role_required
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser, FormParser
from ..models import RegistroAcceso, Vehiculo, PrestamoVehiculo
from django.contrib.auth.decorators import login_required
from vehiculos.models import RegistroAcceso


logger = logging.getLogger(__name__)


def _check_vigilante_api(request):
    """Helper para APIs: validar autenticación y rol 'vigilante'.
    Devuelve (None) si está ok, o JsonResponse con error y código si no."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)

    perfil = getattr(request.user, 'perfil', None)
    if not perfil or not getattr(perfil, 'rol', None):
        return JsonResponse({'error': 'Tu cuenta no tiene rol asignado'}, status=403)

    if getattr(perfil.rol, 'nombre', None) != 'vigilante':
        return JsonResponse({'error': 'Acceso denegado. Solo vigilantes pueden acceder.'}, status=403)

    return None

@role_required('vigilante')
def dashboard_vigilante(request):
    usuario = request.user

    # Últimos 5 registros (globales)
    actividad_reciente = RegistroAcceso.objects.select_related('vehiculo').order_by('-timestamp')[:5]

    return render(request, "vehiculos/dashboard_vigilante.html", {
        'usuario': usuario,
        'actividad_reciente': actividad_reciente,
        'titulo': 'Dashboard Vigilante'
    })


@login_required
@role_required('vigilante')
def camara_vigilante(request):
    return render(request, 'vehiculos/camara_vigilante.html')

@role_required('vigilante')
def registro_acceso_vigilante(request):
    """Vista para registrar accesos de vehículos."""
    return render(request, 'vehiculos/registro_acceso.html', {
        'usuario': request.user,
        'titulo': 'Registrar Acceso'
    })

@role_required('vigilante')
def buscar_vehiculo_vigilante(request):
    """Vista para buscar información de vehículos por placa."""
    return render(request, 'vehiculos/buscar_vehiculo.html', {
        'usuario': request.user,
        'titulo': 'Buscar Vehículo'
    })

@role_required('vigilante')
def vehiculos_cochera_vigilante(request):
    """Vista para mostrar vehículos actualmente en la cochera."""
    return render(request, 'vehiculos/vehiculos_cochera.html', {
        'usuario': request.user,
        'titulo': 'Vehículos en Cochera'
    })


@api_view(['GET'])
def vigilante_estadisticas(request):
    """
    Estadísticas en tiempo real para el dashboard del vigilante.
    Endpoint: /vehiculos/api/vigilante/estadisticas/
    """
    # Verificar que el usuario sea vigilante
    err = _check_vigilante_api(request)
    if err:
        return err
    
    hoy = date.today()
    
    # Estadísticas del día
    entradas_hoy = RegistroAcceso.objects.filter(
        timestamp__date=hoy, 
        tipo_acceso='entrada'
    ).count()
    
    salidas_hoy = RegistroAcceso.objects.filter(
        timestamp__date=hoy, 
        tipo_acceso='salida'
    ).count()
    
    # Vehículos actualmente en cochera (entradas - salidas hoy)
    vehiculos_en_cochera = entradas_hoy - salidas_hoy
    
    # Total de registros hoy
    registros_hoy = entradas_hoy + salidas_hoy
    
    # Registro más reciente
    ultimo_registro = RegistroAcceso.objects.filter(
        timestamp__date=hoy
    ).order_by('-timestamp').first()
    
    return JsonResponse({
        'entradas_hoy': entradas_hoy,
        'salidas_hoy': salidas_hoy,
        'vehiculos_en_cochera': max(0, vehiculos_en_cochera),
        'registros_hoy': registros_hoy,
        'ultimo_registro': {
            'placa': ultimo_registro.vehiculo.placa if ultimo_registro else None,
            'tipo': ultimo_registro.tipo_acceso if ultimo_registro else None,
            'hora': ultimo_registro.timestamp.strftime('%H:%M') if ultimo_registro else None
        } if ultimo_registro else None,
        'fecha': hoy.strftime('%Y-%m-%d')
    })

@api_view(['POST'])
def vigilante_detectar_placa(request):
    """
    Detectar placa usando cámara en tiempo real.
    Endpoint: /vehiculos/api/vigilante/detectar-placa/
    """
    # Verificar que el usuario sea vigilante
    err = _check_vigilante_api(request)
    if err:
        return err
    
    try:
        # Inicializar cámara si es necesario
        camera_manager = CameraManager()

        # Capturar frame y detectar placa
        detection_result = camera_manager.detect_from_camera()

        if detection_result.get('plates_detected'):
            return JsonResponse({
                'success': True,
                'plates_detected': detection_result['plates_detected'],
                'confidence_scores': detection_result.get('confidence_scores', []),
                'timestamp': timezone.now().isoformat(),
                'message': f"Detectada(s) {len(detection_result['plates_detected'])} placa(s)"
            })
        else:
            return JsonResponse({
                'success': False,
                'plates_detected': [],
                'message': 'No se detectaron placas en este momento'
            })

    except Exception as e:
        logger.error(f"Error en detección de placa: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error en detección: {str(e)}',
            'plates_detected': []
        }, status=500)

@api_view(['GET'])
def vigilante_vehiculos_cochera(request):
    """
    Lista de vehículos actualmente en la cochera.
    Endpoint: /vehiculos/api/vigilante/vehiculos-cochera/
    """
    # Verificar que el usuario sea vigilante
    err = _check_vigilante_api(request)
    if err:
        return err
    
    hoy = date.today()
    
    # Obtener todos los vehículos que entraron hoy y no han salido
    vehiculos_cochera = []
    
    # Buscar todos los registros de entrada de hoy
    entradas_hoy = RegistroAcceso.objects.filter(
        timestamp__date=hoy,
        tipo_acceso='entrada'
    ).order_by('-timestamp')
    
    for entrada in entradas_hoy:
        # Verificar si ya salió
        salida = RegistroAcceso.objects.filter(
            vehiculo=entrada.vehiculo,
            timestamp__date=hoy,
            timestamp__gt=entrada.timestamp,
            tipo_acceso='salida'
        ).first()
        
        if not salida:  # No ha salido
            vehiculos_cochera.append({
                'vehiculo_id': entrada.vehiculo.id,
                'placa': entrada.vehiculo.placa,
                'propietario': entrada.vehiculo.usuario.get_full_name() or entrada.vehiculo.usuario.username,
                'usuario_autorizado': entrada.usuario_autorizado.get_full_name() or entrada.usuario_autorizado.username,
                'hora_entrada': entrada.timestamp.strftime('%H:%M'),
                'tiempo_estacionado': str(timezone.now() - entrada.timestamp).split('.')[0],
                'es_prestamo': entrada.prestamo_relacionado is not None
            })
    
    return JsonResponse({
        'vehiculos_en_cochera': vehiculos_cochera,
        'total': len(vehiculos_cochera),
        'fecha': hoy.strftime('%Y-%m-%d')
    })

@api_view(['POST'])
def vigilante_registrar_acceso(request):
    """
    Registrar entrada/salida de vehículo por vigilante.
    Endpoint: /vehiculos/api/vigilante/registrar-acceso/
    """
    err = _check_vigilante_api(request)
    if err:
        return err
    
    try:
        placa = request.POST.get('placa_detectada', '').strip().upper()
        tipo_acceso = request.POST.get('tipo_acceso', '').lower()
        confianza = float(request.POST.get('confianza_deteccion', 0.0))
        observaciones = request.POST.get('observaciones', '')
        
        # Validaciones
        if not placa:
            return JsonResponse({'error': 'Placa requerida'}, status=400)
            
        if tipo_acceso not in ['entrada', 'salida']:
            return JsonResponse({'error': 'Tipo de acceso debe ser "entrada" o "salida"'}, status=400)
            
        # Buscar vehículo por placa
        try:
            vehiculo = Vehiculo.objects.get(placa=placa)
        except Vehiculo.DoesNotExist:
            return JsonResponse({
                'error': f'Vehículo con placa {placa} no está registrado'
            }, status=404)
        
        # Verificar lógica de entrada/salida
        ultimo_registro = RegistroAcceso.objects.filter(
            vehiculo=vehiculo
        ).order_by('-timestamp').first()
        
        # Validación de secuencia entrada/salida
        if ultimo_registro:
            if tipo_acceso == 'entrada' and ultimo_registro.tipo_acceso == 'entrada':
                return JsonResponse({
                    'error': f'El vehículo {placa} ya tiene una entrada registrada sin salida'
                }, status=400)
            elif tipo_acceso == 'salida' and ultimo_registro.tipo_acceso == 'salida':
                return JsonResponse({
                    'error': f'El vehículo {placa} no tiene una entrada previa para registrar salida'
                }, status=400)
        elif tipo_acceso == 'salida':
            return JsonResponse({
                'error': f'No se puede registrar salida sin una entrada previa para {placa}'
            }, status=400)
        
        # Determinar usuario autorizado (propietario o préstamo activo)
        usuario_autorizado = vehiculo.usuario  # Por defecto el propietario
        prestamo_activo = None
        
        # Verificar si hay préstamo activo
        prestamos_activos = PrestamoVehiculo.objects.filter(
            vehiculo=vehiculo,
            estado='aprobado',
            fecha_inicio__lte=timezone.now().date(),
            fecha_fin__gte=timezone.now().date()
        )
        
        if prestamos_activos.exists():
            prestamo_activo = prestamos_activos.first()
            usuario_autorizado = prestamo_activo.usuario_solicitante
        
        # Crear registro de acceso
        registro = RegistroAcceso.objects.create(
            vehiculo=vehiculo,
            usuario_autorizado=usuario_autorizado,
            tipo_acceso=tipo_acceso,
            placa_detectada=placa,
            confianza_deteccion=confianza,
            vigilante=request.user,
            prestamo_relacionado=prestamo_activo,
            observaciones=observaciones or f'Registro {tipo_acceso} por detección automática'
        )
        
        return JsonResponse({
            'success': True,
            'registro_id': registro.id,
            'mensaje': f'{tipo_acceso.capitalize()} registrada correctamente',
            'vehiculo': {
                'placa': vehiculo.placa,
                'propietario': vehiculo.usuario.get_full_name() or vehiculo.usuario.username,
                'usuario_autorizado': usuario_autorizado.get_full_name() or usuario_autorizado.username,
                'es_prestamo': prestamo_activo is not None
            },
            'registro': {
                'tipo_acceso': registro.tipo_acceso,
                'timestamp': registro.timestamp.isoformat(),
                'confianza': registro.confianza_deteccion
            }
        })
        
    except ValueError as e:
        return JsonResponse({'error': f'Datos inválidos: {str(e)}'}, status=400)
    except Exception as e:
        logger.error(f"Error al registrar acceso: {str(e)}")
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

@api_view(['GET'])
def vigilante_buscar_vehiculo(request):
    """
    Buscar información de vehículo por placa.
    Endpoint: /vehiculos/api/vigilante/buscar-vehiculo/?placa=ABC123
    """
    err = _check_vigilante_api(request)
    if err:
        return err
    
    placa = request.GET.get('placa', '').strip().upper()
    
    if not placa:
        return JsonResponse({'error': 'Parámetro placa requerido'}, status=400)
    
    try:
        vehiculo = Vehiculo.objects.get(placa=placa)
        
        # Buscar préstamo activo
        prestamo_activo = PrestamoVehiculo.objects.filter(
            vehiculo=vehiculo,
            estado='aprobado',
            fecha_inicio__lte=timezone.now().date(),
            fecha_fin__gte=timezone.now().date()
        ).first()
        
        # Último registro
        ultimo_registro = RegistroAcceso.objects.filter(
            vehiculo=vehiculo
        ).order_by('-timestamp').first()
        
        return JsonResponse({
            'encontrado': True,
            'vehiculo': {
                'id': vehiculo.id,
                'placa': vehiculo.placa,
                'marca': vehiculo.marca,
                'modelo': vehiculo.modelo,
                'color': vehiculo.color,
                'propietario': vehiculo.usuario.get_full_name() or vehiculo.usuario.username,
                'propietario_username': vehiculo.usuario.username
            },
            'prestamo_activo': {
                'usuario_autorizado': prestamo_activo.usuario_solicitante.get_full_name() or prestamo_activo.usuario_solicitante.username,
                'fecha_inicio': prestamo_activo.fecha_inicio.strftime('%Y-%m-%d'),
                'fecha_fin': prestamo_activo.fecha_fin.strftime('%Y-%m-%d'),
                'motivo': prestamo_activo.motivo
            } if prestamo_activo else None,
            'ultimo_acceso': {
                'tipo': ultimo_registro.tipo_acceso,
                'timestamp': ultimo_registro.timestamp.isoformat(),
                'vigilante': ultimo_registro.vigilante.username
            } if ultimo_registro else None,
            'esta_en_cochera': ultimo_registro and ultimo_registro.tipo_acceso == 'entrada' if ultimo_registro else False
        })
        
    except Vehiculo.DoesNotExist:
        return JsonResponse({
            'encontrado': False,
            'mensaje': f'Vehículo con placa {placa} no está registrado'
        })
    except Exception as e:
        logger.error(f"Error al buscar vehículo: {str(e)}")
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
