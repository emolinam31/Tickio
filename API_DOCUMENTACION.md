# 📚 Documentación API REST - TICKIO

## Introducción

Bienvenido a la **API REST de TICKIO**. Esta es una interfaz para gestionar eventos, boletos y órdenes de compra de manera programática. Puedes consumir esta API desde cualquier aplicación web, móvil o de escritorio.

---

## 🚀 Inicio Rápido

### 1. Iniciar el Servidor

Abre la terminal en la carpeta `Tickio_project` y ejecuta:

```bash
cd Tickio_project
uvicorn api_app:app --reload --port 8001
```

**Resultado esperado:**
```
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
```

### 2. Acceder a la API

Abre tu navegador en:

- **Inicio de la API:** http://localhost:8001
- **Documentación interactiva:** http://localhost:8001/api/docs
- **Listado de eventos:** http://localhost:8001/api/v1/eventos/

---

## 📋 ¿Qué Hace Esta API?

La API TICKIO permite:

| Funcionalidad | Descripción |
|--------------|-------------|
| **Listar Eventos** | Obtener todos los eventos disponibles con filtros |
| **Buscar Eventos** | Búsqueda avanzada por nombre, categoría, precio, fecha |
| **Detalles de Evento** | Información completa de un evento específico |
| **Filtrar por Disponibilidad** | Solo eventos con cupos disponibles |
| **Filtrar por Precio** | Rango de precios |
| **Filtrar por Fecha** | Eventos en un período específico |
| **Filtrar por Ubicación** | Eventos por ciudad/lugar |
| **Gestionar por Organizador** | Eventos de un organizador específico |

---

## 📡 Endpoints Principales

### Base URL
```
http://localhost:8001/api/v1/eventos
```

### 1. Listar Todos los Eventos
```
GET /api/v1/eventos/
```

**Parámetros (opcionales):**
- `estado` - Filtro por estado (default: `publicado`)
- `ordenar_por` - Ordenar resultados (default: `-fecha`)

**Ejemplo:**
```
http://localhost:8001/api/v1/eventos/?estado=publicado&ordenar_por=nombre
```

**Respuesta (200 OK):**
```json
[
  {
    "id": 1,
    "nombre": "Concierto Rock 2025",
    "descripcion": "Gran concierto de rock...",
    "fecha": "2025-02-14",
    "lugar": "Medellin",
    "precio": "50.00",
    "cupos_disponibles": 100,
    "estado": "publicado",
    "categoria": {
      "id": 1,
      "nombre": "Conciertos",
      "descripcion": "Eventos musicales"
    },
    "organizador_id": 5,
    "organizador_nombre": "Juan Pérez",
    "fecha_creacion": "2025-01-01T10:00:00",
    "ticket_types_count": 3
  }
]
```

---

### 2. Obtener Evento por ID
```
GET /api/v1/eventos/id/{evento_id}
```

**Parámetro:**
- `evento_id` - ID del evento (número entero)

**Ejemplo:**
```
http://localhost:8001/api/v1/eventos/id/1
```

**Respuesta (200 OK):**
```json
{
  "id": 1,
  "nombre": "Concierto Rock 2025",
  "descripcion": "Gran concierto de rock en vivo",
  "fecha": "2025-02-14",
  "lugar": "Medellin",
  "precio": "50.00",
  "cupos_disponibles": 100,
  "estado": "publicado",
  "categoria": {
    "id": 1,
    "nombre": "Conciertos",
    "descripcion": "Eventos musicales"
  },
  "organizador_id": 5,
  "organizador_nombre": "Juan Pérez",
  "fecha_creacion": "2025-01-01T10:00:00",
  "fecha_actualizacion": "2025-01-15T14:30:00",
  "ticket_types": [
    {
      "id": 1,
      "name": "VIP",
      "price": "100.00",
      "capacity": 50,
      "sold": 10,
      "active": true
    },
    {
      "id": 2,
      "name": "General",
      "price": "50.00",
      "capacity": 200,
      "sold": 50,
      "active": true
    }
  ],
  "total_disponible": 190,
  "precio_minimo": "50.00"
}
```

**Error (404 No Encontrado):**
```json
{
  "detail": "Evento con ID 999 no encontrado o no está publicado"
}
```

---

### 3. Buscar por Nombre
```
GET /api/v1/eventos/nombre/{nombre}
```

**Parámetros:**
- `nombre` - Nombre o parte del nombre del evento
- `estado` - Filtro por estado (default: `publicado`)

**Ejemplo:**
```
http://localhost:8001/api/v1/eventos/nombre/concierto?estado=publicado
```

---

### 4. Filtrar por Categoría
```
GET /api/v1/eventos/categoria/{categoria_id}
```

