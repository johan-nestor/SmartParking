from django.core.management.base import BaseCommand
from usuarios.models import Rol


class Command(BaseCommand):
    help = 'Inicializa los roles básicos del sistema'

    def handle(self, *args, **options):
        roles_basicos = [
            {
                'nombre': 'usuario',
                'rol_por_defecto': True,
                'descripcion': 'Usuario normal del sistema'
            },
            {
                'nombre': 'vigilante', 
                'rol_por_defecto': False,
                'descripcion': 'Vigilante de cochera con acceso a cámara y registro de accesos'
            },
            {
                'nombre': 'administrador_general',
                'rol_por_defecto': False, 
                'descripcion': 'Administrador general del sistema'
            }
        ]

        for rol_data in roles_basicos:
            rol, created = Rol.objects.get_or_create(
                nombre=rol_data['nombre'],
                defaults={
                    'rol_por_defecto': rol_data['rol_por_defecto'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Rol "{rol.nombre}" creado correctamente')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Rol "{rol.nombre}" ya existe')
                )

        # Asegurar que solo haya un rol por defecto
        Rol.objects.filter(rol_por_defecto=True).exclude(nombre='usuario').update(rol_por_defecto=False)
        Rol.objects.filter(nombre='usuario').update(rol_por_defecto=True)
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Inicialización de roles completada')
        )
        self.stdout.write(
            self.style.SUCCESS('📋 Roles disponibles:')
        )
        
        for rol in Rol.objects.all():
            default_text = " (por defecto)" if rol.rol_por_defecto else ""
            self.stdout.write(f'   - {rol.nombre}{default_text}')
            
        self.stdout.write(
            self.style.SUCCESS(f'\n💡 Para asignar roles use: python manage.py asignar_rol <username> <rol>')
        )