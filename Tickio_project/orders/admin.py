from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Order, OrderItem, Ticket, TicketHold

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'user__username')
    date_hierarchy = 'created_at'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'event', 'ticket_type', 'quantity', 'line_total')
    list_filter = ('order', 'event')
    search_fields = ('order__id', 'event__nombre', 'name')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('unique_code', 'user', 'event', 'ticket_type', 'is_used', 'created_at')
    list_filter = ('is_used', 'created_at', 'event')
    search_fields = ('unique_code', 'user__email', 'event__nombre')
    date_hierarchy = 'created_at'

@admin.register(TicketHold)
class TicketHoldAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket_type', 'user', 'quantity', 'expires_at', 'created_at')
    list_filter = ('expires_at', 'created_at')
    search_fields = ('ticket_type__name', 'user__email', 'session_key')
    date_hierarchy = 'created_at'
