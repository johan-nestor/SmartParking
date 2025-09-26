from django.urls import path
from . import views
from .views import editar_perfil
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),

    # Rutas API
    path('api/registro/', views.registro_api, name='registro_api'),
    path('api/roles/', views.obtener_roles, name='obtener_roles'),
    path('api/perfil/', views.perfil_usuario, name='perfil_usuario'),
    
    # Rutas para administradores
    path('api/admin/usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('api/admin/cambiar-rol/', views.cambiar_rol_usuario, name='cambiar_rol_usuario'),
    
    # Autenticación
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
