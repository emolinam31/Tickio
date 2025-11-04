from fastapi import APIRouter, HTTPException, Query
from datetime import date
from decimal import Decimal
from typing import Optional, List

from events.models import Evento
from events.repositories import EventoRepository
from events.schemas import EventoListaSchema, EventoDetailSchema
from events.geocoding_service import GeocodingServiceWithCache

# Crear router para eventos
router = APIRouter(prefix="/api/v1/eventos", tags=["Eventos"])


@router.get("/", response_model=List[EventoListaSchema])
def listar_eventos(
    estado: str = Query("publicado", description="Estado del evento: publicado, borrador, pausado"),
    ordenar_por: str = Query("-fecha", description="Campo para ordenar: -fecha, nombre, precio")
):
    """
    Listar todos los eventos disponibles

    **Parámetros de consulta:**
    - `estado`: Filtrar por estado (por defecto: publicado)
    - `ordenar_por`: Ordenar resultados (por defecto: -fecha)

    **Ejemplos:**
    - `/api/v1/eventos/` - Obtener todos los eventos publicados
    - `/api/v1/eventos/?estado=publicado&ordenar_por=nombre`
    """
    eventos = EventoRepository.get_all_eventos(estado=estado, ordenar_por=ordenar_por)
    return [
        EventoListaSchema(
            **evento_to_dict(evento),
            ticket_types_count=evento.ticket_types.count()
        )
        for evento in eventos
    ]


@router.get("/id/{evento_id}", response_model=EventoDetailSchema)
def obtener_evento_por_id(evento_id: int):
    """
    Obtener detalles de un evento específico por ID

    **Parámetros:**
    - `evento_id`: ID del evento

    **Ejemplo:**
    - `/api/v1/eventos/id/1`
    """
    evento = EventoRepository.get_evento_by_id(evento_id)
    if not evento:
        raise HTTPException(
            status_code=404,
            detail=f"Evento con ID {evento_id} no encontrado o no está publicado"
        )

    # Obtener coordenadas del lugar
    coords = GeocodingServiceWithCache.get_coordinates_cached(
        lugar=evento.lugar,
        ciudad=evento.lugar.split(',')[-1].strip() if ',' in evento.lugar else evento.lugar
    )

    evento_dict = evento_to_dict(evento)
    evento_dict['latitud'] = coords['latitud']
    evento_dict['longitud'] = coords['longitud']

    return EventoDetailSchema(
        **evento_dict,
        ticket_types=[
            {
                'id': tt.id,
                'name': tt.name,
                'price': tt.price,
                'capacity': tt.capacity,
                'sold': tt.sold,
                'active': tt.active
            }
            for tt in evento.ticket_types.all()
        ],
        total_disponible=evento.total_available(),
        precio_minimo=evento.min_ticket_price()
    )


@router.get("/nombre/{nombre}", response_model=List[EventoListaSchema])
def buscar_eventos_por_nombre(
    nombre: str,
    estado: str = Query("publicado", description="Estado del evento")
):
    """
    Buscar eventos por nombre (búsqueda parcial, insensible a mayúsculas/minúsculas)

    **Parámetros:**
    - `nombre`: Nombre o parte del nombre del evento
    - `estado`: Estado del evento (por defecto: publicado)

    **Ejemplo:**
    - `/api/v1/eventos/nombre/concierto`
    """
    eventos = EventoRepository.get_eventos_by_nombre(nombre=nombre, estado=estado)
    return [
        EventoListaSchema(
            **evento_to_dict(evento),
            ticket_types_count=evento.ticket_types.count()
        )
        for evento in eventos
    ]


@router.get("/categoria/{categoria_id}", response_model=List[EventoListaSchema])
def obtener_eventos_por_categoria(
    categoria_id: int,
    estado: str = Query("publicado", description="Estado del evento")
):
    """
    Obtener eventos de una categoría específica

    **Parámetros:**
    - `categoria_id`: ID de la categoría
    - `estado`: Estado del evento (por defecto: publicado)

    **Ejemplo:**
    - `/api/v1/eventos/categoria/1`
    """
    eventos = EventoRepository.get_eventos_by_categoria(categoria_id=categoria_id, estado=estado)
    return [
        EventoListaSchema(
            **evento_to_dict(evento),
            ticket_types_count=evento.ticket_types.count()
        )
        for evento in eventos
    ]


