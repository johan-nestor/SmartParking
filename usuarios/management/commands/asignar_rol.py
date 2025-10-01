from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from usuarios.models import Perfil, Rol


class Command(BaseCommand):
    help = 'Asigna roles a usuarios del sistema'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario')
        parser.add_argument('rol', type=str, choices=['vigilante', 'usuario', 'administrador_general'], 
                           help='Rol a asignar')

    def handle(self, *args, **options):
        username = options['username']
        rol_nombre = options['rol']

        try:
            # Buscar usuario
            user = User.objects.get(username=username)
            
            # Obtener o crear perfil
            perfil, created = Perfil.objects.get_or_create(user=user)
            
            # Obtener rol
            rol = Rol.objects.get(nombre=rol_nombre)
            
            # Asignar rol
            perfil.rol = rol
            perfil.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Rol "{rol_nombre}" asignado correctamente al usuario "{username}"'
                )
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Usuario "{username}" no encontrado')
            )
        except Rol.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Rol "{rol_nombre}" no encontrado')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )