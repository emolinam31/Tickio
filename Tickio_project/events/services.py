"""
Servicios de negocio para la aplicación de eventos.

Proporciona la lógica de negocio de alto nivel para operaciones con eventos,
categorías y tipos de boletos. Utiliza el Repository Pattern y separa
responsabilidades según principios SOLID.

Autor: Sistema de Arquitectura - TICKIO
"""

from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from typing import List, Optional, Dict
from decimal import Decimal

from events.models import Evento, CategoriaEvento, TicketType
from events.repositories import (
    EventRepository, CategoryRepository, TicketTypeRepository
)


class EventService:
    """Servicio para gestionar operaciones relacionadas con eventos."""

    @staticmethod
    def create_event(organizer, nombre: str, descripcion: str,
                    fecha, lugar: str, categoria_id: int,
                    cupos_disponibles: int = 0) -> Evento:
        """
        Crea un nuevo evento en estado de borrador.

        Args:
            organizer: Usuario organizador que crea el evento
            nombre: Nombre del evento
            descripcion: Descripción del evento
            fecha: Fecha del evento
            lugar: Lugar del evento
            categoria_id: ID de la categoría
            cupos_disponibles: Cupos disponibles (deprecado, se usa TicketType)

        Returns:
            Evento: Evento creado

        Raises:
            ValidationError: Si hay errores en la validación
        """
        # Validar fecha
        if fecha < timezone.now().date():
            raise ValidationError("La fecha del evento no puede ser en el pasado")

        # Validar que la categoría existe
        category = CategoryRepository.find_by_id(categoria_id)
        if not category:
            raise ValidationError("Categoría no encontrada")

        # Crear evento
        evento = Evento.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            fecha=fecha,
            lugar=lugar,
            categoria_id=categoria_id,
            organizador=organizer,
            cupos_disponibles=cupos_disponibles,
            estado='borrador'
        )

        return evento

    @staticmethod
    def publish_event(event_id: int) -> Evento:
        """
        Publica un evento (cambia su estado a 'publicado').

        Args:
            event_id: ID del evento a publicar

        Returns:
            Evento: Evento publicado

        Raises:
            ValidationError: Si el evento no puede ser publicado
        """
        evento = EventRepository.find_by_id(event_id)
        if not evento:
            raise ValidationError("Evento no encontrado")

        if evento.estado == 'publicado':
            raise ValidationError("El evento ya está publicado")

        # Validar que tenga al menos un tipo de boleto
        ticket_types = evento.ticket_types.filter(active=True)
        if not ticket_types.exists():
            raise ValidationError("El evento debe tener al menos un tipo de boleto activo")

        evento.estado = 'publicado'
        evento.save()

        return evento

    @staticmethod
    def pause_event(event_id: int) -> Evento:
        """
        Pausa un evento (cambia su estado a 'pausado').

        Args:
            event_id: ID del evento a pausar

        Returns:
            Evento: Evento pausado

        Raises:
            ValidationError: Si el evento no puede ser pausado
        """
        evento = EventRepository.find_by_id(event_id)
        if not evento:
            raise ValidationError("Evento no encontrado")

        if evento.estado != 'publicado':
            raise ValidationError("Solo se pueden pausar eventos publicados")

        evento.estado = 'pausado'
        evento.save()

        return evento

    @staticmethod
    def resume_event(event_id: int) -> Evento:
        """
        Reanuda un evento (cambia su estado a 'publicado').

        Args:
            event_id: ID del evento a reanudar

        Returns:
            Evento: Evento reanudado

        Raises:
            ValidationError: Si el evento no puede ser reanudado
        """
        evento = EventRepository.find_by_id(event_id)
        if not evento:
            raise ValidationError("Evento no encontrado")

        if evento.estado != 'pausado':
            raise ValidationError("Solo se pueden reanudar eventos pausados")

        evento.estado = 'publicado'
        evento.save()

        return evento

    @staticmethod
    def cancel_event(event_id: int) -> Evento:
        """
        Cancela un evento (cambia su estado a 'borrador').

        Args:
            event_id: ID del evento a cancelar

        Returns:
            Evento: Evento cancelado

        Raises:
            ValidationError: Si el evento no puede ser cancelado
        """
        evento = EventRepository.find_by_id(event_id)
        if not evento:
            raise ValidationError("Evento no encontrado")

        evento.estado = 'borrador'
        evento.save()

        return evento

    @staticmethod
    def get_event_stats(event_id: int) -> Dict:
        """
        Obtiene estadísticas detalladas de un evento.

        Args:
            event_id: ID del evento

        Returns:
            Dict: Diccionario con estadísticas del evento
        """
        return EventRepository.get_event_stats(event_id)

    @staticmethod
    def search_events(query: str = "", category_id: Optional[int] = None,
                     location: Optional[str] = None,
                     date_from: Optional[str] = None) -> List[Evento]:
        """
        Busca eventos con múltiples criterios.

        Args:
            query: Término de búsqueda
            category_id: ID de categoría (opcional)
            location: Lugar (opcional)
            date_from: Fecha mínima en formato YYYY-MM-DD (opcional)

        Returns:
            List[Evento]: Lista de eventos que coinciden
        """
        return EventRepository.search_events(
            query=query,
            category_id=category_id,
            location=location,
            date_from=date_from
        )

    @staticmethod
    def get_upcoming_events() -> List[Evento]:
        """
        Obtiene todos los eventos publicados próximos.

        Returns:
            List[Evento]: Lista de eventos próximos
        """
        return EventRepository.find_upcoming_events()

    @staticmethod
    def get_available_events() -> List[Evento]:
        """
        Obtiene eventos publicados que tienen boletos disponibles.

        Returns:
            List[Evento]: Lista de eventos con disponibilidad
        """
        return EventRepository.find_events_with_available_tickets()


