"""
Modelos de órdenes y boletos para la aplicación de eventos.

Proporciona los modelos para gestionar órdenes, items de órdenes, boletos
y retenciones temporales de boletos.

Autor: Sistema de Arquitectura - TICKIO
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from events.models import Evento, TicketType
import uuid


class Order(models.Model):
    """Modelo para gestionar órdenes de compra."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Usuario"),
        related_name='orders'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Fecha de creación")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Fecha de actualización")
    )
    status = models.CharField(
        max_length=20,
        default='created',
        verbose_name=_("Estado"),
        help_text=_("Estado de la orden: created, paid, refunded")
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Monto total")
    )

    class Meta:
        verbose_name = _("Orden")
        verbose_name_plural = _("Órdenes")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Orden #{self.id} - {self.user}"

    def get_total_items(self) -> int:
        """Retorna el total de items en la orden."""
        return sum(item.quantity for item in self.items.all())


# ============================================================================
# MODELO DE RESERVA (BOOKING) - Abstracción alternativa para órdenes
# ============================================================================

BOOKING_STATUS_CHOICES = [
    ('pending', _('Pendiente')),
    ('confirmed', _('Confirmada')),
    ('paid', _('Pagada')),
    ('cancelled', _('Cancelada')),
    ('refunded', _('Reembolsada')),
]


class Booking(models.Model):
    """
    Modelo de Reserva para gestión de bookings con estado.

    Este modelo proporciona una abstracción más clara para operaciones de
    reserva, separando la responsabilidad de una orden. Puede coexistir
    con Order o reemplazarlo en futuras versiones.

    Relacionado con: Order (compatibilidad) y Event/TicketType
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Usuario"),
        related_name='bookings'
    )
    event = models.ForeignKey(
        Evento,
        on_delete=models.PROTECT,
        verbose_name=_("Evento"),
        related_name='bookings'
    )
    booking_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de reserva")
    )
    status = models.CharField(
        max_length=20,
        choices=BOOKING_STATUS_CHOICES,
        default='pending',
        verbose_name=_("Estado de la reserva")
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Monto total")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notas")
    )

    # Auditoría
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Última actualización")
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Fecha de cancelación")
    )

    class Meta:
        verbose_name = _("Reserva")
        verbose_name_plural = _("Reservas")
        ordering = ['-booking_date']
        indexes = [
            models.Index(fields=['user', '-booking_date']),
            models.Index(fields=['event', 'status']),
        ]

    def __str__(self):
        return f"Reserva #{self.id} - {self.user.nombre} - {self.event.nombre}"

    def can_be_cancelled(self) -> bool:
        """Verifica si la reserva puede ser cancelada."""
        return self.status in ['pending', 'confirmed']

    def cancel(self) -> bool:
        """Cancela la reserva si es posible."""
        if self.can_be_cancelled():
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.save()
            return True
        return False

    def get_items_count(self) -> int:
        """Retorna el número total de items en la reserva."""
        return sum(item.quantity for item in self.items.all())


class BookingItem(models.Model):
    """
    Modelo para items dentro de una Reserva.

    Proporciona granularidad a nivel de tipo de boleto dentro de una reserva.
    """

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        verbose_name=_("Reserva"),
        related_name='items'
    )
    ticket_type = models.ForeignKey(
        TicketType,
        on_delete=models.PROTECT,
        verbose_name=_("Tipo de boleto")
    )
    quantity = models.PositiveIntegerField(
        verbose_name=_("Cantidad"),
        help_text=_("Número de boletos de este tipo")
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Precio unitario")
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Subtotal")
    )

    class Meta:
        verbose_name = _("Item de reserva")
        verbose_name_plural = _("Items de reserva")

    def __str__(self):
        return f"{self.quantity}x {self.ticket_type.name}"

    def save(self, *args, **kwargs):
        """Calcula automáticamente el subtotal."""
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_("Orden"))
    event = models.ForeignKey(Evento, on_delete=models.PROTECT, verbose_name=_("Evento"))
    ticket_type = models.ForeignKey(TicketType, on_delete=models.PROTECT, verbose_name=_("Tipo de boleto"))
    name = models.CharField(max_length=120, verbose_name=_("Nombre"))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Precio unitario"))
    quantity = models.PositiveIntegerField(verbose_name=_("Cantidad"))
    line_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Total de línea"))

    class Meta:
        verbose_name = _("Item de orden")
        verbose_name_plural = _("Items de orden")

    def __str__(self):
        return f"{self.quantity} x {self.name}"


class Ticket(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='tickets', verbose_name=_("Orden"))
    ticket_type = models.ForeignKey(TicketType, on_delete=models.PROTECT, verbose_name=_("Tipo de boleto"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name=_("Usuario"))
    event = models.ForeignKey(Evento, on_delete=models.PROTECT, verbose_name=_("Evento"))
    unique_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name=_("Código único"))
    is_used = models.BooleanField(default=False, verbose_name=_("Usado"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de creación"))

    class Meta:
        verbose_name = _("Boleto")
        verbose_name_plural = _("Boletos")

    def __str__(self):
        return f'Ticket for {self.event.nombre} - {self.ticket_type.name}'


class TicketHold(models.Model):
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name='holds', verbose_name=_("Tipo de boleto"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Usuario"))
    session_key = models.CharField(max_length=64, db_index=True, verbose_name=_("Clave de sesión"))
    quantity = models.PositiveIntegerField(verbose_name=_("Cantidad"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de creación"))
    expires_at = models.DateTimeField(db_index=True, verbose_name=_("Fecha de expiración"))

    class Meta:
        verbose_name = _("Reserva temporal")
        verbose_name_plural = _("Reservas temporales")
        indexes = [
            models.Index(fields=["ticket_type", "expires_at"]),
            models.Index(fields=["session_key", "expires_at"]),
        ]

    def is_active(self) -> bool:
        return self.expires_at > timezone.now()