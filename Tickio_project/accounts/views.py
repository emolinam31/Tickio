from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm, CustomUserChangeForm
from orders.models import Order
from django.utils.translation import gettext as _


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('¡Registro exitoso!'))
            return redirect('events:home')
        else:
            messages.error(request, _('Por favor corrija los errores en el formulario.'))
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Perfil actualizado!'))
            return redirect('accounts:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, '¡Has cerrado sesión!')
    return redirect('events:home')

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('tickets').order_by('-created_at')
    context = {
        'orders': orders
    }
    return render(request, 'orders/my_orders.html', context)
