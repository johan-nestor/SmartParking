from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib import messages

from .forms import RegistroUsuarioForm
from .models import Perfil
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
