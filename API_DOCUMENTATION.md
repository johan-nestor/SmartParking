# SmartParking - Documentación API para Frontend Vue.js 3

## Autenticación

Todas las APIs requieren autenticación JWT. Incluye en los headers:
```javascript
headers: {
  'Authorization': `Bearer ${access_token}`,
  'Content-Type': 'application/json'
}
```

## Endpoints Base

- **Base URL**: `http://localhost:8000`
- **API Base**: `/api/`

---

## 🔐 AUTENTICACIÓN

### 1. Registro de Usuario
```http
POST /usuarios/api/registro/
```

**Body:**
```json
{
  "username": "usuario123",
  "password": "password123",
  "password_confirm": "password123",
  "email": "usuario@email.com",
  "first_name": "Juan",
  "last_name": "Pérez"
}
```

**Response Success (201):**
```json
{
  "user": {
    "id": 1,
    "username": "usuario123",
    "email": "usuario@email.com",
    "first_name": "Juan",
    "last_name": "Pérez"
  },
  "perfil": {
    "rol": "usuario"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1Q...",
    "refresh": "eyJ0eXAiOiJKV1Q..."
  },
  "message": "Usuario registrado correctamente"
}
```

### 2. Login
```http
POST /api/token/
```

**Body:**
```json
{
  "username": "usuario123",
  "password": "password123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1Q...",
  "refresh": "eyJ0eXAiOiJKV1Q..."
}
```

### 3. Refresh Token
```http
POST /api/token/refresh/
```

---

## 👤 GESTIÓN DE USUARIOS (Solo Administradores)

### 4. Listar Usuarios
```http
GET /usuarios/api/admin/usuarios/
```

**Response:**
```json
[
  {
    "id": 1,
    "username": "usuario123",
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@email.com",
    "rol": "usuario",
    "fecha_registro": "2024-01-15T10:30:00Z"
  }
]
```

### 5. Cambiar Rol de Usuario
```http
POST /usuarios/api/admin/cambiar-rol/
```

**Body:**
```json
{
  "usuario_id": 1,
  "nuevo_rol": "vigilante"
}
```

---

## 🚗 GESTIÓN DE VEHÍCULOS

### 6. Listar Vehículos del Usuario
```http
GET /vehiculos/api/vehiculos/
```

### 7. Crear Vehículo
```http
POST /vehiculos/api/vehiculos/
```

**Body:**
```json
{
  "placa": "ABC123",
  "marca": "Toyota",
  "modelo": "Corolla",
  "anio": 2020,
  "color": "Blanco"
}
```

### 8. Actualizar Vehículo
```http
PUT /vehiculos/api/vehiculos/{id}/
```

### 9. Eliminar Vehículo
```http
DELETE /vehiculos/api/vehiculos/{id}/
```

---

## 🤝 PRÉSTAMOS DE VEHÍCULOS

### 10. Crear Solicitud de Préstamo
```http
POST /vehiculos/api/prestamos/
```

**Body:**
```json
{
  "vehiculo": 1,
  "fecha_inicio": "2024-01-20",
  "fecha_fin": "2024-01-22",
  "motivo": "Viaje de trabajo"
}
```

### 11. Listar Préstamos
```http
GET /vehiculos/api/prestamos/
```

**Query Parameters:**
- `estado`: `pendiente`, `aprobado`, `rechazado`
- `usuario_solicitante`: ID del usuario

### 12. Aprobar/Rechazar Préstamo
```http
PATCH /vehiculos/api/prestamos/{id}/
```

**Body:**
```json
{
  "estado": "aprobado"  // o "rechazado"
}
```

---

## 🛡️ ENDPOINTS PARA VIGILANTES

### 13. Estadísticas Dashboard
```http
GET /vehiculos/api/vigilante/estadisticas/
```

**Response:**
```json
{
  "entradas_hoy": 5,
  "salidas_hoy": 3,
  "vehiculos_en_cochera": 2,
  "registros_hoy": 8,
  "ultimo_registro": {
    "placa": "XYZ789",
    "tipo": "entrada",
    "hora": "14:30"
  },
  "fecha": "2024-01-20"
}
```

### 14. Detectar Placa con Cámara
```http
POST /vehiculos/api/vigilante/detectar-placa/
```

**Response Success:**
```json
{
  "success": true,
  "plates_detected": ["ABC123"],
  "confidence_scores": [0.85],
  "timestamp": "2024-01-20T14:30:00Z",
  "message": "Detectada(s) 1 placa(s)"
}
```

**Response No Detection:**
```json
{
  "success": false,
  "plates_detected": [],
  "message": "No se detectaron placas en este momento"
}
```

### 15. Registrar Acceso (Entrada/Salida)
```http
POST /vehiculos/api/vigilante/registrar-acceso/
```

**Body (Form Data):**
```
placa_detectada: "ABC123"
tipo_acceso: "entrada"  // o "salida"
confianza_deteccion: "0.85"
observaciones: "Detección automática"
```

**Response Success:**
```json
{
  "success": true,
  "registro_id": 123,
  "mensaje": "Entrada registrada correctamente",
  "vehiculo": {
    "placa": "ABC123",
    "propietario": "Juan Pérez",
    "usuario_autorizado": "María García",
    "es_prestamo": true
  },
  "registro": {
    "tipo_acceso": "entrada",
    "timestamp": "2024-01-20T14:30:00Z",
    "confianza": 0.85
  }
}
```

