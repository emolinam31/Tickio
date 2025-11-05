from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse
from .forms import CustomUserCreationForm, CustomUserChangeForm
from orders.models import Order

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = [{'name': 'Iniciar Sesión'}]
        return context

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Registro exitoso!')
            return redirect('events:home')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = CustomUserCreationForm()
    breadcrumbs = [{'name': 'Registrarse'}]
    return render(request, 'accounts/register.html', {'form': form, 'breadcrumbs': breadcrumbs})

@login_required
def profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado!')
            return redirect('accounts:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    breadcrumbs = [{'name': 'Mi Perfil'}]
    return render(request, 'accounts/profile.html', {'form': form, 'breadcrumbs': breadcrumbs})

def logout_view(request):
    logout(request)
    messages.info(request, '¡Has cerrado sesión!')
    return redirect('events:home')

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('tickets').order_by('-created_at')
    context = {
        'orders': orders,
        'breadcrumbs': [{'name': 'Mis Órdenes'}]
    }
    return render(request, 'orders/my_orders.html', context)
