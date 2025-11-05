from django.db import models
from django.utils.translation import gettext_lazy as _

class CategoriaEvento(models.Model):
    nombre = models.CharField(max_length=100, verbose_name=_("Nombre"))
    descripcion = models.TextField(verbose_name=_("Descripción"))

    class Meta:
        verbose_name = _("Categoría de Evento")
        verbose_name_plural = _("Categorías de Eventos")

    def __str__(self):
        return self.nombre

class Evento(models.Model):
    ESTADO_CHOICES = [
        ('borrador', _('Borrador')),
        ('publicado', _('Publicado')),
        ('pausado', _('Pausado')),
    ]
    
    nombre = models.CharField(max_length=200, verbose_name=_("Nombre"))
    descripcion = models.TextField(blank=True, verbose_name=_("Descripción"))
    categoria = models.ForeignKey(
        CategoriaEvento, 
        on_delete=models.PROTECT,
        related_name='eventos',
        verbose_name=_("Categoría")
    )
    fecha = models.DateField(verbose_name=_("Fecha"))
    lugar = models.CharField(max_length=200, verbose_name=_("Lugar"))
    organizador = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='eventos_organizados',
        limit_choices_to={'tipo': 'organizador'},
        null=True,  # Permitir valores nulos temporalmente para el script de población
        blank=True,
        verbose_name=_("Organizador")
    )
    cupos_disponibles = models.PositiveIntegerField(verbose_name=_("Cupos disponibles"))
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Precio"))
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='borrador',
        verbose_name=_("Estado")
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de creación"))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de actualización"))

    class Meta:
        verbose_name = _("Evento")
        verbose_name_plural = _("Eventos")
        ordering = ['-fecha', 'nombre']

    def __str__(self):
        return f"{self.nombre} - {self.fecha}"

    def esta_agotado(self):
        return self.cupos_disponibles <= 0

    @property
    def has_ticket_types(self):
        return self.ticket_types.exists()

    def total_available(self):
        if not self.has_ticket_types:
            return self.cupos_disponibles
        return sum(tt.available for tt in self.ticket_types.filter(active=True))

    def min_ticket_price(self):
        if not self.has_ticket_types:
            return self.precio
        prices = list(self.ticket_types.filter(active=True).values_list('price', flat=True))
        return min(prices) if prices else self.precio

    def get_available_ticket_types(self):
        if not self.has_ticket_types:
            return []
        return self.ticket_types.filter(active=True, capacity__gt=models.F('sold')).order_by('price')

    def get_ticket_by_name(self, name: str):
        if not self.has_ticket_types:
            return None
        return (
            self.ticket_types.filter(name__iexact=name, active=True)
            .order_by('price')
            .first()
        )

    def general_ticket(self):
        return self.get_ticket_by_name('General')

    def vip_ticket(self):
        return self.get_ticket_by_name('VIP')


class TicketType(models.Model):
    event = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='ticket_types',
        verbose_name=_("Evento")
    )
    name = models.CharField(max_length=100, verbose_name=_("Nombre"))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Precio"))
    capacity = models.PositiveIntegerField(verbose_name=_("Capacidad"))
    sold = models.PositiveIntegerField(default=0, verbose_name=_("Vendidos"))
    active = models.BooleanField(default=True, verbose_name=_("Activo"))

    class Meta:
        verbose_name = _('Tipo de Boleto')
        verbose_name_plural = _('Tipos de Boleto')
        constraints = [
            models.CheckConstraint(check=models.Q(sold__gte=0), name='tickettype_sold_gte_0'),
            models.CheckConstraint(check=models.Q(capacity__gte=0), name='tickettype_capacity_gte_0'),
            models.CheckConstraint(check=models.Q(price__gte=0), name='tickettype_price_gte_0'),
        ]

    def __str__(self):
        return f"{self.name} ({self.event.nombre})"

    @property
    def available(self):
        return max(self.capacity - self.sold, 0)