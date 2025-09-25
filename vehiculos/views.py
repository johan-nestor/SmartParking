from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Vehiculo
from .forms import VehiculoForm

# Importaciones para API REST
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import VehiculoSerializer

# Vistas existentes para renderizado HTML
@login_required
def lista_vehiculos(request):
    vehiculos = request.user.vehiculos.all()
    return render(request, 'vehiculos/lista_vehiculos.html', {'vehiculos': vehiculos})

@login_required
def agregar_vehiculo(request):
    if request.method == 'POST':
        form = VehiculoForm(request.POST, request.FILES)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.usuario = request.user
            vehiculo.save()
            messages.success(request, "Vehículo agregado correctamente ✅")
            return redirect('lista_vehiculos')
    else:
        form = VehiculoForm()
    return render(request, 'vehiculos/agregar_vehiculo.html', {'form': form})

@login_required
def editar_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, usuario=request.user)
    if request.method == 'POST':
        form = VehiculoForm(request.POST, request.FILES, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo actualizado correctamente ✅")
            return redirect('lista_vehiculos')
    else:
        form = VehiculoForm(instance=vehiculo)
    return render(request, 'vehiculos/editar_vehiculo.html', {'form': form})

@login_required
def eliminar_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, usuario=request.user)
    if request.method == 'POST':
        vehiculo.delete()
        messages.success(request, "Vehículo eliminado correctamente ✅")
        return redirect('lista_vehiculos')
    return render(request, 'vehiculos/eliminar_vehiculo.html', {'vehiculo': vehiculo})

# Vistas para API REST
class VehiculoViewSet(viewsets.ModelViewSet):
    serializer_class = VehiculoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Solo devuelve los vehículos del usuario actual
        return self.request.user.vehiculos.all()
    
    def perform_create(self, serializer):
        # Asigna el usuario actual al crear un nuevo vehículo
        serializer.save(usuario=self.request.user)
