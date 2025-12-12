from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views.vehicle_views import registrar_acceso_manual, buscar_vehiculo_vigilante, buscar_vehiculo_por_placa


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
    path("vigilante/buscar-vehiculo/", buscar_vehiculo_vigilante, name="buscar_vehiculo_vigilante"),
    path('vigilante/vehiculos-cochera/', views.vehiculos_cochera_vigilante, name='vehiculos_cochera_vigilante'),
    
    
    # ===== ENDPOINTS ESPECÍFICOS PARA VIGILANTES (API) =====
    path('api/vigilante/estadisticas/', views.vigilante_estadisticas, name='vigilante_estadisticas'),
    path('api/vigilante/detectar-placa/', views.vigilante_detectar_placa, name='vigilante_detectar_placa'),
    path('api/vigilante/registrar-acceso/', views.vigilante_registrar_acceso, name='vigilante_registrar_acceso'),
    path('api/vigilante/vehiculos-cochera/', views.vigilante_vehiculos_cochera, name='vigilante_vehiculos_cochera'),
    path('api/registrar-acceso-manual/', views.registrar_acceso_manual, name='registrar_acceso_manual'),
    path('api/vehiculo/<str:placa>/', buscar_vehiculo_por_placa, name='buscar_vehiculo_por_placa'),


    # ===== CAMARA =====
    path('monitor/', views.monitor_view, name='monitor'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('video_feed_status/', views.camera_status, name='camera_status'),

        
    # URLs del router
    path('', include(router.urls)),
]