**Parámetros:**
- `categoria_id` - ID de la categoría
- `estado` - Filtro por estado (default: `publicado`)

**Ejemplo:**
```
http://localhost:8001/api/v1/eventos/categoria/1
```

---

### 5. Eventos de un Organizador
```
GET /api/v1/eventos/organizador/{organizador_id}
```

**Parámetros:**
- `organizador_id` - ID del organizador
- `estado` - Filtro por estado (opcional)

**Ejemplo:**
```
http://localhost:8001/api/v1/eventos/organizador/5
```

---

### 6. Buscar por Ubicación
```
GET /api/v1/eventos/lugar/{lugar}
```

**Parámetros:**
- `lugar` - Ciudad o zona del evento
- `estado` - Filtro por estado (default: `publicado`)

**Ejemplo:**
```
http://localhost:8001/api/v1/eventos/lugar/medellin
```

---

### 7. Solo Eventos Disponibles
```
GET /api/v1/eventos/disponibles
```

**Parámetros:**
- `estado` - Filtro por estado (default: `publicado`)

**Ejemplo:**
```
http://localhost:8001/api/v1/eventos/disponibles
```

---

### 8. Filtrar por Rango de Precios
```
GET /api/v1/eventos/rango-precio
```

**Parámetros:**
- `precio_min` - Precio mínimo (default: 0)
- `precio_max` - Precio máximo (default: 9999999)
- `estado` - Filtro por estado (default: `publicado`)

**Ejemplo:**
```
http://localhost:8001/api/v1/eventos/rango-precio?precio_min=50&precio_max=200
```

---

### 9. Filtrar por Rango de Fechas
```
GET /api/v1/eventos/rango-fecha
```

**Parámetros (obligatorios):**
- `fecha_inicio` - Fecha de inicio (formato: YYYY-MM-DD)
- `fecha_fin` - Fecha de fin (formato: YYYY-MM-DD)
- `estado` - Filtro por estado (default: `publicado`)

**Ejemplo:**
```
http://localhost:8001/api/v1/eventos/rango-fecha?fecha_inicio=2025-01-01&fecha_fin=2025-12-31
```

---

### 10. Búsqueda Avanzada
```
GET /api/v1/eventos/buscar
```

**Parámetros (todos opcionales):**
- `nombre` - Nombre del evento
- `categoria_id` - ID de categoría
- `organizador_id` - ID de organizador
- `lugar` - Ubicación
- `fecha_inicio` - Fecha inicio (YYYY-MM-DD)
- `fecha_fin` - Fecha fin (YYYY-MM-DD)
- `precio_min` - Precio mínimo
- `precio_max` - Precio máximo
- `solo_disponibles` - Solo eventos con cupos (true/false)
- `estado` - Estado del evento (default: `publicado`)
- `ordenar_por` - Campo para ordenar (default: `-fecha`)

**Ejemplos:**
```
http://localhost:8001/api/v1/eventos/buscar?nombre=concierto&lugar=medellin

http://localhost:8001/api/v1/eventos/buscar?categoria_id=1&precio_min=50&precio_max=200&solo_disponibles=true

http://localhost:8001/api/v1/eventos/buscar?fecha_inicio=2025-02-01&fecha_fin=2025-02-28&ordenar_por=nombre
```

---

## 🔍 Verificar Estado de la API

### Health Check
```
GET /api/health
```

**Respuesta:**
```json
{
  "status": "ok",
  "message": "La API está funcionando correctamente"
}
```

---

## 📚 Documentación Interactiva

Accede a **http://localhost:8001/api/docs** para:

- ✅ Ver todos los endpoints disponibles
- ✅ Probar cada endpoint directamente desde el navegador
- ✅ Ver esquemas de respuesta
- ✅ Copiar ejemplos de código

**Otras opciones de documentación:**
- ReDoc: http://localhost:8001/api/redoc
- OpenAPI JSON: http://localhost:8001/api/openapi.json

---

## 💻 Ejemplos de Uso

### Con JavaScript/Fetch
```javascript
// Listar todos los eventos
fetch('http://localhost:8001/api/v1/eventos/')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));

// Obtener evento específico
fetch('http://localhost:8001/api/v1/eventos/id/1')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));

// Buscar eventos con filtros
fetch('http://localhost:8001/api/v1/eventos/buscar?nombre=concierto&lugar=medellin')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

### Con Python/Requests
```python
import requests

# Listar eventos
response = requests.get('http://localhost:8001/api/v1/eventos/')
eventos = response.json()
print(eventos)

# Obtener evento por ID
response = requests.get('http://localhost:8001/api/v1/eventos/id/1')
evento = response.json()
print(evento)

