from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Perfil
from .models import Rol

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        perfil = Perfil.objects.create(user=instance)
        # Si existe un rol marcado como por defecto, asignarlo
        rol_def = Rol.objects.filter(rol_por_defecto=True, is_active=True).first()
        if rol_def:
            perfil.rol = rol_def
            perfil.save()

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    instance.perfil.save()