@router.get("/organizador/{organizador_id}", response_model=List[EventoListaSchema])
def obtener_eventos_por_organizador(
    organizador_id: int,
    estado: Optional[str] = Query(None, description="Estado del evento (opcional)")
):
    """
    Obtener eventos creados por un organizador específico

    **Parámetros:**
    - `organizador_id`: ID del organizador
    - `estado`: Estado del evento (opcional, sin filtro si no se proporciona)

    **Ejemplo:**
    - `/api/v1/eventos/organizador/5`
    """
    eventos = EventoRepository.get_eventos_by_organizador(organizador_id=organizador_id, estado=estado)
    return [
        EventoListaSchema(
            **evento_to_dict(evento),
            ticket_types_count=evento.ticket_types.count()
        )
        for evento in eventos
    ]


@router.get("/lugar/{lugar}", response_model=List[EventoListaSchema])
def buscar_eventos_por_lugar(
    lugar: str,
    estado: str = Query("publicado", description="Estado del evento")
):
    """
    Buscar eventos por lugar (búsqueda parcial, insensible a mayúsculas/minúsculas)

    **Parámetros:**
    - `lugar`: Ciudad, lugar o zona del evento
    - `estado`: Estado del evento (por defecto: publicado)

    **Ejemplo:**
    - `/api/v1/eventos/lugar/medellin`
    """
    eventos = EventoRepository.get_eventos_by_lugar(lugar=lugar, estado=estado)
    return [
        EventoListaSchema(
            **evento_to_dict(evento),
            ticket_types_count=evento.ticket_types.count()
        )
        for evento in eventos
    ]


@router.get("/disponibles", response_model=List[EventoListaSchema])
def obtener_eventos_disponibles(
    estado: str = Query("publicado", description="Estado del evento")
):
    """
    Obtener solo eventos que aún tienen cupos disponibles

    **Parámetros:**
    - `estado`: Estado del evento (por defecto: publicado)

    **Ejemplo:**
    - `/api/v1/eventos/disponibles`
    """
    eventos = EventoRepository.get_eventos_disponibles(estado=estado)
    return [
        EventoListaSchema(
            **evento_to_dict(evento),
            ticket_types_count=evento.ticket_types.count()
        )
        for evento in eventos
    ]


@router.get("/rango-precio", response_model=List[EventoListaSchema])
def obtener_eventos_por_rango_precio(
    precio_min: Decimal = Query(0, description="Precio mínimo"),
    precio_max: Decimal = Query(9999999, description="Precio máximo"),
    estado: str = Query("publicado", description="Estado del evento")
):
    """
    Obtener eventos dentro de un rango de precios

    **Parámetros:**
    - `precio_min`: Precio mínimo (por defecto: 0)
    - `precio_max`: Precio máximo (por defecto: 9999999)
    - `estado`: Estado del evento (por defecto: publicado)

    **Ejemplo:**
    - `/api/v1/eventos/rango-precio?precio_min=50&precio_max=200`
    """
    eventos = EventoRepository.get_eventos_por_rango_precio(
        precio_min=precio_min,
        precio_max=precio_max,
        estado=estado
    )
    return [
        EventoListaSchema(
            **evento_to_dict(evento),
            ticket_types_count=evento.ticket_types.count()
        )
        for evento in eventos
    ]


@router.get("/rango-fecha", response_model=List[EventoListaSchema])
def obtener_eventos_por_rango_fecha(
    fecha_inicio: date = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    estado: str = Query("publicado", description="Estado del evento")
):
    """
    Obtener eventos dentro de un rango de fechas

    **Parámetros:**
    - `fecha_inicio`: Fecha de inicio (formato: YYYY-MM-DD, requerido)
    - `fecha_fin`: Fecha de fin (formato: YYYY-MM-DD, requerido)
    - `estado`: Estado del evento (por defecto: publicado)

    **Ejemplo:**
    - `/api/v1/eventos/rango-fecha?fecha_inicio=2025-01-01&fecha_fin=2025-12-31`
    """
    eventos = EventoRepository.get_eventos_by_fecha(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado=estado
    )
    return [
        EventoListaSchema(
            **evento_to_dict(evento),
            ticket_types_count=evento.ticket_types.count()
        )
        for evento in eventos
    ]


