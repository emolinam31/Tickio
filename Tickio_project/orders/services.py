"""
Servicios de negocio para la aplicación de órdenes.

Proporciona la lógica de negocio de alto nivel para checkouts,
pagos y gestión de boletos. Utiliza el Repository Pattern para
acceso a datos y separa responsabilidades según principios SOLID.

Autor: Sistema de Arquitectura - TICKIO
"""

from decimal import Decimal
from typing import Dict, Tuple, List, Optional
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError

from orders.models import Order, OrderItem, Ticket
from orders.repositories import (
    OrderRepository, TicketRepository, TicketHoldRepository
)
from events.models import TicketType
from events.repositories import TicketTypeRepository
from payments.interfaces import PaymentGateway


class TicketService:
    """Servicio para gestionar operaciones relacionadas con boletos."""

    @staticmethod
    def validate_ticket_availability(ticket_type_id: int, quantity: int) -> bool:
        """
        Valida que haya disponibilidad de boletos.

        Args:
            ticket_type_id: ID del tipo de boleto
            quantity: Cantidad solicitada

        Returns:
            bool: True si hay disponibilidad

        Raises:
            ValidationError: Si no hay disponibilidad suficiente
        """
        if not TicketTypeRepository.check_availability(ticket_type_id, quantity):
            raise ValidationError(
                f"No hay suficientes boletos disponibles. Solicitó {quantity}."
            )

        return True

    @staticmethod
    def calculate_total_price(cart: Dict[str, dict]) -> Decimal:
        """
        Calcula el precio total del carrito.

        Args:
            cart: Diccionario del carrito con formato {'key': {'ticket_type_id': int, 'quantity': int}}

        Returns:
            Decimal: Precio total

        Raises:
            ValidationError: Si hay errores en los datos del carrito
        """
        if not cart:
            raise ValidationError("El carrito está vacío")

        total = Decimal('0.00')

        for key, data in cart.items():
            try:
                ticket_type_id = int(data.get('ticket_type_id', 0))
                quantity = int(data.get('quantity', 0))

                if quantity <= 0:
                    raise ValidationError(f"Cantidad inválida en item {key}")

                ticket_type = TicketType.objects.get(id=ticket_type_id, active=True)
                total += ticket_type.price * quantity

            except (KeyError, ValueError) as e:
                raise ValidationError(f"Formato inválido en carrito: {str(e)}")
            except TicketType.DoesNotExist:
                raise ValidationError(f"Tipo de boleto no encontrado o inactivo")

        return total

    @staticmethod
    def create_tickets_for_order(order: Order) -> List[Ticket]:
        """
        Crea boletos individuales para una orden.

        Args:
            order: Orden para la cual crear boletos

        Returns:
            List[Ticket]: Lista de boletos creados
        """
        tickets_to_create = []

        for item in order.items.all():
            for _ in range(item.quantity):
                tickets_to_create.append(
                    Ticket(
                        order=order,
                        ticket_type=item.ticket_type,
                        user=order.user,
                        event=item.event
                    )
                )

        return Ticket.objects.bulk_create(tickets_to_create)


