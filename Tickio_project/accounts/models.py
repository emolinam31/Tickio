from django.contrib.auth.models import AbstractUser
from django.db import models

class Asistente(models.Model):
    historial_compras = models.JSONField(default=dict, blank=True)
    preferencias = models.JSONField(default=dict, blank=True)
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='perfil_asistente')

    def __str__(self):
        return f"Asistente: {self.user.email}"

    class Meta:
        verbose_name = 'Asistente'
        verbose_name_plural = 'Asistentes'

class Organizador(models.Model):
    empresa = models.CharField(max_length=200)
    eventos_publicados = models.ManyToManyField('events.Evento', related_name='organizadores', blank=True)
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='perfil_organizador')

    def __str__(self):
        return f"Organizador: {self.empresa} - {self.user.email}"

    class Meta:
        verbose_name = 'Organizador'
        verbose_name_plural = 'Organizadores'

class CustomUser(AbstractUser):
    TIPO_CHOICES = (
        ('asistente', 'Asistente'),
        ('organizador', 'Organizador'),
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='asistente'
    )
    nombre = models.CharField(max_length=200)
    email = models.EmailField('correo electrónico', unique=True)

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
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
