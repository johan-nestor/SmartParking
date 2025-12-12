from django.db import models
from django.contrib.auth.models import User


class Perfil(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )

    # === DATOS PERSONALES ===
    dni = models.CharField(
        max_length=8,
        unique=True,
        blank=True,     # ← Permite vacío
        null=True,      # ← Permite NULL en BD
        help_text="DNI del usuario (8 dígitos)"
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Teléfono del usuario"
    )

    direccion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Dirección del usuario"
    )

    foto = models.ImageField(
        upload_to='fotos_perfil/',
        default='fotos_perfil/default.png',
        blank=True,
        null=True
    )

    # === ROL ===
    rol = models.ForeignKey(
        'usuarios.Rol',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios'
    )

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.username})"

    def get_nombre_completo(self):
        return self.user.get_full_name().strip() or self.user.username

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuarios"
        ordering = ['user__first_name', 'user__last_name']


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
        return self.get_nombre_display()