@router.get("/buscar", response_model=List[EventoListaSchema])
def buscar_eventos_avanzado(
    nombre: Optional[str] = Query(None, description="Nombre del evento"),
    categoria_id: Optional[int] = Query(None, description="ID de la categoría"),
    organizador_id: Optional[int] = Query(None, description="ID del organizador"),
    lugar: Optional[str] = Query(None, description="Lugar del evento"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    precio_min: Optional[Decimal] = Query(None, description="Precio mínimo"),
    precio_max: Optional[Decimal] = Query(None, description="Precio máximo"),
    solo_disponibles: bool = Query(False, description="Solo eventos con cupos disponibles"),
    estado: str = Query("publicado", description="Estado del evento"),
    ordenar_por: str = Query("-fecha", description="Campo para ordenar")
):
    """
    Búsqueda avanzada de eventos con múltiples filtros

    **Parámetros:**
    - `nombre`: Nombre del evento (opcional)
    - `categoria_id`: ID de la categoría (opcional)
    - `organizador_id`: ID del organizador (opcional)
    - `lugar`: Lugar del evento (opcional)
    - `fecha_inicio`: Fecha de inicio (opcional, formato: YYYY-MM-DD)
    - `fecha_fin`: Fecha de fin (opcional, formato: YYYY-MM-DD)
    - `precio_min`: Precio mínimo (opcional)
    - `precio_max`: Precio máximo (opcional)
    - `solo_disponibles`: Solo eventos con cupos disponibles (por defecto: false)
    - `estado`: Estado del evento (por defecto: publicado)
    - `ordenar_por`: Campo para ordenar (por defecto: -fecha)

    **Ejemplos:**
    - `/api/v1/eventos/buscar?nombre=concierto&lugar=medellin`
    - `/api/v1/eventos/buscar?categoria_id=1&precio_min=50&precio_max=200&solo_disponibles=true`
    """
    eventos = EventoRepository.buscar_eventos(
        nombre=nombre,
        categoria_id=categoria_id,
        organizador_id=organizador_id,
        lugar=lugar,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        precio_min=precio_min,
        precio_max=precio_max,
        solo_disponibles=solo_disponibles,
        estado=estado,
        ordenar_por=ordenar_por
    )
    return [
        EventoListaSchema(
            **evento_to_dict(evento),
            ticket_types_count=evento.ticket_types.count()
        )
        for evento in eventos
    ]


# Funciones auxiliares
def evento_to_dict(evento: Evento) -> dict:
    """Convertir instancia de Evento a diccionario para Pydantic"""
    # Validar que el precio sea un Decimal válido
    precio = evento.precio
    if precio is not None:
        try:
            # Asegurar que el precio es un Decimal y validar su rango
            precio = Decimal(str(precio))
            if precio < 0:
                precio = Decimal('0.00')
        except (ValueError, TypeError):
            precio = Decimal('0.00')
    else:
        precio = Decimal('0.00')

    return {
        'id': evento.id,
        'nombre': evento.nombre,
        'descripcion': evento.descripcion,
        'fecha': evento.fecha,
        'lugar': evento.lugar,
        'precio': precio,
        'cupos_disponibles': evento.cupos_disponibles,
        'estado': evento.estado,
        'categoria': {
            'id': evento.categoria.id,
            'nombre': evento.categoria.nombre,
            'descripcion': evento.categoria.descripcion,
        },
        'organizador_id': evento.organizador_id,
        'organizador_nombre': evento.organizador.nombre if evento.organizador else None,
        'fecha_creacion': evento.fecha_creacion,
        'fecha_actualizacion': evento.fecha_actualizacion,
    }
