from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_vehiculos, name='lista_vehiculos'),
    path('agregar/', views.agregar_vehiculo, name='agregar_vehiculo'),
    path('editar/<int:vehiculo_id>/', views.editar_vehiculo, name='editar_vehiculo'),
    path('eliminar/<int:vehiculo_id>/', views.eliminar_vehiculo, name='eliminar_vehiculo'),
]
