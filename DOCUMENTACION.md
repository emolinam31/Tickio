# Documentación Técnica - Tickio

## Índice
1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Modelos de Datos](#modelos-de-datos)
3. [Vistas y Endpoints](#vistas-y-endpoints)
4. [Servicios y Lógica de Negocio](#servicios-y-lógica-de-negocio)
5. [Flujos de Trabajo Principales](#flujos-de-trabajo-principales)
6. [Internacionalización](#internacionalización)
7. [Sistema de Reservas Temporales](#sistema-de-reservas-temporales)

---

## Arquitectura del Sistema

### Estructura del Proyecto

```
Tickio/
├── Tickio_project/
│   ├── accounts/              # App de usuarios y autenticación
│   │   ├── models.py         # CustomUser, Asistente, Organizador
│   │   ├── views.py          # Vistas de autenticación
│   │   ├── forms.py          # Formularios de usuario
│   │   ├── urls.py           # URLs de la app accounts
│   │   └── templates/        # Templates de autenticación
│   │
│   ├── events/               # App de gestión de eventos
│   │   ├── models.py         # Evento, CategoriaEvento, TicketType
│   │   ├── views.py          # Vistas de eventos
│   │   ├── forms.py          # Formularios de eventos
│   │   ├── urls.py           # URLs de la app events
│   │   ├── decorators.py     # Decoradores de permisos
│   │   └── templates/        # Templates de eventos
│   │
│   ├── orders/               # App de órdenes y tickets
│   │   ├── models.py         # Order, OrderItem, Ticket, TicketHold
│   │   ├── views.py          # Vistas de carrito y checkout
│   │   ├── services.py       # Lógica de negocio de órdenes
│   │   ├── urls.py           # URLs de la app orders
│   │   └── templates/        # Templates de órdenes
│   │
│   ├── payments/             # App de integración de pagos
│   │   ├── interfaces.py     # PaymentGateway (interfaz abstracta)
│   │   └── adapters/
│   │       └── dummy.py      # Implementación de prueba
│   │
│   ├── tickio/               # Configuración principal
│   │   ├── settings.py       # Configuración de Django
│   │   ├── urls.py           # URLs principales
│   │   └── wsgi.py           # WSGI config
│   │
│   ├── templates/            # Templates base
│   ├── static/               # Archivos estáticos
│   └── locale/               # Archivos de traducción
│       ├── es/
│       └── en/
│
├── requirements.txt          # Dependencias del proyecto
└── README.md                # Guía de instalación
```

### Tecnologías Utilizadas

- **Backend**: Django 5.2.4
- **Base de Datos**: SQLite (desarrollo)
- **Frontend**: Bootstrap 5.3.3, HTML5, JavaScript
- **Internacionalización**: Django i18n (Español/Inglés)
- **QR Codes**: qrcode library
- **Imágenes**: Pillow

---

## Modelos de Datos

### 1. CustomUser (accounts/models.py)

Modelo de usuario personalizado que extiende `AbstractUser` de Django.

**Campos:**
- `tipo`: CharField - Tipo de usuario ('asistente' o 'organizador')
- `nombre`: CharField - Nombre completo del usuario
- `email`: EmailField - Email único (usado como USERNAME_FIELD)

**Relaciones:**
- `OneToOne` con `Asistente` (si tipo='asistente')
- `OneToOne` con `Organizador` (si tipo='organizador')

**Métodos:**
- `get_profile()`: Retorna el perfil asociado (Asistente u Organizador)

### 2. Asistente (accounts/models.py)

Perfil extendido para usuarios tipo asistente.

**Campos:**
- `historial_compras`: JSONField - Historial de compras del usuario
- `preferencias`: JSONField - Preferencias del usuario
- `user`: OneToOneField - Relación con CustomUser

### 3. Organizador (accounts/models.py)

Perfil extendido para usuarios tipo organizador.

**Campos:**
- `empresa`: CharField - Nombre de la empresa
- `eventos_publicados`: ManyToManyField - Eventos publicados por el organizador
- `user`: OneToOneField - Relación con CustomUser

### 4. Evento (events/models.py)

Modelo principal de eventos.

**Campos:**
- `nombre`: CharField - Nombre del evento
- `descripcion`: TextField - Descripción del evento
- `categoria`: ForeignKey - Categoría del evento
- `fecha`: DateField - Fecha del evento
- `lugar`: CharField - Lugar donde se realiza
- `organizador`: ForeignKey - Usuario organizador
- `cupos_disponibles`: PositiveIntegerField - Cupos disponibles (legacy)
- `precio`: DecimalField - Precio base (legacy, si no hay tipos de boleto)
- `estado`: CharField - Estado ('borrador', 'publicado', 'pausado')
- `fecha_creacion`: DateTimeField - Fecha de creación
- `fecha_actualizacion`: DateTimeField - Fecha de última actualización

**Métodos:**
- `esta_agotado()`: Retorna True si no hay cupos disponibles
- `total_available()`: Calcula cupos totales disponibles (considerando tipos de boleto)
- `min_ticket_price()`: Retorna el precio mínimo de los tipos de boleto
- `get_available_ticket_types()`: Retorna tipos de boleto disponibles

### 5. TicketType (events/models.py)

Tipos de boleto para un evento.

**Campos:**
- `event`: ForeignKey - Evento al que pertenece
- `name`: CharField - Nombre del tipo de boleto (ej: "General", "VIP")
- `price`: DecimalField - Precio del boleto
- `capacity`: PositiveIntegerField - Capacidad total
- `sold`: PositiveIntegerField - Cantidad vendida
- `active`: BooleanField - Si está activo

**Propiedades:**
- `available`: Calcula disponibilidad (capacity - sold)

### 6. Order (orders/models.py)

Orden de compra.

**Campos:**
- `user`: ForeignKey - Usuario que realiza la compra
- `created_at`: DateTimeField - Fecha de creación
- `updated_at`: DateTimeField - Fecha de actualización
- `status`: CharField - Estado de la orden ('created', 'paid', 'refunded')
- `total_amount`: DecimalField - Monto total de la orden

### 7. OrderItem (orders/models.py)

Item individual de una orden.

**Campos:**
- `order`: ForeignKey - Orden a la que pertenece
- `event`: ForeignKey - Evento
- `ticket_type`: ForeignKey - Tipo de boleto
- `name`: CharField - Nombre del item
- `unit_price`: DecimalField - Precio unitario
- `quantity`: PositiveIntegerField - Cantidad
- `line_total`: DecimalField - Total del item

### 8. Ticket (orders/models.py)

Boleto individual generado.

**Campos:**
- `order`: ForeignKey - Orden de la que proviene
- `ticket_type`: ForeignKey - Tipo de boleto
- `user`: ForeignKey - Usuario propietario
- `event`: ForeignKey - Evento
- `unique_code`: UUIDField - Código único del boleto
- `is_used`: BooleanField - Si el boleto ya fue usado
- `created_at`: DateTimeField - Fecha de creación

### 9. TicketHold (orders/models.py)

Reserva temporal de tickets en el carrito.

**Campos:**
- `ticket_type`: ForeignKey - Tipo de boleto reservado
- `user`: ForeignKey - Usuario (opcional, puede ser anónimo)
- `session_key`: CharField - Clave de sesión del usuario
- `quantity`: PositiveIntegerField - Cantidad reservada
- `created_at`: DateTimeField - Fecha de creación de la reserva
- `expires_at`: DateTimeField - Fecha de expiración (10 minutos)

**Métodos:**
- `is_active()`: Retorna True si la reserva aún no ha expirado

---

## Vistas y Endpoints

### App: Events

#### HomeView
- **URL**: `/`
- **Método**: GET
- **Descripción**: Página principal. Muestra dashboard para organizadores o landing para usuarios normales.
- **Template**: `events/home.html` o `events/organizador_home.html`

#### EventListView
- **URL**: `/events/`
- **Método**: GET
- **Descripción**: Lista todos los eventos disponibles con filtros.
- **Filtros**: nombre, categoría, lugar, fecha
- **Template**: `events/list_events.html`

#### EventDetailView
- **URL**: `/events/<int:pk>/`
- **Método**: GET
- **Descripción**: Detalle de un evento específico con opción de agregar al carrito.
- **Template**: `events/detail_events.html`

#### mis_eventos
- **URL**: `/mis-eventos/`
- **Método**: GET
- **Decorador**: `@login_required`, `@organizador_required`
- **Descripción**: Lista eventos del organizador logueado.
- **Template**: `events/mis_eventos.html`

#### crear_evento
- **URL**: `/evento/crear/`
- **Método**: GET, POST
- **Decorador**: `@login_required`, `@organizador_required`
- **Descripción**: Formulario para crear un nuevo evento.
- **Template**: `events/evento_form.html`

#### editar_evento
- **URL**: `/evento/<int:pk>/editar/`
- **Método**: GET, POST
- **Decorador**: `@login_required`, `@organizador_required`
- **Descripción**: Formulario para editar un evento existente.
- **Template**: `events/evento_form.html`

#### cambiar_estado_evento
- **URL**: `/evento/<int:pk>/estado/`
- **Método**: POST
- **Decorador**: `@login_required`, `@organizador_required`
- **Descripción**: Cambia el estado de un evento (borrador/publicado/pausado).

### App: Accounts

#### register
- **URL**: `/accounts/register/`
- **Método**: GET, POST
- **Descripción**: Registro de nuevos usuarios.
- **Template**: `accounts/register.html`

#### CustomLoginView
- **URL**: `/accounts/login/`
- **Método**: GET, POST
- **Descripción**: Inicio de sesión de usuarios.
- **Template**: `accounts/login.html`

#### logout_view
- **URL**: `/accounts/logout/`
- **Método**: GET
- **Descripción**: Cerrar sesión del usuario.

#### profile
- **URL**: `/accounts/profile/`
- **Método**: GET, POST
- **Decorador**: `@login_required`
- **Descripción**: Perfil del usuario con opción de edición.
- **Template**: `accounts/profile.html`

#### my_orders
- **URL**: `/accounts/my-orders/`
- **Método**: GET
- **Decorador**: `@login_required`
- **Descripción**: Lista de órdenes del usuario.
- **Template**: `templates/orders/my_orders.html`

### App: Orders

#### add_to_cart
- **URL**: `/orders/add/`
- **Método**: POST
- **Descripción**: Agrega tickets al carrito y crea reserva temporal.
- **Parámetros POST**:
  - `ticket_type_id`: ID del tipo de boleto
  - `quantity`: Cantidad (default: 1)

#### remove_from_cart
- **URL**: `/orders/remove/`
- **Método**: POST
- **Descripción**: Remueve un item del carrito y libera la reserva.
- **Parámetros POST**:
  - `ticket_type_id`: ID del tipo de boleto

#### update_quantity
- **URL**: `/orders/update/`
- **Método**: POST
- **Descripción**: Actualiza la cantidad de un item en el carrito.
- **Parámetros POST**:
  - `ticket_type_id`: ID del tipo de boleto
  - `delta`: '+1' o '-1'

#### cart_view
- **URL**: `/orders/cart/`
- **Método**: GET
- **Descripción**: Muestra el carrito de compras.
- **Template**: `orders/cart.html`

#### checkout_view
- **URL**: `/orders/checkout/`
- **Método**: GET, POST
- **Decorador**: `@login_required`
- **Descripción**: Proceso de checkout y pago.
- **Template**: `orders/checkout.html`

#### ticket_detail_view
- **URL**: `/orders/ticket/<uuid:ticket_code>/`
- **Método**: GET
- **Decorador**: `@login_required`
- **Descripción**: Detalle de un ticket con código QR.
- **Template**: `orders/ticket_detail.html`

---

## Servicios y Lógica de Negocio

### OrderService (orders/services.py)

Servicio principal para gestión de órdenes y checkout.

#### Métodos Principales:

##### `checkout(cart, user) -> Order`
Ejecuta el proceso completo de checkout:
1. Valida el carrito y usuario
2. Crea la orden
3. Crea los items de la orden
4. Actualiza el stock de tickets
5. Procesa el pago
6. Crea los tickets individuales
7. Retorna la orden creada

**Uso:**
```python
from orders.services import checkout

order = checkout(cart_dict, user=request.user)
```

### TicketService (orders/services.py)

Servicio para operaciones relacionadas con tickets.

#### Métodos:

##### `validate_ticket_availability(ticket_type_id, quantity) -> bool`
Valida que haya disponibilidad suficiente de tickets.

##### `calculate_total_price(cart) -> Decimal`
Calcula el precio total del carrito.

##### `create_tickets_for_order(order) -> List[Ticket]`
Crea los boletos individuales para una orden.

### Sistema de Reservas Temporales

El sistema implementa reservas temporales de tickets cuando se agregan al carrito.

**Funcionamiento:**
1. Al agregar al carrito, se crea un `TicketHold` con expiración de 10 minutos
2. La disponibilidad efectiva considera los holds activos de otros usuarios
3. Al remover del carrito o completar la compra, se liberan los holds
4. Los holds expirados se ignoran automáticamente en el cálculo de disponibilidad

**Funciones auxiliares en `orders/views.py`:**
- `_ensure_session_key(request)`: Asegura que la sesión tenga una clave
- `_held_quantities(ticket_type, session_key)`: Calcula holds totales y propios
- `_effective_available(ticket_type, session_key)`: Calcula disponibilidad real

---

## Flujos de Trabajo Principales

### 1. Flujo de Compra de Tickets

```
1. Usuario navega eventos
   ↓
2. Selecciona evento y tipo de boleto
   ↓
3. Agrega al carrito (add_to_cart)
   - Se crea TicketHold (reserva 10 min)
   - Se actualiza disponibilidad efectiva
   ↓
4. Visualiza carrito (cart_view)
   ↓
5. Procede al checkout (checkout_view)
   - Valida disponibilidad
   - Crea orden
   - Procesa pago
   - Crea tickets
   - Libera holds
   ↓
6. Recibe confirmación y tickets
```

### 2. Flujo de Creación de Evento (Organizador)

```
1. Organizador accede a "Mis Eventos"
   ↓
2. Hace clic en "Crear Nuevo Evento"
   ↓
3. Completa formulario de evento
   - Datos básicos (nombre, fecha, lugar, etc.)
   - Tipos de boleto (formset)
   ↓
4. Guarda evento
   - Estado inicial: 'borrador'
   ↓
5. Cambia estado a 'publicado' (opcional)
   - Evento visible para usuarios
```

### 3. Flujo de Registro de Usuario

```
1. Usuario accede a registro
   ↓
2. Completa formulario
   - Email, username, nombre
   - Tipo (asistente/organizador)
   - Contraseña
   ↓
3. Sistema crea CustomUser
   ↓
4. Crea perfil asociado (Asistente u Organizador)
   ↓
5. Inicia sesión automáticamente
   ↓
6. Redirige según tipo de usuario
```

---

## Internacionalización

El sistema soporta múltiples idiomas (Español/Inglés).

### Configuración

**Settings (`tickio/settings.py`):**
- `LANGUAGE_CODE = "es"`
- `LANGUAGES = [('es', 'Spanish'), ('en', 'English')]`
- `LOCALE_PATHS = [BASE_DIR / 'locale']`

### Uso en Templates

```django
{% load i18n %}
{% trans "Texto a traducir" %}
{% blocktrans with var=value %}Texto con {{ var }}{% endblocktrans %}
```

### Uso en Vistas

```python
from django.utils.translation import gettext as _

messages.success(request, _("¡Registro exitoso!"))
```

### Uso en Modelos

```python
from django.utils.translation import gettext_lazy as _

class Evento(models.Model):
    nombre = models.CharField(max_length=200, verbose_name=_("Nombre"))
    
    class Meta:
        verbose_name = _("Evento")
```

### Compilar Traducciones

```bash
# Extraer cadenas nuevas
python manage.py makemessages -l en

# Editar locale/en/LC_MESSAGES/django.po

# Compilar traducciones
python manage.py compilemessages
```

---

## Sistema de Reservas Temporales

### Objetivo

Evitar que múltiples usuarios compiten por los mismos tickets cuando están en proceso de compra.

### Implementación

**Modelo TicketHold:**
- Almacena reservas temporales de tickets
- Expiración automática después de 10 minutos
- Vinculado a sesión del usuario

**Lógica:**
1. Al agregar al carrito: se crea/actualiza TicketHold
2. Disponibilidad efectiva = capacidad - vendidos - (holds activos de otros)
3. Al remover del carrito: se elimina el hold
4. Al completar compra: se liberan todos los holds de la sesión
5. Holds expirados: no se consideran en el cálculo

**Constante:**
- `HOLD_MINUTES = 10` (en `orders/views.py`)

### Ventajas

- Reduce conflictos de concurrencia
- Mejora experiencia de usuario
- Permite tiempo razonable para completar compra
- Liberación automática de reservas expiradas

---

## Patrones de Diseño Utilizados

### 1. Repository Pattern (parcialmente implementado)
- Servicios separados de acceso a datos
- `TicketTypeRepository`, `OrderRepository`, etc.

### 2. Service Layer Pattern
- `OrderService`, `TicketService` encapsulan lógica de negocio
- Separación entre vistas y lógica

### 3. Strategy Pattern
- `PaymentGateway` como interfaz abstracta
- Implementaciones concretas: `DummyGateway`

### 4. Decorator Pattern
- `@login_required`, `@organizador_required`
- Extienden funcionalidad de vistas

---

## Consideraciones de Seguridad

### Autenticación y Autorización
- Uso de `@login_required` para vistas protegidas
- `@organizador_required` para acciones de organizadores
- Validación de propiedad en edición de eventos

### Transacciones
- `@transaction.atomic` en checkout para garantizar consistencia
- `select_for_update()` para evitar condiciones de carrera

### Validación
- Validación de disponibilidad antes de checkout
- Validación de stock con locks de base de datos
- Validación de formularios con Django Forms

---

## Extensiones Futuras

### Posibles Mejoras

1. **Sistema de Notificaciones**
   - Email al completar compra
   - Notificaciones de eventos próximos

2. **Gateway de Pagos Real**
   - Integración con Stripe/MercadoPago
   - Webhooks de confirmación

3. **Sistema de Cola**
   - Para eventos de alta demanda
   - Distribución justa de tickets

4. **Dashboard Avanzado**
   - Estadísticas detalladas
   - Reportes de ventas

5. **API REST**
   - Endpoints JSON para integración
   - Autenticación por tokens

---

## Contacto y Soporte

Para preguntas sobre el código o contribuciones, consultar el README.md principal.

---

**Versión de Documentación**: 1.0  
**Última Actualización**: 2025

