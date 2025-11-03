"""
Repositorio de datos para la aplicación de órdenes y boletos.

Proporciona acceso abstrato a los datos de órdenes, items de órdenes y boletos
sin exponer la implementación directa del ORM de Django.

Autor: Sistema de Arquitectura - TICKIO
"""

from django.utils import timezone
from django.db.models import Q, Sum, Count, F
from datetime import timedelta
from typing import List, Optional
from uuid import UUID

from orders.models import Order, OrderItem, Ticket, TicketHold


class OrderRepository:
    """Repositorio para gestionar el acceso a datos de órdenes."""

    @staticmethod
    def find_by_user(user_id: int) -> List[Order]:
        """
        Obtiene todas las órdenes de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            List[Order]: Lista de órdenes del usuario ordenadas por fecha
        """
        return Order.objects.filter(
            user_id=user_id
        ).prefetch_related('items', 'tickets').order_by('-created_at')

    @staticmethod
    def find_by_id(order_id: int) -> Optional[Order]:
        """
        Obtiene una orden por su ID con todas las relaciones precargadas.

        Args:
            order_id: ID de la orden

        Returns:
            Optional[Order]: Orden encontrada con items y boletos, o None
        """
        return Order.objects.filter(
            id=order_id
        ).prefetch_related('items', 'tickets').first()

    @staticmethod
    def find_active_orders() -> List[Order]:
        """
        Obtiene órdenes activas (no canceladas).

        Returns:
            List[Order]: Lista de órdenes activas
        """
        return Order.objects.filter(
            status__in=['created', 'paid']
        ).select_related('user').prefetch_related('items')

    @staticmethod
    def find_orders_in_period(start_date, end_date, user_id: Optional[int] = None) -> List[Order]:
        """
        Obtiene órdenes en un período específico.

        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            user_id: ID del usuario (opcional)

        Returns:
            List[Order]: Lista de órdenes en el período
        """
        queryset = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset.select_related('user').prefetch_related('items')

    @staticmethod
    def get_order_total_by_user(user_id: int) -> dict:
        """
        Obtiene estadísticas de gastos de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            dict: Diccionario con estadísticas de gastos
        """
        stats = Order.objects.filter(
            user_id=user_id,
            status='paid'
        ).aggregate(
            total_spent=Sum('total_amount'),
            order_count=Count('id'),
            avg_order_value=Sum('total_amount') / Count('id')
        )

        return {
            'total_spent': stats.get('total_spent', 0),
            'order_count': stats.get('order_count', 0),
            'avg_order_value': stats.get('avg_order_value', 0),
        }

    @staticmethod
    def find_paid_orders() -> List[Order]:
        """
        Obtiene todas las órdenes pagadas.

        Returns:
            List[Order]: Lista de órdenes pagadas
        """
        return Order.objects.filter(
            status='paid'
        ).select_related('user').prefetch_related('items')


class OrderItemRepository:
    """Repositorio para gestionar el acceso a items de órdenes."""

    @staticmethod
    def find_by_order(order_id: int) -> List[OrderItem]:
        """
        Obtiene todos los items de una orden.

        Args:
            order_id: ID de la orden

        Returns:
            List[OrderItem]: Lista de items de la orden
        """
        return OrderItem.objects.filter(
            order_id=order_id
        ).select_related('event', 'ticket_type')

    @staticmethod
    def find_items_for_event(event_id: int) -> List[OrderItem]:
        """
        Obtiene todos los items de órdenes para un evento específico.

        Args:
            event_id: ID del evento

        Returns:
            List[OrderItem]: Lista de items del evento
        """
        return OrderItem.objects.filter(
            event_id=event_id
        ).select_related('order', 'ticket_type')

    @staticmethod
    def get_event_sales_stats(event_id: int) -> dict:
        """
        Obtiene estadísticas de ventas para un evento.

        Args:
            event_id: ID del evento

        Returns:
            dict: Diccionario con estadísticas de ventas
        """
        stats = OrderItem.objects.filter(
            event_id=event_id,
            order__status='paid'
        ).aggregate(
            total_tickets=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price')),
            orders_count=Count('order', distinct=True)
        )

        return {
            'total_tickets_sold': stats.get('total_tickets', 0),
            'total_revenue': stats.get('total_revenue', 0),
            'orders_count': stats.get('orders_count', 0),
        }


