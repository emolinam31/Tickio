from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from events.models import Evento, TicketType
import uuid


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Usuario"))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_("Fecha de creación"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de actualización"))
    status = models.CharField(max_length=20, default='created', verbose_name=_("Estado"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Monto total"))

    class Meta:
        verbose_name = _("Orden")
        verbose_name_plural = _("Órdenes")

    def __str__(self):
        return f"Order #{self.id}"


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