### 16. Vehículos en Cochera
```http
GET /vehiculos/api/vigilante/vehiculos-cochera/
```

**Response:**
```json
{
  "vehiculos_en_cochera": [
    {
      "vehiculo_id": 1,
      "placa": "ABC123",
      "propietario": "Juan Pérez",
      "usuario_autorizado": "María García",
      "hora_entrada": "10:30",
      "tiempo_estacionado": "4:15:22",
      "es_prestamo": true
    }
  ],
  "total": 1,
  "fecha": "2024-01-20"
}
```

### 17. Buscar Vehículo por Placa
```http
GET /vehiculos/api/vigilante/buscar-vehiculo/?placa=ABC123
```

**Response Found:**
```json
{
  "encontrado": true,
  "vehiculo": {
    "id": 1,
    "placa": "ABC123",
    "marca": "Toyota",
    "modelo": "Corolla",
    "color": "Blanco",
    "propietario": "Juan Pérez",
    "propietario_username": "juan123"
  },
  "prestamo_activo": {
    "usuario_autorizado": "María García",
    "fecha_inicio": "2024-01-20",
    "fecha_fin": "2024-01-22",
    "motivo": "Viaje de trabajo"
  },
  "ultimo_acceso": {
    "tipo": "entrada",
    "timestamp": "2024-01-20T10:30:00Z",
    "vigilante": "vigilante1"
  },
  "esta_en_cochera": true
}
```

---

## 📊 REGISTROS DE ACCESO

### 18. Listar Registros de Acceso
```http
GET /vehiculos/api/accesos/
```

**Query Parameters:**
- `limit`: Número de resultados por página
- `tipo_acceso`: `entrada` o `salida`
- `fecha`: `YYYY-MM-DD`
- `vehiculo__placa`: Filtrar por placa

### 19. Estadísticas Generales
```http
GET /vehiculos/api/accesos/estadisticas/
```

---

## 🔧 CONFIGURACIÓN CORS

Para tu frontend Vue 3, asegúrate de que Django tenga configurado CORS:

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Vue dev server
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True
```

---

## 📝 EJEMPLO DE USO EN VUE 3

### Composable para API calls:

```javascript
// composables/useApi.js
import { ref } from 'vue'

export function useApi() {
  const loading = ref(false)
  const error = ref(null)

  const getAuthHeaders = () => ({
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'Content-Type': 'application/json'
  })

  const apiCall = async (url, options = {}) => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`http://localhost:8000${url}`, {
        ...options,
        headers: {
          ...getAuthHeaders(),
          ...options.headers
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      return await response.json()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // Métodos específicos
  const vigilanteStats = () => apiCall('/vehiculos/api/vigilante/estadisticas/')
  
  const detectarPlaca = () => apiCall('/vehiculos/api/vigilante/detectar-placa/', {
    method: 'POST'
  })

  const registrarAcceso = (data) => {
    const formData = new FormData()
    Object.entries(data).forEach(([key, value]) => {
      formData.append(key, value)
    })

    return apiCall('/vehiculos/api/vigilante/registrar-acceso/', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
      body: formData
    })
  }

  return {
    loading,
    error,
    apiCall,
    vigilanteStats,
    detectarPlaca,
    registrarAcceso
  }
}
```

### Componente de Dashboard:

```vue
<!-- components/VigilanteDashboard.vue -->
<template>
  <div class="dashboard">
    <div class="stats-grid">
      <div class="stat-card">
        <h3>{{ stats.entradas_hoy }}</h3>
        <p>Entradas Hoy</p>
      </div>
      <div class="stat-card">
        <h3>{{ stats.salidas_hoy }}</h3>
        <p>Salidas Hoy</p>
      </div>
      <!-- Más stats... -->
    </div>
    
    <div class="camera-section">
      <video ref="cameraRef" autoplay></video>
      <button @click="detectarPlaca">Detectar Placa</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'

const stats = ref({})
const cameraRef = ref(null)
const { vigilanteStats, detectarPlaca } = useApi()

onMounted(async () => {
  // Cargar estadísticas iniciales
  stats.value = await vigilanteStats()
  
  // Inicializar cámara
  const stream = await navigator.mediaDevices.getUserMedia({ video: true })
  cameraRef.value.srcObject = stream
})
</script>
```

---

## ⚠️ NOTAS IMPORTANTES

1. **Roles**: Solo usuarios con rol `vigilante` pueden acceder a endpoints `/api/vigilante/`
2. **Autenticación**: Todos los endpoints requieren JWT token válido
3. **YOLO**: Asegúrate de tener instaladas las dependencias: `ultralytics`, `opencv-python`, `torch`
4. **Cámara**: Los navegadores requieren HTTPS en producción para acceso a cámara
5. **WebRTC**: Para streaming en tiempo real, considera implementar WebSocket para el feed de cámara

---

## 🚀 PRÓXIMOS PASOS

1. Ejecutar `python manage.py setup_roles` para crear roles por defecto
2. Configurar tu frontend Vue 3 con estos endpoints
3. Implementar componentes de cámara y dashboard
4. Entrenar modelo YOLO personalizado para placas chilenas/locales