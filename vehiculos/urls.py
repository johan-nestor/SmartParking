from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para la API REST
router = DefaultRouter()
router.register(r'api', views.VehiculoViewSet, basename='vehiculo-api')

urlpatterns = [
    # URLs existentes
    path('', views.lista_vehiculos, name='lista_vehiculos'),
    path('agregar/', views.agregar_vehiculo, name='agregar_vehiculo'),
    path('editar/<int:vehiculo_id>/', views.editar_vehiculo, name='editar_vehiculo'),
    path('eliminar/<int:vehiculo_id>/', views.eliminar_vehiculo, name='eliminar_vehiculo'),
    
    # URLs de la API
    path('', include(router.urls)),
]
