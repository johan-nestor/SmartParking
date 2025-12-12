from .camera_views import video_feed, monitor_view, camera_status
from .vigilante_views import (
    dashboard_vigilante, camara_vigilante, registro_acceso_vigilante,
    buscar_vehiculo_vigilante, vehiculos_cochera_vigilante,
    vigilante_estadisticas, vigilante_detectar_placa,
    vigilante_registrar_acceso, vigilante_buscar_vehiculo,
    vigilante_vehiculos_cochera
)
from .vehicle_views import (
    lista_vehiculos, agregar_vehiculo, editar_vehiculo,
    eliminar_vehiculo, registrar_acceso_manual
)
from .api_views import (
    VehiculoViewSet, PrestamoVehiculoViewSet,
    RegistroAccesoViewSet, registrar_acceso_automatico
)

__all__ = [
    'video_feed', 'monitor_view', 'camera_status',
    'dashboard_vigilante', 'camara_vigilante', 'registro_acceso_vigilante',
    'buscar_vehiculo_vigilante', 'vehiculos_cochera_vigilante',
    'vigilante_estadisticas', 'vigilante_detectar_placa',
    'vigilante_registrar_acceso', 'vigilante_buscar_vehiculo',
    'vigilante_vehiculos_cochera',
    'lista_vehiculos', 'agregar_vehiculo', 'editar_vehiculo',
    'eliminar_vehiculo',
    'VehiculoViewSet', 'PrestamoVehiculoViewSet',
    'RegistroAccesoViewSet', 'registrar_acceso_automatico'
]