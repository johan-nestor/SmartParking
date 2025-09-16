from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    foto = models.ImageField(upload_to="fotos_perfil/", default="fotos_perfil/default.png")

    def __str__(self):
        return self.user.username