class OrderService:
    """Servicio para gestionar operaciones de órdenes y checkouts."""

    def __init__(self, payment_gateway: Optional[PaymentGateway] = None):
        """
        Inicializa el servicio de órdenes.

        Args:
            payment_gateway: Gateway de pagos (usará DummyGateway si no se proporciona)
        """
        self.payment_gateway = payment_gateway
        self.ticket_service = TicketService()

    def get_payment_gateway(self) -> PaymentGateway:
        """
        Obtiene el gateway de pagos, usando el default si es necesario.

        Returns:
            PaymentGateway: Gateway de pagos configurado
        """
        if self.payment_gateway is None:
            from payments.adapters.dummy import DummyGateway
            self.payment_gateway = DummyGateway()

        return self.payment_gateway

    def validate_checkout_request(self, cart: Dict[str, dict], user) -> None:
        """
        Valida que el checkout sea posible.

        Args:
            cart: Carrito del usuario
            user: Usuario que realiza la compra

        Raises:
            ValidationError: Si hay errores en la validación
        """
        if not cart:
            raise ValidationError("El carrito está vacío")

        if not user or not user.is_authenticated:
            raise ValidationError("Es necesario iniciar sesión para comprar")

        # Validar disponibilidad de cada item
        for key, data in cart.items():
            ticket_type_id = data.get('ticket_type_id')
            quantity = int(data.get('quantity', 0))

            self.ticket_service.validate_ticket_availability(ticket_type_id, quantity)

    def create_order_items(self, order: Order, cart: Dict[str, dict]) -> Decimal:
        """
        Crea los items de la orden a partir del carrito.

        Args:
            order: Orden a la cual agregar items
            cart: Carrito del usuario

        Returns:
            Decimal: Total calculado

        Raises:
            ValidationError: Si hay errores en la creación de items
        """
        order_items = []
        total = Decimal('0.00')

        for key, data in cart.items():
            try:
                # Usar select_for_update para evitar condiciones de carrera
                ticket_type = (
                    TicketType.objects.select_for_update()
                    .select_related('event')
                    .get(pk=data['ticket_type_id'], active=True)
                )
                quantity = int(data['quantity'])

                # Validar disponibilidad actual
                if ticket_type.sold + quantity > ticket_type.capacity:
                    raise ValidationError(
                        f"No hay disponibilidad suficiente para {ticket_type.name}"
                    )

                # Actualizar stock
                TicketType.objects.filter(pk=ticket_type.pk).update(
                    sold=F('sold') + quantity
                )

                # Crear item de orden
                line_total = ticket_type.price * quantity
                total += line_total

                order_items.append(OrderItem(
                    order=order,
                    event=ticket_type.event,
                    ticket_type=ticket_type,
                    name=ticket_type.name,
                    unit_price=ticket_type.price,
                    quantity=quantity,
                    line_total=line_total,
                ))

            except TicketType.DoesNotExist:
                raise ValidationError("Tipo de boleto no encontrado o inactivo")
            except (KeyError, ValueError) as e:
                raise ValidationError(f"Error procesando carrito: {str(e)}")

        OrderItem.objects.bulk_create(order_items)
        return total

    @transaction.atomic
    def checkout(self, cart: Dict[str, dict], user) -> Order:
        """
        Ejecuta el proceso completo de checkout.

        Realiza:
        1. Validación del carrito y usuario
        2. Cálculo del total
        3. Creación de orden e items
        4. Procesamiento de pago
        5. Creación de boletos

        Args:
            cart: Carrito del usuario
            user: Usuario que realiza la compra

        Returns:
            Order: Orden creada y pagada

        Raises:
            ValidationError: Si hay errores en cualquier paso del checkout
        """
        # Validar checkout
        self.validate_checkout_request(cart, user)

        # Crear orden
        order = Order.objects.create(user=user)

        try:
            # Crear items y obtener total
            total = self.create_order_items(order, cart)

            # Procesar pago
            gateway = self.get_payment_gateway()
            success, reference = gateway.charge(
                total,
                metadata={"order_id": order.id, "user_id": user.id}
            )

            if not success:
                raise ValidationError("El pago fue rechazado. Por favor intente de nuevo.")

            # Actualizar orden con información de pago
            order.total_amount = total
            order.status = 'paid'
            order.save()

            # Crear boletos individuales
            self.ticket_service.create_tickets_for_order(order)

            return order

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Error durante el checkout: {str(e)}")


class PaymentService:
    """Servicio para gestionar operaciones relacionadas con pagos."""

    def __init__(self, payment_gateway: PaymentGateway):
        """
        Inicializa el servicio de pagos.

        Args:
            payment_gateway: Gateway de pagos a utilizar
        """
        self.gateway = payment_gateway

    def process_payment(self, order: Order) -> Tuple[bool, str]:
        """
        Procesa el pago de una orden.

        Args:
            order: Orden a pagar

        Returns:
            Tuple[bool, str]: (éxito, referencia de transacción)
        """
        success, reference = self.gateway.charge(
            order.total_amount,
            metadata={"order_id": order.id}
        )
        return success, reference

    def refund_booking(self, order: Order) -> bool:
        """
        Reembolsa una orden (placeholder para implementación futura).

        Args:
            order: Orden a reembolsar

        Returns:
            bool: True si el reembolso fue exitoso
        """
        # Implementación futura con gateway específico
        # Por ahora solo marca el estado
        order.status = 'refunded'
        order.save()
        return True


# Función de compatibilidad hacia atrás
def checkout(cart: Dict[str, dict], user=None, gateway: PaymentGateway | None = None) -> Order:
    """
    Función legacy de checkout para compatibilidad hacia atrás.

    DEPRECADO: Use OrderService.checkout() en su lugar.

    Args:
        cart: Carrito del usuario
        user: Usuario que realiza la compra
        gateway: Gateway de pagos (opcional)

    Returns:
        Order: Orden creada

    Raises:
        ValidationError: Si hay errores en el checkout
    """
    order_service = OrderService(payment_gateway=gateway)
    return order_service.checkout(cart, user)


