from django.core.management.base import BaseCommand
from usuarios.models import Rol


class Command(BaseCommand):
    help = 'Crea los roles por defecto del sistema'

    def handle(self, *args, **options):
        roles_data = [
            {
                'nombre': Rol.ADMINISTRADOR_GENERAL,
                'rol_por_defecto': False,
                'description': 'Administrador con acceso completo al sistema'
            },
            {
                'nombre': Rol.VIGILANTE,
                'rol_por_defecto': False,
                'description': 'Vigilante con acceso a registro de vehículos y cámara'
            },
            {
                'nombre': Rol.USUARIO,
                'rol_por_defecto': True,
                'description': 'Usuario regular del sistema'
            }
        ]

        for rol_data in roles_data:
            rol, created = Rol.objects.get_or_create(
                nombre=rol_data['nombre'],
                defaults={
                    'rol_por_defecto': rol_data['rol_por_defecto'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Rol "{rol.get_nombre_display()}" creado exitosamente')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Rol "{rol.get_nombre_display()}" ya existe')
                )

        # Asegurar que solo hay un rol por defecto
        roles_por_defecto = Rol.objects.filter(rol_por_defecto=True)
        if roles_por_defecto.count() > 1:
            # Dejar solo el rol 'usuario' como por defecto
            Rol.objects.filter(rol_por_defecto=True).exclude(nombre=Rol.USUARIO).update(rol_por_defecto=False)
            self.stdout.write(
                self.style.WARNING('Se encontraron múltiples roles por defecto. Se dejó solo "Usuario" como predeterminado.')
            )

        self.stdout.write(
            self.style.SUCCESS('Configuración de roles completada.')
        )