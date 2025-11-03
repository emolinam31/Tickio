# 🎫 TICKIO - Sistema de Reserva de Eventos

**TICKIO** es una aplicación web moderna para la gestión y reserva de eventos. Permite a organizadores crear y gestionar eventos, mientras que los asistentes pueden explorar, reservar boletos y descargar sus entradas en formato digital.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Requisitos Previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [API de Servicios](#api-de-servicios)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Testing](#testing)
- [Contribución](#contribución)
- [Licencia](#licencia)

## ✨ Características

### Para Asistentes
- ✅ Explorar eventos próximos con múltiples filtros
- ✅ Ver detalles completos de eventos
- ✅ Agregar boletos al carrito de compras
- ✅ Checkout seguro con procesamiento de pagos
- ✅ Descargar boletos en formato digital con código QR
- ✅ Historial de órdenes y boletos
- ✅ Soporte multiidioma (Español/Inglés)

### Para Organizadores
- ✅ Crear y gestionar eventos
- ✅ Definir múltiples tipos de boletos (General, VIP, etc.)
- ✅ Controlar capacidad y disponibilidad
- ✅ Cambiar estado de eventos (Borrador → Publicado → Pausado)
- ✅ Ver estadísticas de ventas en tiempo real
- ✅ Gestionar tipos de boletos

### Técnicas
- ✅ Arquitectura de tres capas (Models, Services, Repositories)
- ✅ Patrón Repository para abstracción de datos
- ✅ Service Layer para lógica de negocio
- ✅ Principios SOLID aplicados
- ✅ Transacciones atómicas en operaciones críticas
- ✅ Sistema de carrito basado en sesiones
- ✅ Código QR para validación de boletos
- ✅ Sistema de retención temporal de boletos

## 🏗️ Arquitectura

TICKIO sigue una arquitectura de tres capas:

```
┌─────────────────────────────────────────────┐
│         Capa de Presentación (Views)        │
│  (Django Templates & Static Files)          │
├─────────────────────────────────────────────┤
│      Capa de Lógica de Negocio (Services)   │
│  (EventService, OrderService, etc.)         │
├─────────────────────────────────────────────┤
│  Capa de Acceso a Datos (Repositories)      │
│  (EventRepository, OrderRepository, etc.)   │
├─────────────────────────────────────────────┤
│         Capa de Base de Datos (ORM)         │
│  (Django ORM con SQLite3)                   │
└─────────────────────────────────────────────┘
```

### Patrones de Diseño

1. **Repository Pattern**: Abstrae el acceso a datos
2. **Service Layer**: Encapsula la lógica de negocio
3. **Adapter Pattern**: Para integración de gateways de pago
4. **State Pattern**: Para gestión de estados de eventos
5. **Command Pattern**: Para operaciones transaccionales

## 📦 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git
- SQLite3 (incluido en Python)

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/emolinam31/Tickio.git
cd Tickio
```

### 2. Crear Entorno Virtual

```bash
# En Windows
python -m venv venv
venv\Scripts\activate

# En Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Navegar al Directorio del Proyecto

```bash
cd Tickio_project
```

### 5. Ejecutar Migraciones de Base de Datos

```bash
python manage.py migrate
```

### 6. Poblar Base de Datos (Opcional)

```bash
python manage.py runscript populateEventdb
```

### 7. Crear Superusuario (Admin)

```bash
python manage.py createsuperuser
```

### 8. Ejecutar el Servidor

```bash
python manage.py runserver
```

La aplicación estará disponible en `http://localhost:8000`

## ⚙️ Configuración

### Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
DEBUG=True
SECRET_KEY=tu-clave-secreta-aqui
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3

# Configuración de Pagos (opcional)
PAYMENT_GATEWAY=dummy  # o stripe, paypal, etc.

# Configuración de Email (opcional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-contraseña
```

### Configuración de Idioma

Los idiomas soportados están en `Tickio_project/tickio/settings.py`:

```python
LANGUAGES = [
    ('es', _('Spanish')),
    ('en', _('English')),
]
```

## 📖 Uso

### Para Asistentes

1. **Registrarse**
   - Ir a `/accounts/register/`
   - Seleccionar tipo "Asistente"
   - Completar formulario

2. **Explorar Eventos**
   - Ir a `/events/` o `/`
   - Usar filtros de búsqueda
   - Ver detalles del evento

3. **Comprar Boletos**
   - Agregar boletos al carrito
   - Ir a `/orders/cart/`
   - Proceder a checkout
   - Completar pago

4. **Descargar Boletos**
   - Ir a `/accounts/my-orders/`
   - Ver historial de órdenes
   - Descargar boletos con código QR

### Para Organizadores

1. **Registrarse**
   - Ir a `/accounts/register/`
   - Seleccionar tipo "Organizador"
   - Completar información

2. **Crear Evento**
   - Ir a `/mis-eventos/`
   - Click en "Crear Evento"
   - Llenar detalles del evento

3. **Definir Tipos de Boletos**
   - En formulario de creación
   - Agregar múltiples tipos (General, VIP, etc.)
   - Definir precios y capacidad

4. **Publicar Evento**
   - Cambiar estado a "Publicado"
   - El evento aparecerá en búsquedas

5. **Ver Estadísticas**
   - Dashboard muestra ventas en tiempo real
   - Estadísticas por tipo de boleto

## 🔧 API de Servicios

### EventService

```python
from events.services import EventService

# Crear evento
evento = EventService.create_event(
    organizer=usuario,
    nombre="Rock Festival 2024",
    descripcion="Un gran festival de rock",
    fecha=date(2024, 6, 15),
    lugar="Estadio Nacional",
    categoria_id=1
)

# Publicar evento
EventService.publish_event(event_id=1)

# Obtener estadísticas
stats = EventService.get_event_stats(event_id=1)
print(f"Boletos vendidos: {stats['total_sold']}")
```

### OrderService

```python
from orders.services import OrderService
from payments.adapters.dummy import DummyGateway

# Crear servicio de órdenes
order_service = OrderService(payment_gateway=DummyGateway())

# Procesar checkout
carrito = {
    'item_1': {'ticket_type_id': 1, 'quantity': 2},
    'item_2': {'ticket_type_id': 2, 'quantity': 1}
}

orden = order_service.checkout(carrito, user=usuario)
print(f"Orden creada: {orden.id}, Total: {orden.total_amount}")
```

### RepositoriesPattern

```python
from events.repositories import EventRepository, TicketTypeRepository

# Buscar eventos próximos
eventos = EventRepository.find_upcoming_events()

# Buscar por categoría
eventos = EventRepository.find_events_by_category(category_id=1)

# Validar disponibilidad
disponible = TicketTypeRepository.check_availability(
    ticket_type_id=1,
    quantity=5
)
```

## 📁 Estructura del Proyecto

```
TICKIO/
├── Tickio_project/
│   ├── accounts/              # Autenticación y perfiles de usuarios
│   │   ├── models.py         # CustomUser, Asistente, Organizador
│   │   ├── views.py          # Vistas de autenticación
│   │   ├── services.py       # Servicios de usuario (nuevo)
│   │   ├── repositories.py   # Acceso a datos de usuario (nuevo)
│   │   ├── urls.py
│   │   ├── forms.py
│   │   └── templates/
│   │
│   ├── events/               # Gestión de eventos
│   │   ├── models.py         # Evento, CategoriaEvento, TicketType
│   │   ├── views.py          # Vistas de eventos
│   │   ├── services.py       # Servicios de evento (nuevo)
│   │   ├── repositories.py   # Acceso a datos de evento (nuevo)
│   │   ├── urls.py
│   │   ├── forms.py
│   │   └── templates/
│   │
│   ├── orders/               # Gestión de órdenes y carrito
│   │   ├── models.py         # Order, OrderItem, Ticket
│   │   ├── views.py          # Vistas de carrito y checkout
│   │   ├── services.py       # Servicios de orden (mejorado)
│   │   ├── repositories.py   # Acceso a datos de orden (nuevo)
│   │   ├── urls.py
│   │   └── templates/
│   │
│   ├── payments/             # Integración de pagos
│   │   ├── interfaces.py     # PaymentGateway abstracto
│   │   ├── adapters/
│   │   │   └── dummy.py      # Implementación de prueba
│   │   └── migrations/
│   │
│   ├── notifications/        # Sistema de notificaciones (futuro)
│   ├── dashboard/            # Dashboard de organizadores
│   │
│   ├── templates/            # Templates base
│   ├── static/               # Archivos estáticos (CSS, JS)
│   ├── locale/               # Archivos de internacionalización
│   ├── manage.py
│   └── db.sqlite3
│
├── requirements.txt          # Dependencias
├── README.md                 # Este archivo
└── FEEDBACK_PROFESOR[1].md   # Feedback de correcciones
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
python manage.py test

# Tests de una app específica
python manage.py test accounts

# Tests con verbosidad
python manage.py test --verbosity=2

# Tests con cobertura
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### Estructura de Tests

```
accounts/tests.py       # Tests de autenticación
events/tests.py         # Tests de eventos
orders/tests.py         # Tests de órdenes
payments/tests.py       # Tests de pagos
```

### Ejemplo de Test

```python
from django.test import TestCase
from accounts.models import CustomUser
from events.models import Evento, CategoriaEvento

class EventoTestCase(TestCase):
    def setUp(self):
        self.categoria = CategoriaEvento.objects.create(
            nombre="Rock",
            descripcion="Música rock"
        )

    def test_crear_evento(self):
        evento = Evento.objects.create(
            nombre="Rock Festival",
            descripcion="Un festival",
            fecha="2024-06-15",
            lugar="Estadio",
            categoria=self.categoria,
            organizador=self.usuario
        )
        self.assertEqual(evento.nombre, "Rock Festival")
```

## 👥 Contribución

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Guía de Estilo

- Seguir PEP 8 para Python
- Usar docstrings en español
- Agregar comentarios de autor en archivos principales
- Mantener separación de responsabilidades
- Usar type hints

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo LICENSE para más detalles.

## 👨‍💻 Autor

**Equipo de Desarrollo - TICKIO**
- Universidad EAFIT
- Curso: Arquitectura de Software
- Semestre 6

## 📞 Soporte

Para reportar problemas o sugerencias, por favor abre un issue en GitHub.

---

**Versión:** 1.0.0
**Última actualización:** Noviembre 2024
