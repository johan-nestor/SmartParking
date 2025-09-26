from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Perfil, Rol


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['telefono', 'direccion', 'foto', 'rol']


class RegistroSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    telefono = serializers.CharField(max_length=20, allow_blank=True, required=False)
    direccion = serializers.CharField(max_length=200, allow_blank=True, required=False)
    foto = serializers.ImageField(required=False, allow_null=True)
    # role puede ser id del Rol o nombre
    role = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data.get('password') != data.get('password2'):
            raise serializers.ValidationError("Las contraseñas no coinciden")
        if User.objects.filter(username=data.get('username')).exists():
            raise serializers.ValidationError({"username": "Este nombre de usuario ya está en uso"})
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({"email": "Este correo ya está registrado"})
        return data

    def create(self, validated_data):
        username = validated_data.get('username')
        email = validated_data.get('email')
        password = validated_data.get('password')
        telefono = validated_data.get('telefono', '')
        direccion = validated_data.get('direccion', '')
        foto = validated_data.get('foto', None)
        role_val = validated_data.get('role', '')

        user = User.objects.create_user(username=username, email=email, password=password)

        # signals.post_save crea Perfil automáticamente; refrescamos
        try:
            perfil = user.perfil
        except Perfil.DoesNotExist:
            perfil = Perfil.objects.create(user=user)

        perfil.telefono = telefono
        perfil.direccion = direccion
        if foto:
            perfil.foto = foto

        # Asignar rol si se proporciona (por id o por nombre)
        if role_val:
            rol_obj = None
            # probar por id
            try:
                rol_obj = Rol.objects.get(pk=int(role_val))
            except Exception:
                # probar por nombre
                rol_obj = Rol.objects.filter(nombre__iexact=role_val).first()

            if rol_obj:
                perfil.rol = rol_obj

        perfil.save()
        return user
