from django.db import models
from django.contrib.auth.models import User

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
