from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Vehiculo
from .forms import VehiculoForm

# Importaciones para API REST
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Count
from datetime import date, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from .serializers import (
    VehiculoSerializer, 
    PrestamoVehiculoSerializer, 
    RegistroAccesoSerializer,
    RegistroAccesoCreateSerializer
)
from .models import Vehiculo, PrestamoVehiculo, RegistroAcceso
from .plate_detection import detect_plate_from_upload, CameraManager

logger = logging.getLogger(__name__)

# Vistas existentes para renderizado HTML
@login_required
def lista_vehiculos(request):
    vehiculos = request.user.vehiculos.all()
    return render(request, 'vehiculos/lista_vehiculos.html', {'vehiculos': vehiculos})

@login_required
def agregar_vehiculo(request):
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
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, usuario=request.user)
    if request.method == 'POST':
        vehiculo.delete()
        messages.success(request, "Vehículo eliminado correctamente ✅")
        return redirect('lista_vehiculos')
    return render(request, 'vehiculos/eliminar_vehiculo.html', {'vehiculo': vehiculo})

# Vistas para API REST
class VehiculoViewSet(viewsets.ModelViewSet):
    serializer_class = VehiculoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Solo devuelve los vehículos del usuario actual
        return self.request.user.vehiculos.all()
    
    def perform_create(self, serializer):
        # Asigna el usuario actual al crear un nuevo vehículo
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=['post'])
    def detect_plate(self, request, pk=None):
        """Detecta placa en una foto del vehículo"""
        vehiculo = self.get_object()
        
        if 'image' not in request.FILES:
            return Response(
                {'error': 'Se requiere una imagen'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            detection_result = detect_plate_from_upload(request.FILES['image'])
            return Response(detection_result)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrestamoVehiculoViewSet(viewsets.ModelViewSet):
    serializer_class = PrestamoVehiculoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Usuario puede ver préstamos donde es prestador o prestatario
        return PrestamoVehiculo.objects.filter(
            Q(prestador=user) | Q(prestatario=user)
        ).order_by('-fecha_solicitud')

    def perform_create(self, serializer):
        # El usuario actual es el prestador
        serializer.save(prestador=self.request.user)

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprueba un préstamo (solo el prestador)"""
        prestamo = self.get_object()
        
        if prestamo.prestador != request.user:
            return Response(
                {'error': 'Solo el dueño del vehículo puede aprobar el préstamo'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if prestamo.estado != 'pendiente':
            return Response(
                {'error': 'Solo se pueden aprobar préstamos pendientes'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        prestamo.estado = 'aprobado'
        # Si la fecha de inicio es ahora o pasada, activar inmediatamente
        if prestamo.fecha_inicio <= timezone.now():
            prestamo.estado = 'activo'
        
        prestamo.save()
        
        serializer = self.get_serializer(prestamo)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        """Rechaza un préstamo (solo el prestador)"""
        prestamo = self.get_object()
        
        if prestamo.prestador != request.user:
            return Response(
                {'error': 'Solo el dueño del vehículo puede rechazar el préstamo'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        prestamo.estado = 'rechazado'
        prestamo.save()
        
        serializer = self.get_serializer(prestamo)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def mis_prestamos(self, request):
        """Obtiene préstamos del usuario actual"""
        user = request.user
        
        # Préstamos donde soy prestador
        prestamos_otorgados = self.get_queryset().filter(prestador=user)
        
        # Préstamos donde soy prestatario
        prestamos_recibidos = self.get_queryset().filter(prestatario=user)
        
        return Response({
            'prestamos_otorgados': self.get_serializer(prestamos_otorgados, many=True).data,
            'prestamos_recibidos': self.get_serializer(prestamos_recibidos, many=True).data
        })


class RegistroAccesoViewSet(viewsets.ReadOnlyModelViewSet):
    """Vista de solo lectura para registros de acceso"""
    serializer_class = RegistroAccesoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Si es vigilante, puede ver todos los registros
        if hasattr(user, 'perfil') and user.perfil.rol and user.perfil.rol.nombre == 'vigilante':
            return RegistroAcceso.objects.all().order_by('-timestamp')
        
        # Usuarios normales solo ven registros de sus vehículos
        return RegistroAcceso.objects.filter(
            Q(vehiculo__usuario=user) | Q(usuario_autorizado=user)
        ).order_by('-timestamp')

    @action(detail=False, methods=['get'])
    def mis_accesos(self, request):
        """Obtiene registros de acceso del usuario actual"""
        user = request.user
        registros = RegistroAcceso.objects.filter(
            usuario_autorizado=user
        ).order_by('-timestamp')
        
        serializer = self.get_serializer(registros, many=True)
        return Response(serializer.data)


# Vistas específicas para vigilantes
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def registrar_acceso_automatico(request):
    """
    Registra acceso automático mediante detección de placa
    Solo para usuarios con rol de vigilante
    """
    # Verificar permisos de vigilante
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol:
        return Response(
            {'error': 'No tienes permisos de vigilante'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.user.perfil.rol.nombre != 'vigilante':
        return Response(
            {'error': 'Solo los vigilantes pueden registrar accesos'}, 
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = RegistroAccesoCreateSerializer(
        data=request.data, 
        context={'request': request}
    )
    
    if serializer.is_valid():
        registro = serializer.save()
        response_serializer = RegistroAccesoSerializer(registro)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def detectar_placa_camara(request):
    """
    Detecta placa desde cámara en tiempo real
    Solo para vigilantes
    """
    # Verificar permisos de vigilante
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol:
        return Response(
            {'error': 'No tienes permisos de vigilante'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.user.perfil.rol.nombre != 'vigilante':
        return Response(
            {'error': 'Solo los vigilantes pueden usar la cámara'}, 
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        camera = CameraManager()
        result = camera.detect_plates_in_frame()
        camera.release()
        
        if result:
            return Response(result)
        else:
            return Response(
                {'error': 'No se pudo capturar frame de la cámara'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Error en detección por cámara: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def estadisticas_accesos(request):
    """
    Obtiene estadísticas de accesos para vigilantes y administradores
    """
    # Verificar permisos
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol:
        return Response(
            {'error': 'No tienes permisos suficientes'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    rol = request.user.perfil.rol.nombre
    if rol not in ['vigilante', 'administrador_general']:
        return Response(
            {'error': 'Solo vigilantes y administradores pueden ver estadísticas'}, 
            status=status.HTTP_403_FORBIDDEN
        )

    from django.db.models import Count
    from datetime import datetime, timedelta

    hoy = timezone.now().date()
    hace_7_dias = hoy - timedelta(days=7)
    
    # Estadísticas básicas
    total_registros = RegistroAcceso.objects.count()
    registros_hoy = RegistroAcceso.objects.filter(timestamp__date=hoy).count()
    registros_semana = RegistroAcceso.objects.filter(timestamp__date__gte=hace_7_dias).count()
    
    # Entradas vs salidas hoy
    entradas_hoy = RegistroAcceso.objects.filter(
        timestamp__date=hoy, tipo_acceso='entrada'
    ).count()
    salidas_hoy = RegistroAcceso.objects.filter(
        timestamp__date=hoy, tipo_acceso='salida'
    ).count()
    
    # Vehículos únicos hoy
    vehiculos_unicos_hoy = RegistroAcceso.objects.filter(
        timestamp__date=hoy
    ).values('vehiculo').distinct().count()

    return Response({
        'total_registros': total_registros,
        'registros_hoy': registros_hoy,
        'registros_semana': registros_semana,
        'entradas_hoy': entradas_hoy,
        'salidas_hoy': salidas_hoy,
        'vehiculos_unicos_hoy': vehiculos_unicos_hoy,
        'vehiculos_en_cochera': entradas_hoy - salidas_hoy,
    })


# =============== ENDPOINTS ESPECÍFICOS PARA VIGILANTES ===============

@api_view(['GET'])
@login_required
def vigilante_estadisticas(request):
    """
    Estadísticas en tiempo real para el dashboard del vigilante.
    Endpoint: /vehiculos/api/vigilante/estadisticas/
    """
    # Verificar que el usuario sea vigilante
    if not hasattr(request.user, 'perfil') or request.user.perfil.rol.nombre != 'vigilante':
        return JsonResponse({'error': 'Acceso denegado. Solo vigilantes pueden acceder.'}, status=403)
    
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
        'vehiculos_en_cochera': max(0, vehiculos_en_cochera),  # No puede ser negativo
        'registros_hoy': registros_hoy,
        'ultimo_registro': {
            'placa': ultimo_registro.vehiculo.placa if ultimo_registro else None,
            'tipo': ultimo_registro.tipo_acceso if ultimo_registro else None,
            'hora': ultimo_registro.timestamp.strftime('%H:%M') if ultimo_registro else None
        } if ultimo_registro else None,
        'fecha': hoy.strftime('%Y-%m-%d')
    })


@api_view(['POST'])
@login_required
@csrf_exempt
def vigilante_detectar_placa(request):
    """
    Detectar placa usando cámara en tiempo real.
    Endpoint: /vehiculos/api/vigilante/detectar-placa/
    """
    # Verificar que el usuario sea vigilante
    if not hasattr(request.user, 'perfil') or request.user.perfil.rol.nombre != 'vigilante':
        return JsonResponse({'error': 'Acceso denegado. Solo vigilantes pueden usar la detección.'}, status=403)
    
    try:
        # Inicializar cámara si es necesario
        camera_manager = CameraManager()
        
        # Capturar frame y detectar placa
        detection_result = camera_manager.detect_from_camera()
        
        if detection_result.get('plates_detected'):
            return JsonResponse({
                'success': True,
                'plates_detected': detection_result['plates_detected'],
                'confidence_scores': detection_result['confidence_scores'],
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


@api_view(['POST'])
@login_required
@csrf_exempt
def vigilante_registrar_acceso(request):
    """
    Registrar entrada/salida de vehículo por vigilante.
    Endpoint: /vehiculos/api/vigilante/registrar-acceso/
    """
    # Verificar que el usuario sea vigilante
    if not hasattr(request.user, 'perfil') or request.user.perfil.rol.nombre != 'vigilante':
        return JsonResponse({'error': 'Acceso denegado. Solo vigilantes pueden registrar accesos.'}, status=403)
    
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
                'error': f'Vehículo con placa {placa} no está registrado en el sistema'
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
@login_required
def vigilante_vehiculos_cochera(request):
    """
    Lista de vehículos actualmente en la cochera.
    Endpoint: /vehiculos/api/vigilante/vehiculos-cochera/
    """
    # Verificar que el usuario sea vigilante
    if not hasattr(request.user, 'perfil') or request.user.perfil.rol.nombre != 'vigilante':
        return JsonResponse({'error': 'Acceso denegado. Solo vigilantes pueden acceder.'}, status=403)
    
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
                'tiempo_estacionado': str(timezone.now() - entrada.timestamp).split('.')[0],  # Sin microsegundos
                'es_prestamo': entrada.prestamo_relacionado is not None
            })
    
    return JsonResponse({
        'vehiculos_en_cochera': vehiculos_cochera,
        'total': len(vehiculos_cochera),
        'fecha': hoy.strftime('%Y-%m-%d')
    })


@api_view(['GET'])
@login_required
def vigilante_buscar_vehiculo(request):
    """
    Buscar información de vehículo por placa.
    Endpoint: /vehiculos/api/vigilante/buscar-vehiculo/?placa=ABC123
    """
    # Verificar que el usuario sea vigilante
    if not hasattr(request.user, 'perfil') or request.user.perfil.rol.nombre != 'vigilante':
        return JsonResponse({'error': 'Acceso denegado. Solo vigilantes pueden acceder.'}, status=403)
    
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
