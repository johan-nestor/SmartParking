from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Vehiculo, PrestamoVehiculo, RegistroAcceso


class VehiculoSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    
    class Meta:
        model = Vehiculo
        fields = ['id', 'marca', 'modelo', 'placa', 'color', 'foto_vehiculo', 
                 'foto_placa', 'fecha_registro', 'usuario_nombre']


class PrestamoVehiculoSerializer(serializers.ModelSerializer):
    prestador_nombre = serializers.CharField(source='prestador.username', read_only=True)
    prestatario_nombre = serializers.CharField(source='prestatario.username', read_only=True)
    vehiculo_info = VehiculoSerializer(source='vehiculo', read_only=True)
    esta_activo = serializers.ReadOnlyField()

    class Meta:
        model = PrestamoVehiculo
        fields = ['id', 'vehiculo', 'vehiculo_info', 'prestador', 'prestador_nombre', 
                 'prestatario', 'prestatario_nombre', 'fecha_solicitud', 'fecha_inicio', 
                 'fecha_fin', 'estado', 'motivo', 'notas', 'esta_activo']

    def validate(self, data):
        """Validaciones personalizadas para préstamos"""
        vehiculo = data.get('vehiculo')
        prestador = data.get('prestador')
        prestatario = data.get('prestatario')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')

        # Validar que el prestador es el dueño del vehículo
        if vehiculo and prestador and vehiculo.usuario != prestador:
            raise serializers.ValidationError(
                "Solo el propietario del vehículo puede prestarlo"
            )

        # Validar que el prestatario no es el mismo que el prestador
        if prestador and prestatario and prestador == prestatario:
            raise serializers.ValidationError(
                "No puedes prestarte un vehículo a ti mismo"
            )

        # Validar fechas
        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            raise serializers.ValidationError(
                "La fecha de inicio debe ser anterior a la fecha de fin"
            )

        # Validar que no haya solapamiento con otros préstamos activos
        if vehiculo and fecha_inicio and fecha_fin:
            prestamos_solapados = PrestamoVehiculo.objects.filter(
                vehiculo=vehiculo,
                estado__in=['aprobado', 'activo'],
                fecha_inicio__lt=fecha_fin,
                fecha_fin__gt=fecha_inicio
            )
            
            # Si estamos actualizando, excluir el préstamo actual
            if self.instance:
                prestamos_solapados = prestamos_solapados.exclude(id=self.instance.id)
            
            if prestamos_solapados.exists():
                raise serializers.ValidationError(
                    "Ya existe un préstamo activo para este vehículo en el período seleccionado"
                )

        return data


class RegistroAccesoSerializer(serializers.ModelSerializer):
    vehiculo_info = VehiculoSerializer(source='vehiculo', read_only=True)
    vigilante_nombre = serializers.CharField(source='vigilante.username', read_only=True)
    usuario_autorizado_nombre = serializers.CharField(source='usuario_autorizado.username', read_only=True)
    es_acceso_autorizado = serializers.ReadOnlyField()

    class Meta:
        model = RegistroAcceso
        fields = ['id', 'vehiculo', 'vehiculo_info', 'usuario_autorizado', 
                 'usuario_autorizado_nombre', 'vigilante', 'vigilante_nombre', 
                 'tipo_acceso', 'timestamp', 'metodo', 'placa_detectada', 
                 'confianza_deteccion', 'foto_capturada', 'placa_coincide', 
                 'prestamo_relacionado', 'observaciones', 'es_acceso_autorizado']

    def validate(self, data):
        """Validaciones para registros de acceso"""
        vehiculo = data.get('vehiculo')
        usuario_autorizado = data.get('usuario_autorizado')
        placa_detectada = data.get('placa_detectada')

        # Si hay placa detectada, verificar coincidencia
        if vehiculo and placa_detectada:
            data['placa_coincide'] = vehiculo.placa.upper() == placa_detectada.upper()

        # Verificar autorización del usuario
        if vehiculo and usuario_autorizado:
            # Verificar si es el propietario
            if usuario_autorizado == vehiculo.usuario:
                data['prestamo_relacionado'] = None
            else:
                # Buscar préstamo activo
                prestamo_activo = PrestamoVehiculo.objects.filter(
                    vehiculo=vehiculo,
                    prestatario=usuario_autorizado,
                    estado='activo',
                    fecha_inicio__lte=timezone.now(),
                    fecha_fin__gte=timezone.now()
                ).first()
                
                if prestamo_activo:
                    data['prestamo_relacionado'] = prestamo_activo
                else:
                    raise serializers.ValidationError(
                        f"El usuario {usuario_autorizado.username} no está autorizado para usar este vehículo"
                    )

        return data


class RegistroAccesoCreateSerializer(serializers.Serializer):
    """Serializer simplificado para crear registros de acceso desde la cámara"""
    placa_detectada = serializers.CharField(max_length=20)
    tipo_acceso = serializers.ChoiceField(choices=RegistroAcceso.TIPO_ACCESO_CHOICES)
    confianza_deteccion = serializers.FloatField(min_value=0.0, max_value=1.0)
    foto_capturada = serializers.ImageField(required=False)
    observaciones = serializers.CharField(required=False, allow_blank=True)

    def validate_placa_detectada(self, value):
        """Buscar vehículo por placa detectada"""
        try:
            vehiculo = Vehiculo.objects.get(placa__iexact=value)
            self.vehiculo_encontrado = vehiculo
            return value.upper()
        except Vehiculo.DoesNotExist:
            raise serializers.ValidationError(f"No se encontró un vehículo registrado con la placa: {value}")

    def create(self, validated_data):
        """Crear registro de acceso automático"""
        placa = validated_data['placa_detectada']
        vehiculo = self.vehiculo_encontrado
        vigilante = self.context['request'].user

        # Determinar usuario autorizado (propietario o prestatario activo)
        usuario_autorizado = vehiculo.usuario
        prestamo_relacionado = None

        # Buscar préstamo activo
        prestamo_activo = PrestamoVehiculo.objects.filter(
            vehiculo=vehiculo,
            estado='activo',
            fecha_inicio__lte=timezone.now(),
            fecha_fin__gte=timezone.now()
        ).first()

        if prestamo_activo:
            usuario_autorizado = prestamo_activo.prestatario
            prestamo_relacionado = prestamo_activo

        # Crear registro
        registro = RegistroAcceso.objects.create(
            vehiculo=vehiculo,
            usuario_autorizado=usuario_autorizado,
            vigilante=vigilante,
            tipo_acceso=validated_data['tipo_acceso'],
            metodo='automatico',
            placa_detectada=placa,
            confianza_deteccion=validated_data['confianza_deteccion'],
            foto_capturada=validated_data.get('foto_capturada'),
            placa_coincide=True,
            prestamo_relacionado=prestamo_relacionado,
            observaciones=validated_data.get('observaciones', '')
        )

        return registro