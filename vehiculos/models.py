from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Vehiculo(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehiculos')
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    placa = models.CharField(max_length=20, unique=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    foto_vehiculo = models.ImageField(upload_to='vehiculos/fotos/', blank=True, null=True)
    foto_placa = models.ImageField(upload_to='vehiculos/placas/', blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.placa})"

    class Meta:
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
        ordering = ['-fecha_registro']


class PrestamoVehiculo(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('activo', 'Activo'),
        ('finalizado', 'Finalizado'),
    ]

    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='prestamos')
    prestador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehiculos_prestados')
    prestatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehiculos_recibidos')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    motivo = models.TextField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Préstamo: {self.vehiculo.placa} - {self.prestatario.username}"

    @property
    def esta_activo(self):
        now = timezone.now()
        return (self.estado == 'activo' and 
                self.fecha_inicio <= now <= self.fecha_fin)

    class Meta:
        verbose_name = 'Préstamo de Vehículo'
        verbose_name_plural = 'Préstamos de Vehículos'
        ordering = ['-fecha_solicitud']


class RegistroAcceso(models.Model):
    TIPO_ACCESO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]

    METODO_CHOICES = [
        ('manual', 'Registro Manual'),
        ('automatico', 'Reconocimiento Automático'),
        ('mixto', 'Verificación Manual + Automática'),
    ]

    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='registros_acceso')
    usuario_autorizado = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='accesos_autorizados',
        help_text='Usuario autorizado para usar el vehículo (propietario o prestatario)'
    )
    vigilante = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='registros_vigilancia'
    )
    tipo_acceso = models.CharField(max_length=10, choices=TIPO_ACCESO_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    metodo = models.CharField(max_length=15, choices=METODO_CHOICES, default='manual')
    
    # Datos del reconocimiento de placa
    placa_detectada = models.CharField(max_length=20, blank=True, null=True)
    confianza_deteccion = models.FloatField(
        blank=True, null=True,
        help_text='Nivel de confianza de la detección (0.0 - 1.0)'
    )
    foto_capturada = models.ImageField(upload_to='accesos/fotos/', blank=True, null=True)
    
    # Validaciones
    placa_coincide = models.BooleanField(default=True)
    prestamo_relacionado = models.ForeignKey(
        PrestamoVehiculo, 
        on_delete=models.SET_NULL, 
        blank=True, null=True,
        help_text='Préstamo activo relacionado con este acceso'
    )
    
    # Observaciones
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo_acceso.title()} - {self.vehiculo.placa} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

    @property
    def es_acceso_autorizado(self):
        """Verifica si el acceso está autorizado considerando préstamos activos"""
        # El propietario siempre tiene acceso
        if self.usuario_autorizado == self.vehiculo.usuario:
            return True
        
        # Verificar préstamos activos
        if self.prestamo_relacionado and self.prestamo_relacionado.esta_activo:
            return self.usuario_autorizado == self.prestamo_relacionado.prestatario
        
        return False

    class Meta:
        verbose_name = 'Registro de Acceso'
        verbose_name_plural = 'Registros de Acceso'
        ordering = ['-timestamp']
