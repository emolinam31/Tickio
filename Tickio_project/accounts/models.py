from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class Asistente(models.Model):
    historial_compras = models.JSONField(default=dict, blank=True, verbose_name=_("Historial de compras"))
    preferencias = models.JSONField(default=dict, blank=True, verbose_name=_("Preferencias"))
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='perfil_asistente', verbose_name=_("Usuario"))

    def __str__(self):
        return f"Asistente: {self.user.email}"

    class Meta:
        verbose_name = _('Asistente')
        verbose_name_plural = _('Asistentes')

class Organizador(models.Model):
    empresa = models.CharField(max_length=200, verbose_name=_("Empresa"))
    eventos_publicados = models.ManyToManyField('events.Evento', related_name='organizadores', blank=True, verbose_name=_("Eventos publicados"))
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='perfil_organizador', verbose_name=_("Usuario"))

    def __str__(self):
        return f"Organizador: {self.empresa} - {self.user.email}"

    class Meta:
        verbose_name = _('Organizador')
        verbose_name_plural = _('Organizadores')

class CustomUser(AbstractUser):
    TIPO_CHOICES = (
        ('asistente', _('Asistente')),
        ('organizador', _('Organizador')),
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='asistente',
        verbose_name=_("Tipo")
    )
    nombre = models.CharField(max_length=200, verbose_name=_("Nombre"))
    email = models.EmailField(_('correo electrónico'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'nombre']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            if self.tipo == 'asistente' and not hasattr(self, 'perfil_asistente'):
                Asistente.objects.create(user=self)
            elif self.tipo == 'organizador' and not hasattr(self, 'perfil_organizador'):
                Organizador.objects.create(user=self, empresa='')

    def get_profile(self):
        if self.tipo == 'asistente':
            return self.perfil_asistente
        return self.perfil_organizador

    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')