# Búsqueda avanzada
params = {
    'nombre': 'concierto',
    'lugar': 'medellin',
    'solo_disponibles': True
}
response = requests.get('http://localhost:8001/api/v1/eventos/buscar', params=params)
eventos = response.json()
print(eventos)
```

### Con cURL
```bash
# Listar todos los eventos
curl http://localhost:8001/api/v1/eventos/

# Obtener evento por ID
curl http://localhost:8001/api/v1/eventos/id/1

# Búsqueda avanzada
curl "http://localhost:8001/api/v1/eventos/buscar?nombre=concierto&lugar=medellin"

# Con filtros de precio
curl "http://localhost:8001/api/v1/eventos/rango-precio?precio_min=50&precio_max=200"
```

---

## 🔑 Estados y Filtros

### Estados de Evento
- `publicado` - Evento visible y disponible para compra
- `borrador` - Evento en edición, no visible
- `pausado` - Evento pausado temporalmente

### Campos de Ordenamiento
- `-fecha` - Por fecha (más reciente primero, default)
- `fecha` - Por fecha (más antiguos primero)
- `nombre` - Por nombre (A-Z)
- `precio` - Por precio (menor a mayor)

---

## ⚙️ Configuración Avanzada

### Cambiar Puerto
Si deseas usar un puerto diferente a 8001:

```bash
cd Tickio_project
uvicorn api_app:app --reload --port 5000
```

Luego accede a: `http://localhost:5000`

### Ejecutar sin Recarga Automática
```bash
cd Tickio_project
uvicorn api_app:app --port 8001
```

### Ejecutar en Red Local
Para que otros equipos accedan (cambiar host):

```bash
cd Tickio_project
uvicorn api_app:app --reload --host 0.0.0.0 --port 8001
```

Luego otros equipos acceden usando tu IP: `http://tu-ip:8001`

---

## ❌ Códigos de Error

| Código | Descripción |
|--------|-------------|
| **200** | ✅ Solicitud exitosa |
| **400** | ⚠️ Solicitud inválida (parámetros incorrectos) |
| **404** | ❌ Recurso no encontrado |
| **500** | ❌ Error interno del servidor |

### Ejemplos de Error

**Evento no encontrado (404):**
```json
{
  "detail": "Evento con ID 999 no encontrado o no está publicado"
}
```

**Parámetro inválido (400):**
```json
{
  "detail": "Fecha de inicio debe ser anterior a fecha de fin"
}
```

---

## 🔐 Limitaciones Actuales

⚠️ La API actual **no requiere autenticación**. En producción se recomienda:

- ✅ Agregar autenticación JWT
- ✅ Implementar rate limiting
- ✅ Validar CORS a dominios específicos
- ✅ Usar HTTPS en lugar de HTTP

---

## 🐛 Solución de Problemas

### "No se puede acceder a localhost:8001"

**Solución 1:** Verificar que el servidor está corriendo
```bash
# En la terminal, deberías ver:
INFO:     Uvicorn running on http://127.0.0.1:8001
```

**Solución 2:** Probar desde la línea de comandos
```bash
curl http://localhost:8001/api/health
```

**Solución 3:** Verificar el firewall
- Windows: Permite acceso al puerto 8001 en el firewall

### "Connection refused"

Asegúrate de estar en la carpeta `Tickio_project` antes de ejecutar el comando:

```bash
cd Tickio_project
uvicorn api_app:app --reload --port 8001
```

### "ModuleNotFoundError: No module named 'fastapi'"

Instala las dependencias:
```bash
pip install -r requirements.txt
```

---

## 📞 Soporte

Para reportar problemas o sugerencias:

1. Verifica los logs en la terminal donde corre la API
2. Consulta la documentación interactiva en `/api/docs`
3. Revisa este archivo `API_DOCUMENTACION.md`

---

## 🎓 Arquitectura API

La API está construida con:

- **Framework:** FastAPI (Python)
- **Servidor:** Uvicorn
- **Base de Datos:** SQLite (Django ORM)
- **Validación:** Pydantic
- **Documentación:** OpenAPI/Swagger

### Componentes Principales

```
api_app.py (Aplicación FastAPI)
    ↓
events/api/evento_router.py (Endpoints)
    ↓
events/repositories.py (Acceso a datos)
    ↓
Django ORM → db.sqlite3 (Base de Datos)
```

---

## ✅ Conclusión

¡Tu API está lista para usar!

**Próximos pasos:**
1. Inicia el servidor: `uvicorn api_app:app --reload --port 8001`
2. Accede a la documentación: `http://localhost:8001/api/docs`
3. Comienza a consumir los endpoints

Para más información, consulta la documentación interactiva en `/api/docs`.

---

**Versión:** 1.0.0
**Última actualización:** Noviembre 2024
**Autor:** Sistema de Arquitectura - TICKIO
