from decimal import Decimal
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages
from events.models import TicketType
from .services import checkout as checkout_service
from .models import Ticket, TicketHold
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.utils.translation import gettext as _
import qrcode
import io
import base64

CART_SESSION_KEY = 'cart'
HOLD_MINUTES = 10

def _get_cart(session):
    cart = session.get(CART_SESSION_KEY)
    if cart is None:
        cart = {}
        session[CART_SESSION_KEY] = cart
    return cart


def _ensure_session_key(request: HttpRequest) -> str:
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _held_quantities(ticket_type: TicketType, session_key: str) -> tuple[int, int]:
    now = timezone.now()
    qs = TicketHold.objects.filter(ticket_type=ticket_type, expires_at__gt=now)
    total = qs.aggregate(total=models.Sum('quantity'))['total'] or 0
    mine = qs.filter(session_key=session_key).aggregate(total=models.Sum('quantity'))['total'] or 0
    return total, mine


def _effective_available(ticket_type: TicketType, session_key: str) -> int:
    total_holds, my_hold = _held_quantities(ticket_type, session_key)
    base_available = max(ticket_type.capacity - ticket_type.sold, 0)
    return max(base_available - (total_holds - my_hold), 0)


@require_POST
def add_to_cart(request: HttpRequest) -> HttpResponse:
    ticket_type_id = request.POST.get('ticket_type_id')
    quantity_raw = request.POST.get('quantity', '1')
    try:
        quantity = max(int(quantity_raw), 1)
    except (TypeError, ValueError):
        quantity = 1

    ticket_type = get_object_or_404(TicketType, pk=ticket_type_id, active=True)
    session_key = _ensure_session_key(request)
    effective_avail = _effective_available(ticket_type, session_key)

    if effective_avail <= 0:
        return _redirect_with_message(request, 'orders:cart_view', False, _(f"{ticket_type.name} está agotado"))

    cart = _get_cart(request.session)
    item = cart.get(str(ticket_type.id))

    if item:
        new_qty = item['quantity'] + quantity
        cap = effective_avail + int(item['quantity'])
        if new_qty > cap:
            new_qty = cap
        item['quantity'] = new_qty
    else:
        cart[str(ticket_type.id)] = {
            'ticket_type_id': ticket_type.id,
            'event_id': ticket_type.event_id,
            'name': ticket_type.name,
            'price': str(ticket_type.price),
            'quantity': min(quantity, effective_avail),
        }

    # Crear/actualizar hold para esta sesión
    hold_qty = int(cart[str(ticket_type.id)]['quantity'])
    expires_at = timezone.now() + timedelta(minutes=HOLD_MINUTES)
    TicketHold.objects.update_or_create(
        ticket_type=ticket_type,
        session_key=session_key,
        defaults={
            'user': request.user if request.user.is_authenticated else None,
            'quantity': hold_qty,
            'expires_at': expires_at,
        }
    )

    request.session.modified = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'cart_count': _cart_total_quantity(cart)})
    return redirect('orders:cart_view')


@require_POST
def remove_from_cart(request: HttpRequest) -> HttpResponse:
    ticket_type_id = request.POST.get('ticket_type_id')
    cart = _get_cart(request.session)
    if ticket_type_id and str(ticket_type_id) in cart:
        del cart[str(ticket_type_id)]
        # Liberar hold de esta sesión
        session_key = _ensure_session_key(request)
        TicketHold.objects.filter(ticket_type_id=ticket_type_id, session_key=session_key).delete()
        request.session.modified = True
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'cart_count': _cart_total_quantity(cart)})
    return redirect('orders:cart_view')


def cart_view(request: HttpRequest) -> HttpResponse:
    cart = _get_cart(request.session)
    items = []
    total = Decimal('0.00')
    for key, data in cart.items():
        price = Decimal(data['price'])
        quantity = int(data['quantity'])
        line_total = price * quantity
        total += line_total
        items.append({
            **data,
            'price': price,
            'line_total': line_total,
        })
    context = {
        'items': items,
        'total': total,
        'breadcrumbs': [{'name': 'Carrito de Compras'}]
    }
    return render(request, 'orders/cart.html', context)


def _cart_total_quantity(cart: dict) -> int:
    return sum(int(v.get('quantity', 0)) for v in cart.values())


@login_required
def checkout_view(request: HttpRequest) -> HttpResponse:
    cart = request.session.get(CART_SESSION_KEY, {})
    if not cart:
        messages.error(request, _("Tu carrito está vacío."))
        return redirect('orders:cart_view')

    if request.method == 'POST':
        try:
            order = checkout_service(cart, user=request.user)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('orders:checkout')

        # Limpiar carrito y mostrar mensaje
        request.session[CART_SESSION_KEY] = {}
        request.session.modified = True
        # Liberar holds de la sesión
        session_key = _ensure_session_key(request)
        TicketHold.objects.filter(session_key=session_key).delete()

        messages.success(request, _("¡Tu compra se ha realizado con éxito! Ya puedes ver tus tickets en 'Mis Órdenes'."))
        return redirect('accounts:my_orders')

    breadcrumbs = [
        {'name': 'Carrito de Compras', 'url': reverse('orders:cart_view')},
        {'name': 'Checkout'}
    ]
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'breadcrumbs': breadcrumbs
    })


@require_POST
def update_quantity(request: HttpRequest) -> HttpResponse:
    ticket_type_id = request.POST.get('ticket_type_id')
    delta_raw = request.POST.get('delta')
    if ticket_type_id is None or delta_raw not in {'+1', '-1'}:
        return redirect('orders:cart_view')

    cart = _get_cart(request.session)
    item = cart.get(str(ticket_type_id))
    if not item:
        return redirect('orders:cart_view')

    tt = get_object_or_404(TicketType, pk=ticket_type_id, active=True)
    session_key = _ensure_session_key(request)
    current_qty = int(item['quantity'])
    delta = 1 if delta_raw == '+1' else -1
    new_qty = current_qty + delta
    if new_qty < 1:
        del cart[str(ticket_type_id)]
        TicketHold.objects.filter(ticket_type=tt, session_key=session_key).delete()
    else:
        eff = _effective_available(tt, session_key)
        cap = eff + current_qty
        if new_qty > cap:
            new_qty = cap
        item['quantity'] = new_qty
        # Actualizar hold
        expires_at = timezone.now() + timedelta(minutes=HOLD_MINUTES)
        TicketHold.objects.update_or_create(
            ticket_type=tt,
            session_key=session_key,
            defaults={
                'user': request.user if request.user.is_authenticated else None,
                'quantity': int(new_qty),
                'expires_at': expires_at,
            }
        )

    request.session.modified = True
    return redirect('orders:cart_view')


def _redirect_with_message(request: HttpRequest, to: str, success: bool, message: str) -> HttpResponse:
    (messages.success if success else messages.error)(request, message)
    return redirect(to)


@login_required
def ticket_detail_view(request, ticket_code):
    ticket = get_object_or_404(Ticket, unique_code=ticket_code, user=request.user)

    # Generate QR Code
    qr_data = request.build_absolute_uri(request.path) # Example data, can be a validation URL
    qr_img = qrcode.make(qr_data)

    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    context = {
        'ticket': ticket,
        'qr_code': qr_base64,
        'breadcrumbs': [
            {'name': 'Mis Órdenes', 'url': reverse('accounts:my_orders')},
            {'name': f'Ticket {ticket.unique_code[:8]}...'}
        ]
    }
    return render(request, 'orders/ticket_detail.html', context)


