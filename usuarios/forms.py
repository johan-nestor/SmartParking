from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Perfil


class RegistroUsuarioForm(UserCreationForm):
    # Campos del User
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Nombre'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Apellido'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Correo electrónico'})
    )

    # Campos del Perfil
    dni = forms.CharField(
        max_length=8,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'DNI (8 dígitos)'})
    )
    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Teléfono'})
    )
    direccion = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Dirección'})
    )
    foto = forms.ImageField(
        required=False,
        widget=forms.FileInput()
    )

    class Meta:
        model = User
        fields = [
            "username", "email", "first_name", "last_name",
            "password1", "password2",
            "dni", "telefono", "direccion", "foto"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Clases Bootstrap
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        # Personalizar labels
        self.fields['username'].label = "Nombre de usuario"
        self.fields['email'].label = "Correo electrónico"
        self.fields['first_name'].label = "Nombre"
        self.fields['last_name'].label = "Apellido"
        self.fields['password1'].label = "Contraseña"
        self.fields['password2'].label = "Confirmar contraseña"

    # === VALIDACIÓN PERSONALIZADA ===
    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if not dni.isdigit():
            raise forms.ValidationError("El DNI solo debe contener números.")
        if len(dni) != 8:
            raise forms.ValidationError("El DNI debe tener exactamente 8 dígitos.")
        if Perfil.objects.filter(dni=dni).exists():
            raise forms.ValidationError("Este DNI ya está registrado.")
        return dni

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está en uso.")
        return email

    # === GUARDAR USUARIO + PERFIL ===
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            # Crear Perfil
            Perfil.objects.create(
                user=user,
                dni=self.cleaned_data['dni'],
                telefono=self.cleaned_data.get('telefono', ''),
                direccion=self.cleaned_data.get('direccion', ''),
                foto=self.cleaned_data.get('foto'),
                rol=None  # Asignar rol por defecto o en vista
            )
        return user

class EditarPerfilForm(forms.ModelForm):
    # Campos del User
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'})
    )

    class Meta:
        model = Perfil
        fields = ['first_name', 'last_name', 'dni', 'rol']  # SOLO campos que EXISTEN en Perfil
        widgets = {
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DNI (8 dígitos)'}),
            'rol': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

        # Aplicar clases a todos
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        perfil = super().save(commit=False)
        user = perfil.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            perfil.save()
        return perfil