#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para limpiar y normalizar los precios de los eventos.
Ejecutar: python manage.py shell < cleanup_prices.py
O: python cleanup_prices.py
"""

import os
import sys
import django
from decimal import Decimal

# Configurar output encoding
sys.stdout.reconfigure(encoding='utf-8')

# Configurar Django si se ejecuta directamente
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tickio.settings')
    django.setup()

from events.models import Evento, TicketType

def cleanup_evento_prices():
    """Limpiar precios de eventos que estén fuera de rango válido"""
    eventos = Evento.objects.all()
    updated = 0

    for evento in eventos:
        # Validar que el precio esté en rango razonable (0 - 999,999.99)
        if evento.precio < 0 or evento.precio > Decimal('999999.99'):
            print(f"⚠️  Evento {evento.id} ({evento.nombre}) - Precio inválido: {evento.precio}")
            # Asignar precio por defecto
            evento.precio = Decimal('50.00')
            evento.save()
            updated += 1
        # Validar que tenga máximo 2 decimales
        elif evento.precio.as_tuple().exponent < -2:
            print(f"⚠️  Evento {evento.id} ({evento.nombre}) - Demasiados decimales: {evento.precio}")
            evento.precio = evento.precio.quantize(Decimal('0.01'))
            evento.save()
            updated += 1

    print(f"\n✅ Eventos actualizados: {updated}")
    return updated

def cleanup_ticket_prices():
    """Limpiar precios de tipos de boletos"""
    tickets = TicketType.objects.all()
    updated = 0

    for ticket in tickets:
        # Validar que el precio esté en rango razonable
        if ticket.price < 0 or ticket.price > Decimal('999999.99'):
            print(f"⚠️  TicketType {ticket.id} ({ticket.name}) - Precio inválido: {ticket.price}")
            ticket.price = Decimal('25.00')
            ticket.save()
            updated += 1
        # Validar que tenga máximo 2 decimales
        elif ticket.price.as_tuple().exponent < -2:
            print(f"⚠️  TicketType {ticket.id} ({ticket.name}) - Demasiados decimales: {ticket.price}")
            ticket.price = ticket.price.quantize(Decimal('0.01'))
            ticket.save()
            updated += 1

    print(f"✅ TicketTypes actualizados: {updated}")
    return updated

def print_evento_summary():
    """Mostrar resumen de eventos y precios"""
    eventos = Evento.objects.all()
    print("\n📊 RESUMEN DE EVENTOS:")
    print(f"Total eventos: {eventos.count()}")

    min_price = eventos.aggregate(Min=django.db.models.Min('precio'))['Min']
    max_price = eventos.aggregate(Max=django.db.models.Max('precio'))['Max']

    print(f"Precio mínimo: {min_price}")
    print(f"Precio máximo: {max_price}")

    # Mostrar primeros 10
    print("\n🎟️  Primeros 10 eventos:")
    for evento in eventos[:10]:
        print(f"  {evento.id:3d} | {evento.nombre:30s} | ${evento.precio:10.2f}")

if __name__ == '__main__':
    print("🧹 Iniciando limpieza de precios...\n")

    print("📌 Limpiando precios de eventos...")
    cleanup_evento_prices()

    print("\n📌 Limpiando precios de tipos de boletos...")
    cleanup_ticket_prices()

    print_evento_summary()
    print("\n✨ Limpieza completada!")
