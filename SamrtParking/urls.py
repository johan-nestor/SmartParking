"""
URL configuration for SamrtParking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from usuarios.views import landing_page
from django.http import HttpResponse
from django.views.decorators.http import require_GET

@require_GET
def favicon(request):
    # SVG favicon simple
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="50" fill="#059669"/>
    <text x="50" y="65" font-family="Arial" font-size="60" fill="white" text-anchor="middle" font-weight="bold">S</text>
    </svg>'''
    return HttpResponse(svg_content, content_type="image/svg+xml")

urlpatterns = [
    path('', landing_page, name='landing'),  # Ruta raíz para la landing
    path('favicon.ico', favicon, name='favicon'),  # Favicon
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('vehiculos/', include('vehiculos.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
