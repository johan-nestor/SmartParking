from rest_framework import serializers
from .models import Vehiculo

class VehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = ['id', 'marca', 'modelo', 'placa', 'color', 'foto_vehiculo', 'foto_placa', 'fecha_registro']