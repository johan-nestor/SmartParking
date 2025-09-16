from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Perfil


class RegistroUsuarioForm(UserCreationForm):
    telefono = forms.CharField(max_length=20, required=False)
    direccion = forms.CharField(max_length=200, required=False)
    foto = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "telefono", "direccion", "foto"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases Bootstrap a los campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["telefono", "direccion", "foto"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
