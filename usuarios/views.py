from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import IntegrityError

from .forms import RegistroUsuarioForm
from .models import Perfil, Rol
from .serializers import RegistroSerializer
from vehiculos.models import Vehiculo

# Registro de usuario
def registro(request):
    if request.method == "POST":
        form = RegistroUsuarioForm(request.POST, request.FILES)  # importante: incluir archivos
        if form.is_valid():
            user = form.save()  # crea usuario en auth_user

            # Guardar datos extra en perfil
            if hasattr(user, 'perfil'):
                user.perfil.telefono = form.cleaned_data.get('telefono')
                user.perfil.direccion = form.cleaned_data.get('direccion')
                if form.cleaned_data.get('foto'):
                    user.perfil.foto = form.cleaned_data.get('foto')
                user.perfil.save()

            login(request, user)  # iniciar sesión directo
            return redirect('dashboard')
    else:
        form = RegistroUsuarioForm()
    return render(request, "usuarios/registro.html", {"form": form})

# Login de usuario
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "usuarios/login.html", {"error": "Usuario o contraseña incorrectos"})
    return render(request, "usuarios/login.html")

# Logout
def logout_view(request):
    logout(request)
    return redirect("login")

# Dashboard
@login_required(login_url="login")
def dashboard(request):
    """
    Muestra el dashboard principal con resumen del usuario y enlace a la gestión de vehículos.
    """
    vehiculos = request.user.vehiculos.all()  # Vehículos del usuario logueado
    return render(request, "usuarios/dashboard.html", {
        "vehiculos": vehiculos
    })

# Formulario para editar perfil
class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["telefono", "direccion", "foto"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

# Editar perfil
@login_required(login_url="login")
def editar_perfil(request):
    perfil = request.user.perfil  # obtenemos el perfil del usuario logueado
    if request.method == "POST":
        form = EditarPerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Tu perfil se actualizó correctamente ✅")
            return redirect("perfil")  # redirige a la vista del perfil
    else:
        form = EditarPerfilForm(instance=perfil)

    return render(request, "usuarios/editar_perfil.html", {"form": form})

# Ver perfil
@login_required(login_url="login")
def perfil(request):
    perfil = request.user.perfil
    return render(request, "usuarios/perfil.html", {"perfil": perfil})

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def registro_api(request):
    serializer = RegistroSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generar tokens JWT
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'detail': 'Usuario registrado con éxito',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def obtener_roles(request):
    """Obtiene lista de roles disponibles para registro"""
    from .models import Rol
    
    roles = Rol.objects.filter(is_active=True).values('id', 'nombre')
    roles_formateados = []
    
    for rol in roles:
        roles_formateados.append({
            'id': rol['id'],
            'nombre': rol['nombre'],
            'display_name': dict(Rol.ROL_CHOICES).get(rol['nombre'], rol['nombre'])
        })
    
    return Response(roles_formateados)


@api_view(['GET'])
def perfil_usuario(request):
    """Obtiene perfil del usuario autenticado"""
    if not request.user.is_authenticated:
        return Response(
            {'detail': 'No autenticado'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        perfil = request.user.perfil
        return Response({
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            },
            'perfil': {
                'telefono': perfil.telefono,
                'direccion': perfil.direccion,
                'foto': perfil.foto.url if perfil.foto else None,
                'rol': {
                    'id': perfil.rol.id if perfil.rol else None,
                    'nombre': perfil.rol.nombre if perfil.rol else None,
                    'display_name': perfil.rol.get_nombre_display() if perfil.rol else None,
                }
            }
        })
    except Perfil.DoesNotExist:
        return Response(
            {'detail': 'Perfil no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def listar_usuarios(request):
    """Lista todos los usuarios - solo para administradores"""
    # Verificar permisos de administrador
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol:
        return Response(
            {'error': 'No tienes permisos de administrador'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.user.perfil.rol.nombre != 'administrador_general':
        return Response(
            {'error': 'Solo los administradores pueden ver la lista de usuarios'}, 
            status=status.HTTP_403_FORBIDDEN
        )

    usuarios = User.objects.all().select_related('perfil', 'perfil__rol')
    usuarios_data = []
    
    for user in usuarios:
        try:
            perfil = user.perfil
            usuario_info = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'date_joined': user.date_joined,
                'perfil': {
                    'telefono': perfil.telefono,
                    'direccion': perfil.direccion,
                    'rol': {
                        'id': perfil.rol.id if perfil.rol else None,
                        'nombre': perfil.rol.nombre if perfil.rol else None,
                        'display_name': perfil.rol.get_nombre_display() if perfil.rol else None,
                    }
                }
            }
            usuarios_data.append(usuario_info)
        except Perfil.DoesNotExist:
            # Usuario sin perfil
            usuario_info = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'date_joined': user.date_joined,
                'perfil': None
            }
            usuarios_data.append(usuario_info)
    
    return Response(usuarios_data)


@api_view(['POST'])
def cambiar_rol_usuario(request):
    """Cambia el rol de un usuario - solo para administradores"""
    # Verificar permisos de administrador
    if not hasattr(request.user, 'perfil') or not request.user.perfil.rol:
        return Response(
            {'error': 'No tienes permisos de administrador'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.user.perfil.rol.nombre != 'administrador_general':
        return Response(
            {'error': 'Solo los administradores pueden cambiar roles'}, 
            status=status.HTTP_403_FORBIDDEN
        )

    user_id = request.data.get('user_id')
    nuevo_rol_id = request.data.get('rol_id')
    
    if not user_id or not nuevo_rol_id:
        return Response(
            {'error': 'Se requieren user_id y rol_id'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Obtener usuario y rol
        usuario = User.objects.get(id=user_id)
        nuevo_rol = Rol.objects.get(id=nuevo_rol_id)
        
        # No permitir cambiar el rol del propio administrador
        if usuario == request.user:
            return Response(
                {'error': 'No puedes cambiar tu propio rol'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener o crear perfil
        perfil, created = Perfil.objects.get_or_create(user=usuario)
        rol_anterior = perfil.rol
        
        # Cambiar rol
        perfil.rol = nuevo_rol
        perfil.save()
        
        return Response({
            'message': f'Rol cambiado exitosamente',
            'usuario': usuario.username,
            'rol_anterior': rol_anterior.get_nombre_display() if rol_anterior else 'Sin rol',
            'rol_nuevo': nuevo_rol.get_nombre_display(),
        })
        
    except User.DoesNotExist:
        return Response(
            {'error': 'Usuario no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Rol.DoesNotExist:
        return Response(
            {'error': 'Rol no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error interno: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
