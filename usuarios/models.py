from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    foto = models.ImageField(upload_to="fotos_perfil/", default="fotos_perfil/default.png")
    # Referencia por cadena para evitar problemas de importación (Rol definido más abajo)
    rol = models.ForeignKey(
        'usuarios.Rol',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
    )
    def __str__(self):
        return self.user.username

class Rol(models.Model):
    """
    Modelo para gestionar los roles de usuario en el sistema.
    """
    ADMINISTRADOR_GENERAL = 'administrador_general'
    VIGILANTE = 'vigilante'
    USUARIO = 'usuario'
    
    ROL_CHOICES = [
        (ADMINISTRADOR_GENERAL, 'Administrador General'),
        (VIGILANTE, 'Vigilante'),
        (USUARIO, 'Usuario'),
    ]

    nombre = models.CharField(
        max_length=50, 
        unique=True,
        choices=ROL_CHOICES,
        verbose_name='Nombre del Rol',
    )

    rol_por_defecto = models.BooleanField(
        default=False, 
        verbose_name='Rol por Defecto',
        help_text='Indica si este rol es el rol por defecto para nuevos usuarios.'
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'rol_rol'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(fields=['nombre'], name='unique_rol_nombre')
        ]
    
    def __str__(self):
        # Devuelve la etiqueta amigable definida en choices
        return self.get_nombre_display()