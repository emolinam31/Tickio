from django.db.models import Q, Prefetch
from datetime import date
from decimal import Decimal
from typing import List, Optional
from events.models import Evento, TicketType


class EventoRepository:
    """Repositorio para manejar consultas de eventos"""

    @staticmethod
    def get_all_eventos(estado: str = 'publicado',
                       ordenar_por: str = '-fecha') -> List[Evento]:
        """
        Obtener todos los eventos

        Args:
            estado: Estado del evento ('publicado', 'borrador', 'pausado', None para todos)
            ordenar_por: Campo para ordenar (ej: '-fecha', 'nombre')

        Returns:
            Lista de eventos
        """
        queryset = Evento.objects.select_related('categoria', 'organizador')

        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset.order_by(ordenar_por)

    @staticmethod
    def get_evento_by_id(evento_id: int) -> Optional[Evento]:
        """
        Obtener un evento por ID

        Args:
            evento_id: ID del evento

        Returns:
            Evento o None
        """
        ticket_types = TicketType.objects.filter(active=True)
        prefetch = Prefetch('ticket_types', queryset=ticket_types)

        return (
            Evento.objects
            .select_related('categoria', 'organizador')
            .prefetch_related(prefetch)
            .filter(id=evento_id, estado='publicado')
            .first()
        )

    @staticmethod
    def get_eventos_by_nombre(nombre: str, estado: str = 'publicado') -> List[Evento]:
        """
        Buscar eventos por nombre (búsqueda parcial, case-insensitive)

        Args:
            nombre: Nombre del evento a buscar
            estado: Estado del evento

        Returns:
            Lista de eventos
        """
        queryset = Evento.objects.select_related('categoria', 'organizador')

        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset.filter(nombre__icontains=nombre).order_by('nombre')

    @staticmethod
    def get_eventos_by_categoria(categoria_id: int, estado: str = 'publicado') -> List[Evento]:
        """
        Obtener eventos por categoría

        Args:
            categoria_id: ID de la categoría
            estado: Estado del evento

        Returns:
            Lista de eventos
        """
        queryset = Evento.objects.select_related('categoria', 'organizador')

        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset.filter(categoria_id=categoria_id).order_by('-fecha')

    @staticmethod
    def get_eventos_by_organizador(organizador_id: int, estado: str = None) -> List[Evento]:
        """
        Obtener eventos por organizador

        Args:
            organizador_id: ID del organizador
            estado: Estado del evento (None para todos los estados)

        Returns:
            Lista de eventos
        """
        queryset = Evento.objects.select_related('categoria', 'organizador')
        queryset = queryset.filter(organizador_id=organizador_id)

        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset.order_by('-fecha')

    @staticmethod
    def get_eventos_by_fecha(fecha_inicio: date, fecha_fin: date, estado: str = 'publicado') -> List[Evento]:
        """
        Obtener eventos en un rango de fechas

        Args:
            fecha_inicio: Fecha inicial (inclusive)
            fecha_fin: Fecha final (inclusive)
            estado: Estado del evento

        Returns:
            Lista de eventos
        """
        queryset = Evento.objects.select_related('categoria', 'organizador')

        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset.filter(
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin
        ).order_by('fecha')

    @staticmethod
    def get_eventos_by_lugar(lugar: str, estado: str = 'publicado') -> List[Evento]:
        """
        Buscar eventos por lugar (búsqueda parcial, case-insensitive)

        Args:
            lugar: Lugar del evento a buscar
            estado: Estado del evento

        Returns:
            Lista de eventos
        """
        queryset = Evento.objects.select_related('categoria', 'organizador')

        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset.filter(lugar__icontains=lugar).order_by('nombre')

    @staticmethod
    def get_eventos_disponibles(estado: str = 'publicado') -> List[Evento]:
        """
        Obtener solo eventos que aún tienen cupos disponibles

        Args:
            estado: Estado del evento

        Returns:
            Lista de eventos con cupos disponibles
        """
        queryset = Evento.objects.select_related('categoria', 'organizador')

        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset.filter(cupos_disponibles__gt=0).order_by('-fecha')

    @staticmethod
    def get_eventos_por_rango_precio(precio_min: Decimal, precio_max: Decimal,
                                    estado: str = 'publicado') -> List[Evento]:
        """
        Obtener eventos dentro de un rango de precio

        Args:
            precio_min: Precio mínimo
            precio_max: Precio máximo
            estado: Estado del evento

        Returns:
            Lista de eventos
        """
        queryset = Evento.objects.select_related('categoria', 'organizador')

        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset.filter(
            precio__gte=precio_min,
            precio__lte=precio_max
        ).order_by('precio')

    @staticmethod
    def buscar_eventos(
        nombre: Optional[str] = None,
        categoria_id: Optional[int] = None,
        organizador_id: Optional[int] = None,
        lugar: Optional[str] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        precio_min: Optional[Decimal] = None,
        precio_max: Optional[Decimal] = None,
        solo_disponibles: bool = False,
        estado: str = 'publicado',
        ordenar_por: str = '-fecha'
    ) -> List[Evento]:
        """
        Búsqueda avanzada de eventos con múltiples filtros

        Args:
            nombre: Nombre del evento (búsqueda parcial)
            categoria_id: ID de la categoría
            organizador_id: ID del organizador
            lugar: Lugar del evento (búsqueda parcial)
            fecha_inicio: Fecha de inicio (inclusive)
            fecha_fin: Fecha de fin (inclusive)
            precio_min: Precio mínimo
            precio_max: Precio máximo
            solo_disponibles: Solo eventos con cupos disponibles
            estado: Estado del evento
            ordenar_por: Campo para ordenar

        Returns:
            Lista de eventos filtrados
        """
        queryset = Evento.objects.select_related('categoria', 'organizador')

        if estado:
            queryset = queryset.filter(estado=estado)

        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)

        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)

        if organizador_id:
            queryset = queryset.filter(organizador_id=organizador_id)

        if lugar:
            queryset = queryset.filter(lugar__icontains=lugar)

        if fecha_inicio:
            queryset = queryset.filter(fecha__gte=fecha_inicio)

        if fecha_fin:
            queryset = queryset.filter(fecha__lte=fecha_fin)

        if precio_min is not None:
            queryset = queryset.filter(precio__gte=precio_min)

        if precio_max is not None:
            queryset = queryset.filter(precio__lte=precio_max)

        if solo_disponibles:
            queryset = queryset.filter(cupos_disponibles__gt=0)

        return queryset.order_by(ordenar_por)