class TicketRepository:
    """Repositorio para gestionar el acceso a boletos."""

    @staticmethod
    def find_by_user(user_id: int) -> List[Ticket]:
        """
        Obtiene todos los boletos de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            List[Ticket]: Lista de boletos del usuario
        """
        return Ticket.objects.filter(
            user_id=user_id
        ).select_related('event', 'ticket_type', 'order').order_by('-created_at')

    @staticmethod
    def find_by_code(ticket_code: UUID) -> Optional[Ticket]:
        """
        Obtiene un boleto por su código único.

        Args:
            ticket_code: UUID del boleto

        Returns:
            Optional[Ticket]: Boleto encontrado o None
        """
        return Ticket.objects.filter(
            unique_code=ticket_code
        ).select_related('event', 'ticket_type', 'order', 'user').first()

    @staticmethod
    def find_by_order(order_id: int) -> List[Ticket]:
        """
        Obtiene todos los boletos de una orden.

        Args:
            order_id: ID de la orden

        Returns:
            List[Ticket]: Lista de boletos de la orden
        """
        return Ticket.objects.filter(
            order_id=order_id
        ).select_related('event', 'ticket_type')

    @staticmethod
    def find_unused_tickets_for_event(event_id: int) -> List[Ticket]:
        """
        Obtiene los boletos no usados de un evento.

        Args:
            event_id: ID del evento

        Returns:
            List[Ticket]: Lista de boletos no usados
        """
        return Ticket.objects.filter(
            event_id=event_id,
            is_used=False,
            order__status='paid'
        ).select_related('user', 'ticket_type')

    @staticmethod
    def mark_as_used(ticket_code: UUID) -> bool:
        """
        Marca un boleto como usado.

        Args:
            ticket_code: UUID del boleto

        Returns:
            bool: True si se actualizó exitosamente, False en caso contrario
        """
        ticket = Ticket.objects.filter(unique_code=ticket_code).first()
        if ticket and not ticket.is_used:
            ticket.is_used = True
            ticket.save()
            return True
        return False

    @staticmethod
    def get_event_attendance_stats(event_id: int) -> dict:
        """
        Obtiene estadísticas de asistencia para un evento.

        Args:
            event_id: ID del evento

        Returns:
            dict: Diccionario con estadísticas de asistencia
        """
        stats = Ticket.objects.filter(
            event_id=event_id,
            order__status='paid'
        ).aggregate(
            total_tickets=Count('id'),
            tickets_used=Count('id', filter=Q(is_used=True)),
            tickets_unused=Count('id', filter=Q(is_used=False))
        )

        return {
            'total_tickets': stats.get('total_tickets', 0),
            'tickets_used': stats.get('tickets_used', 0),
            'tickets_unused': stats.get('tickets_unused', 0),
            'attendance_rate': (
                stats.get('tickets_used', 0) / stats.get('total_tickets', 1) * 100
                if stats.get('total_tickets', 0) > 0 else 0
            ),
        }

    @staticmethod
    def find_valid_tickets_for_event(event_id: int) -> List[Ticket]:
        """
        Obtiene los boletos válidos (pagos no usados) de un evento.

        Args:
            event_id: ID del evento

        Returns:
            List[Ticket]: Lista de boletos válidos
        """
        return Ticket.objects.filter(
            event_id=event_id,
            order__status='paid',
            is_used=False
        ).select_related('user', 'ticket_type')


class TicketHoldRepository:
    """Repositorio para gestionar el acceso a las retenciones de boletos."""

    @staticmethod
    def find_active_holds() -> List[TicketHold]:
        """
        Obtiene todas las retenciones activas (no expiradas).

        Returns:
            List[TicketHold]: Lista de retenciones activas
        """
        return TicketHold.objects.filter(
            expires_at__gt=timezone.now()
        ).select_related('ticket_type', 'user')

    @staticmethod
    def find_expired_holds() -> List[TicketHold]:
        """
        Obtiene todas las retenciones expiradas.

        Returns:
            List[TicketHold]: Lista de retenciones expiradas
        """
        return TicketHold.objects.filter(
            expires_at__lte=timezone.now()
        )

    @staticmethod
    def find_by_session(session_key: str) -> List[TicketHold]:
        """
        Obtiene retenciones activas por clave de sesión.

        Args:
            session_key: Clave de sesión

        Returns:
            List[TicketHold]: Lista de retenciones de la sesión
        """
        return TicketHold.objects.filter(
            session_key=session_key,
            expires_at__gt=timezone.now()
        ).select_related('ticket_type')

    @staticmethod
    def find_by_ticket_type(ticket_type_id: int) -> List[TicketHold]:
        """
        Obtiene retenciones activas por tipo de boleto.

        Args:
            ticket_type_id: ID del tipo de boleto

        Returns:
            List[TicketHold]: Lista de retenciones del tipo de boleto
        """
        return TicketHold.objects.filter(
            ticket_type_id=ticket_type_id,
            expires_at__gt=timezone.now()
        )

    @staticmethod
    def get_total_held_quantity(ticket_type_id: int) -> int:
        """
        Obtiene la cantidad total de boletos retenidos para un tipo de boleto.

        Args:
            ticket_type_id: ID del tipo de boleto

        Returns:
            int: Cantidad total de boletos retenidos
        """
        result = TicketHold.objects.filter(
            ticket_type_id=ticket_type_id,
            expires_at__gt=timezone.now()
        ).aggregate(total=Sum('quantity'))

        return result.get('total', 0) or 0

    @staticmethod
    def cleanup_expired_holds() -> int:
        """
        Elimina todas las retenciones expiradas.

        Returns:
            int: Cantidad de retenciones eliminadas
        """
        deleted_count, _ = TicketHold.objects.filter(
            expires_at__lte=timezone.now()
        ).delete()

        return deleted_count
