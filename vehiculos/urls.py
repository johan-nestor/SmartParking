from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para la API REST
router = DefaultRouter()
router.register(r'api/vehiculos', views.VehiculoViewSet, basename='vehiculo-api')
router.register(r'api/prestamos', views.PrestamoVehiculoViewSet, basename='prestamo-api')
router.register(r'api/accesos', views.RegistroAccesoViewSet, basename='acceso-api')

urlpatterns = [
    # URLs existentes (vistas HTML)
    path('', views.lista_vehiculos, name='lista_vehiculos'),
    path('agregar/', views.agregar_vehiculo, name='agregar_vehiculo'),
    path('editar/<int:vehiculo_id>/', views.editar_vehiculo, name='editar_vehiculo'),
    path('eliminar/<int:vehiculo_id>/', views.eliminar_vehiculo, name='eliminar_vehiculo'),
    
    # ===== VISTAS HTML PARA VIGILANTES =====
    path('vigilante/dashboard/', views.dashboard_vigilante, name='dashboard_vigilante'),
    path('vigilante/camara/', views.camara_vigilante, name='camara_vigilante'),
    path('vigilante/registro-acceso/', views.registro_acceso_vigilante, name='registro_acceso_vigilante'),
    path('vigilante/buscar-vehiculo/', views.buscar_vehiculo_vigilante, name='buscar_vehiculo_vigilante'),
    path('vigilante/vehiculos-cochera/', views.vehiculos_cochera_vigilante, name='vehiculos_cochera_vigilante'),
    
    # ===== ENDPOINTS ESPECÍFICOS PARA VIGILANTES (API) =====
    path('api/vigilante/estadisticas/', views.vigilante_estadisticas, name='vigilante_estadisticas'),
    path('api/vigilante/detectar-placa/', views.vigilante_detectar_placa, name='vigilante_detectar_placa'),
    path('api/vigilante/registrar-acceso/', views.vigilante_registrar_acceso, name='vigilante_registrar_acceso'),
    path('api/vigilante/vehiculos-cochera/', views.vigilante_vehiculos_cochera, name='vigilante_vehiculos_cochera'),
    path('api/vigilante/buscar-vehiculo/', views.vigilante_buscar_vehiculo, name='vigilante_buscar_vehiculo'),

    # ===== CAMARA =====
    path('monitor/', views.monitor_view, name='monitor'),
    path('video_feed/', views.video_feed, name='video_feed'),
    
    # URLs del router
    path('', include(router.urls)),
]
