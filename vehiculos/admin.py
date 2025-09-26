from django.contrib import admin
from .models import Vehiculo, PrestamoVehiculo, RegistroAcceso


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ['placa', 'marca', 'modelo', 'usuario', 'fecha_registro']
    list_filter = ['marca', 'fecha_registro']
    search_fields = ['placa', 'marca', 'modelo', 'usuario__username']
    readonly_fields = ['fecha_registro']


@admin.register(PrestamoVehiculo)
class PrestamoVehiculoAdmin(admin.ModelAdmin):
    list_display = ['vehiculo', 'prestador', 'prestatario', 'fecha_inicio', 'fecha_fin', 'estado']
    list_filter = ['estado', 'fecha_solicitud', 'fecha_inicio']
    search_fields = ['vehiculo__placa', 'prestador__username', 'prestatario__username']
    readonly_fields = ['fecha_solicitud']
    
    fieldsets = (
        ('Información del Préstamo', {
            'fields': ('vehiculo', 'prestador', 'prestatario')
        }),
        ('Fechas', {
            'fields': ('fecha_solicitud', 'fecha_inicio', 'fecha_fin')
        }),
        ('Estado y Observaciones', {
            'fields': ('estado', 'motivo', 'notas')
        }),
    )


@admin.register(RegistroAcceso)
class RegistroAccesoAdmin(admin.ModelAdmin):
    list_display = ['vehiculo', 'tipo_acceso', 'timestamp', 'vigilante', 'usuario_autorizado', 'placa_coincide']
    list_filter = ['tipo_acceso', 'timestamp', 'metodo', 'placa_coincide']
    search_fields = ['vehiculo__placa', 'placa_detectada', 'vigilante__username', 'usuario_autorizado__username']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('vehiculo', 'usuario_autorizado', 'vigilante', 'tipo_acceso', 'timestamp')
        }),
        ('Detección Automática', {
            'fields': ('metodo', 'placa_detectada', 'confianza_deteccion', 'placa_coincide')
        }),
        ('Archivos', {
            'fields': ('foto_capturada',)
        }),
        ('Validación y Observaciones', {
            'fields': ('prestamo_relacionado', 'observaciones')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Los administradores ven todo, otros usuarios solo sus registros
        if request.user.is_superuser:
            return qs
        return qs.filter(vigilante=request.user)
