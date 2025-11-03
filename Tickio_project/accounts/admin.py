from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Asistente, Organizador

class AsistenteInline(admin.StackedInline):
    model = Asistente
    can_delete = False

class OrganizadorInline(admin.StackedInline):
    model = Organizador
    can_delete = False

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'tipo', 'is_staff', 'is_active')
    list_filter = ('tipo', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Información Personal'), {'fields': ('nombre', 'first_name', 'last_name')}),
        (_('Permisos'), {'fields': ('tipo', 'is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'nombre', 'password1', 'password2', 'tipo', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'username', 'nombre')
    ordering = ('email',)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        if obj.tipo == 'asistente':
            return [AsistenteInline(self.model, self.admin_site)]
        return [OrganizadorInline(self.model, self.admin_site)]

class AsistenteAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombre')
    search_fields = ('user__email', 'user__nombre')

    def email(self, obj):
        return obj.user.email

    def nombre(self, obj):
        return obj.user.nombre

class OrganizadorAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'email', 'nombre')
    search_fields = ('empresa', 'user__email', 'user__nombre')

    def email(self, obj):
        return obj.user.email

    def nombre(self, obj):
        return obj.user.nombre

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Asistente, AsistenteAdmin)
admin.site.register(Organizador, OrganizadorAdmin)
