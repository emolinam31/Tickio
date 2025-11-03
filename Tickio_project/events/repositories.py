"""
Repositorio de datos para la aplicación de eventos.

Proporciona acceso abstrato a los datos de eventos, categorías y tipos de boletos
sin exponer la implementación directa del ORM de Django.

Autor: Sistema de Arquitectura - TICKIO
"""

from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from typing import List, Optional

from events.models import Evento, CategoriaEvento, TicketType


class EventRepository:
    """Repositorio para gestionar el acceso a datos de eventos."""

    @staticmethod
    def find_upcoming_events() -> List[Evento]:
        """
        Obtiene todos los eventos futuros publicados ordenados por fecha.

        Returns:
            List[Evento]: Lista de eventos próximos publicados
        """
        return Evento.objects.filter(
            fecha__gte=timezone.now().date(),
            estado='publicado'
        ).select_related('categoria', 'organizador').order_by('fecha')

    @staticmethod
    def find_events_by_category(category_id: int) -> List[Evento]:
        """
        Obtiene eventos publicados de una categoría específica.

        Args:
            category_id: ID de la categoría

        Returns:
            List[Evento]: Lista de eventos en la categoría
        """
        return Evento.objects.filter(
            categoria_id=category_id,
            estado='publicado',
            fecha__gte=timezone.now().date()
        ).select_related('categoria', 'organizador').order_by('fecha')

    @staticmethod
    def find_events_with_available_tickets() -> List[Evento]:
        """
        Obtiene eventos publicados que tienen boletos disponibles.

        Returns:
            List[Evento]: Lista de eventos con disponibilidad
        """
        return Evento.objects.filter(
            estado='publicado',
            fecha__gte=timezone.now().date(),
            ticket_types__active=True,
            ticket_types__capacity__gt=0
        ).distinct().select_related('categoria', 'organizador').order_by('fecha')

    @staticmethod
    def find_by_id(event_id: int) -> Optional[Evento]:
        """
        Obtiene un evento por su ID con todas las relaciones precargadas.

        Args:
            event_id: ID del evento

        Returns:
            Optional[Evento]: Evento encontrado o None
        """
        return Evento.objects.filter(
            id=event_id
        ).select_related('categoria', 'organizador').prefetch_related('ticket_types').first()

    @staticmethod
    def find_by_organizer(organizer_id: int) -> List[Evento]:
        """
        Obtiene todos los eventos de un organizador específico.

        Args:
            organizer_id: ID del organizador

        Returns:
            List[Evento]: Lista de eventos del organizador
        """
        return Evento.objects.filter(
            organizador_id=organizer_id
        ).select_related('categoria').prefetch_related('ticket_types').order_by('-fecha_creacion')

    @staticmethod
    def search_events(query: str, category_id: Optional[int] = None,
                     location: Optional[str] = None,
                     date_from: Optional[str] = None) -> List[Evento]:
        """
        Busca eventos con múltiples criterios.

        Args:
            query: Término de búsqueda (nombre o descripción)
            category_id: ID de categoría (opcional)
            location: Lugar (opcional)
            date_from: Fecha mínima en formato YYYY-MM-DD (opcional)

        Returns:
            List[Evento]: Lista de eventos que coinciden con los criterios
        """
        queryset = Evento.objects.filter(
            estado='publicado',
            fecha__gte=timezone.now().date()
        ).select_related('categoria', 'organizador')

        # Búsqueda de texto
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) | Q(descripcion__icontains=query)
            )

        # Filtro de categoría
        if category_id:
            queryset = queryset.filter(categoria_id=category_id)

        # Filtro de lugar
        if location:
            queryset = queryset.filter(lugar__icontains=location)

        # Filtro de fecha mínima
        if date_from:
            try:
                queryset = queryset.filter(fecha__gte=date_from)
            except ValueError:
                pass  # Ignorar fechas inválidas

        return queryset.order_by('fecha')

    @staticmethod
    def get_event_stats(event_id: int) -> dict:
        """
        Obtiene estadísticas de un evento.

        Args:
            event_id: ID del evento

        Returns:
            dict: Diccionario con estadísticas del evento
        """
        event = Evento.objects.filter(id=event_id).first()
        if not event:
            return {}

        ticket_types = event.ticket_types.all()
        total_capacity = sum(tt.capacity for tt in ticket_types)
        total_sold = sum(tt.sold for tt in ticket_types)
        total_available = total_capacity - total_sold

        return {
            'event_id': event.id,
            'total_capacity': total_capacity,
            'total_sold': total_sold,
            'total_available': total_available,
            'occupancy_percentage': (total_sold / total_capacity * 100) if total_capacity > 0 else 0,
            'ticket_types_count': ticket_types.count(),
        }

    @staticmethod
    def find_past_events(organizer_id: Optional[int] = None) -> List[Evento]:
        """
        Obtiene eventos pasados.

        Args:
            organizer_id: ID del organizador (opcional)

        Returns:
            List[Evento]: Lista de eventos pasados
        """
        queryset = Evento.objects.filter(fecha__lt=timezone.now().date())

        if organizer_id:
            queryset = queryset.filter(organizador_id=organizer_id)

        return queryset.select_related('categoria', 'organizador').order_by('-fecha')


