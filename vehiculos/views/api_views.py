"""
Vistas de API REST
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
import logging
from ..models import Vehiculo, PrestamoVehiculo, RegistroAcceso
from ..serializers import (
    VehiculoSerializer, 
    PrestamoVehiculoSerializer,
    RegistroAccesoSerializer,
    RegistroAccesoCreateSerializer
)
from ..plate_detection import detect_plate_from_upload

logger = logging.getLogger(__name__)

class VehiculoViewSet(viewsets.ModelViewSet):
    """ViewSet para CRUD de vehículos."""
    serializer_class = VehiculoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.request.user.vehiculos.all()
    
    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=['post'])
    def detect_plate(self, request, pk=None):
        """Detecta placa en una foto del vehículo."""
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
    """ViewSet para gestión de préstamos de vehículos."""
    serializer_class = PrestamoVehiculoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PrestamoVehiculo.objects.filter(
            Q(prestador=self.request.user) | Q(prestatario=self.request.user)
        ).order_by('-fecha_solicitud')

    def perform_create(self, serializer):
        serializer.save(prestador=self.request.user)

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprueba un préstamo (solo el prestador)."""
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
        if prestamo.fecha_inicio <= timezone.now():
            prestamo.estado = 'activo'
        prestamo.save()
        
        return Response(self.get_serializer(prestamo).data)

    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        """Rechaza un préstamo (solo el prestador)."""
        prestamo = self.get_object()
        
        if prestamo.prestador != request.user:
            return Response(
                {'error': 'Solo el dueño del vehículo puede rechazar el préstamo'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        prestamo.estado = 'rechazado'
        prestamo.save()
        
        return Response(self.get_serializer(prestamo).data)

class RegistroAccesoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para registros de acceso."""
    serializer_class = RegistroAccesoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if hasattr(user, 'perfil') and user.perfil.rol and user.perfil.rol.nombre == 'vigilante':
            return RegistroAcceso.objects.all().order_by('-timestamp')
        
        return RegistroAcceso.objects.filter(
            Q(vehiculo__usuario=user) | Q(usuario_autorizado=user)
        ).order_by('-timestamp')

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def registrar_acceso_automatico(request):
    """Registra acceso automático mediante detección de placa."""
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol or request.user.perfil.rol.nombre != 'vigilante':
        return Response(
            {'error': 'Solo los vigilantes pueden registrar accesos'}, 
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = RegistroAccesoCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        registro = serializer.save()
        response_serializer = RegistroAccesoSerializer(registro)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)