class EventTicketService:
    """Servicio para gestionar operaciones relacionadas con tipos de boletos."""

    @staticmethod
    def create_ticket_type(event_id: int, name: str, price: Decimal,
                          capacity: int) -> TicketType:
        """
        Crea un nuevo tipo de boleto para un evento.

        Args:
            event_id: ID del evento
            name: Nombre del tipo de boleto
            price: Precio unitario
            capacity: Capacidad máxima

        Returns:
            TicketType: Tipo de boleto creado

        Raises:
            ValidationError: Si hay errores en la validación
        """
        # Validar evento
        evento = EventRepository.find_by_id(event_id)
        if not evento:
            raise ValidationError("Evento no encontrado")

        # Validar precio
        if price < 0:
            raise ValidationError("El precio no puede ser negativo")

        # Validar capacidad
        if capacity <= 0:
            raise ValidationError("La capacidad debe ser mayor a 0")

        # Crear tipo de boleto
        ticket_type = TicketType.objects.create(
            event_id=event_id,
            name=name,
            price=price,
            capacity=capacity,
            sold=0,
            active=True
        )

        return ticket_type

    @staticmethod
    def deactivate_ticket_type(ticket_type_id: int) -> TicketType:
        """
        Desactiva un tipo de boleto.

        Args:
            ticket_type_id: ID del tipo de boleto

        Returns:
            TicketType: Tipo de boleto desactivado

        Raises:
            ValidationError: Si el tipo de boleto no existe
        """
        ticket_type = TicketTypeRepository.find_by_id(ticket_type_id)
        if not ticket_type:
            raise ValidationError("Tipo de boleto no encontrado")

        ticket_type.active = False
        ticket_type.save()

        return ticket_type

    @staticmethod
    def get_event_ticket_types(event_id: int) -> List[TicketType]:
        """
        Obtiene todos los tipos de boletos de un evento.

        Args:
            event_id: ID del evento

        Returns:
            List[TicketType]: Lista de tipos de boletos
        """
        return TicketTypeRepository.find_by_event(event_id)

    @staticmethod
    def get_available_ticket_types(event_id: int) -> List[TicketType]:
        """
        Obtiene tipos de boletos disponibles de un evento.

        Args:
            event_id: ID del evento

        Returns:
            List[TicketType]: Tipos de boletos con disponibilidad
        """
        return TicketTypeRepository.find_with_availability(event_id)

    @staticmethod
    def check_ticket_availability(ticket_type_id: int, quantity: int) -> bool:
        """
        Verifica disponibilidad de boletos.

        Args:
            ticket_type_id: ID del tipo de boleto
            quantity: Cantidad solicitada

        Returns:
            bool: True si hay disponibilidad
        """
        return TicketTypeRepository.check_availability(ticket_type_id, quantity)


class CategoryService:
    """Servicio para gestionar categorías de eventos."""

    @staticmethod
    def get_all_categories() -> List[CategoriaEvento]:
        """
        Obtiene todas las categorías.

        Returns:
            List[CategoriaEvento]: Lista de categorías
        """
        return CategoryRepository.find_all()

    @staticmethod
    def get_categories_with_events() -> List[CategoriaEvento]:
        """
        Obtiene categorías que tienen eventos publicados.

        Returns:
            List[CategoriaEvento]: Categorías con eventos
        """
        return CategoryRepository.find_with_events()

    @staticmethod
    def get_category_by_id(category_id: int) -> Optional[CategoriaEvento]:
        """
        Obtiene una categoría por su ID.

        Args:
            category_id: ID de la categoría

        Returns:
            Optional[CategoriaEvento]: Categoría encontrada o None
        """
        return CategoryRepository.find_by_id(category_id)