class CategoryRepository:
    """Repositorio para gestionar el acceso a datos de categorías de eventos."""

    @staticmethod
    def find_all() -> List[CategoriaEvento]:
        """
        Obtiene todas las categorías de eventos.

        Returns:
            List[CategoriaEvento]: Lista de todas las categorías
        """
        return CategoriaEvento.objects.all().order_by('nombre')

    @staticmethod
    def find_by_id(category_id: int) -> Optional[CategoriaEvento]:
        """
        Obtiene una categoría por su ID.

        Args:
            category_id: ID de la categoría

        Returns:
            Optional[CategoriaEvento]: Categoría encontrada o None
        """
        return CategoriaEvento.objects.filter(id=category_id).first()

    @staticmethod
    def find_with_events() -> List[CategoriaEvento]:
        """
        Obtiene categorías que tienen eventos publicados.

        Returns:
            List[CategoriaEvento]: Lista de categorías con eventos
        """
        return CategoriaEvento.objects.filter(
            evento__estado='publicado'
        ).distinct().order_by('nombre')


class TicketTypeRepository:
    """Repositorio para gestionar el acceso a datos de tipos de boletos."""

    @staticmethod
    def find_by_event(event_id: int) -> List[TicketType]:
        """
        Obtiene todos los tipos de boletos de un evento.

        Args:
            event_id: ID del evento

        Returns:
            List[TicketType]: Lista de tipos de boletos
        """
        return TicketType.objects.filter(
            event_id=event_id,
            active=True
        ).order_by('price')

    @staticmethod
    def find_by_id(ticket_type_id: int) -> Optional[TicketType]:
        """
        Obtiene un tipo de boleto por su ID.

        Args:
            ticket_type_id: ID del tipo de boleto

        Returns:
            Optional[TicketType]: Tipo de boleto encontrado o None
        """
        return TicketType.objects.filter(id=ticket_type_id).first()

    @staticmethod
    def find_with_availability(event_id: int) -> List[TicketType]:
        """
        Obtiene tipos de boletos disponibles de un evento.

        Args:
            event_id: ID del evento

        Returns:
            List[TicketType]: Tipos de boletos con disponibilidad
        """
        return TicketType.objects.filter(
            event_id=event_id,
            active=True
        ).exclude(
            capacity=0
        ).order_by('price')

    @staticmethod
    def check_availability(ticket_type_id: int, quantity: int) -> bool:
        """
        Verifica si hay suficientes boletos disponibles.

        Args:
            ticket_type_id: ID del tipo de boleto
            quantity: Cantidad requerida

        Returns:
            bool: True si hay disponibilidad, False en caso contrario
        """
        ticket_type = TicketType.objects.filter(id=ticket_type_id).first()
        if not ticket_type:
            return False

        available = max(ticket_type.capacity - ticket_type.sold, 0)
        return available >= quantity

    @staticmethod
    def get_total_availability(event_id: int) -> int:
        """
        Obtiene la disponibilidad total de un evento.

        Args:
            event_id: ID del evento

        Returns:
            int: Total de boletos disponibles
        """
        ticket_types = TicketType.objects.filter(event_id=event_id)
        return sum(
            max(tt.capacity - tt.sold, 0) for tt in ticket_types
        )
