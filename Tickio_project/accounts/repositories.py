"""
Repositorio de datos para la aplicación de cuentas.

Proporciona acceso abstrato a los datos de usuarios, asistentes y organizadores
sin exponer la implementación directa del ORM de Django.

Autor: Sistema de Arquitectura - TICKIO
"""

from typing import List, Optional
from django.db.models import Q

from accounts.models import CustomUser, Asistente, Organizador


class UserRepository:
    """Repositorio para gestionar el acceso a datos de usuarios."""

    @staticmethod
    def find_by_id(user_id: int) -> Optional[CustomUser]:
        """
        Obtiene un usuario por su ID.

        Args:
            user_id: ID del usuario

        Returns:
            Optional[CustomUser]: Usuario encontrado o None
        """
        return CustomUser.objects.filter(id=user_id).first()

    @staticmethod
    def find_by_email(email: str) -> Optional[CustomUser]:
        """
        Obtiene un usuario por su email.

        Args:
            email: Email del usuario

        Returns:
            Optional[CustomUser]: Usuario encontrado o None
        """
        return CustomUser.objects.filter(email=email).first()

    @staticmethod
    def find_by_username(username: str) -> Optional[CustomUser]:
        """
        Obtiene un usuario por su nombre de usuario.

        Args:
            username: Nombre de usuario

        Returns:
            Optional[CustomUser]: Usuario encontrado o None
        """
        return CustomUser.objects.filter(username=username).first()

    @staticmethod
    def find_all_users() -> List[CustomUser]:
        """
        Obtiene todos los usuarios.

        Returns:
            List[CustomUser]: Lista de todos los usuarios
        """
        return CustomUser.objects.all().order_by('-date_joined')

    @staticmethod
    def find_organizers() -> List[CustomUser]:
        """
        Obtiene todos los usuarios que son organizadores.

        Returns:
            List[CustomUser]: Lista de organizadores
        """
        return CustomUser.objects.filter(tipo='organizador').order_by('nombre')

    @staticmethod
    def find_assistants() -> List[CustomUser]:
        """
        Obtiene todos los usuarios que son asistentes.

        Returns:
            List[CustomUser]: Lista de asistentes
        """
        return CustomUser.objects.filter(tipo='asistente').order_by('nombre')

    @staticmethod
    def find_active_users() -> List[CustomUser]:
        """
        Obtiene todos los usuarios activos.

        Returns:
            List[CustomUser]: Lista de usuarios activos
        """
        return CustomUser.objects.filter(is_active=True).order_by('nombre')

    @staticmethod
    def search_users(query: str) -> List[CustomUser]:
        """
        Busca usuarios por nombre, email o nombre de usuario.

        Args:
            query: Término de búsqueda

        Returns:
            List[CustomUser]: Lista de usuarios que coinciden
        """
        return CustomUser.objects.filter(
            Q(nombre__icontains=query) |
            Q(email__icontains=query) |
            Q(username__icontains=query)
        ).order_by('nombre')

    @staticmethod
    def email_exists(email: str) -> bool:
        """
        Verifica si un email ya está registrado.

        Args:
            email: Email a verificar

        Returns:
            bool: True si el email existe, False en caso contrario
        """
        return CustomUser.objects.filter(email=email).exists()

    @staticmethod
    def username_exists(username: str) -> bool:
        """
        Verifica si un nombre de usuario ya está registrado.

        Args:
            username: Nombre de usuario a verificar

        Returns:
            bool: True si el nombre existe, False en caso contrario
        """
        return CustomUser.objects.filter(username=username).exists()


class AsistenteRepository:
    """Repositorio para gestionar el acceso a datos de asistentes."""

    @staticmethod
    def find_by_user_id(user_id: int) -> Optional[Asistente]:
        """
        Obtiene el perfil de asistente por ID de usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Optional[Asistente]: Perfil de asistente o None
        """
        return Asistente.objects.filter(usuario_id=user_id).first()

    @staticmethod
    def find_all() -> List[Asistente]:
        """
        Obtiene todos los asistentes.

        Returns:
            List[Asistente]: Lista de todos los asistentes
        """
        return Asistente.objects.all().select_related('usuario').order_by('usuario__nombre')

    @staticmethod
    def find_with_purchase_history() -> List[Asistente]:
        """
        Obtiene asistentes que tienen historial de compras.

        Returns:
            List[Asistente]: Lista de asistentes con compras
        """
        return Asistente.objects.filter(
            historial_compras__isnull=False
        ).exclude(
            historial_compras={}
        ).select_related('usuario')

    @staticmethod
    def get_assistant_stats(user_id: int) -> dict:
        """
        Obtiene estadísticas de un asistente.

        Args:
            user_id: ID del usuario asistente

        Returns:
            dict: Diccionario con estadísticas del asistente
        """
        asistente = Asistente.objects.filter(usuario_id=user_id).first()
        if not asistente:
            return {}

        return {
            'user_id': user_id,
            'purchase_count': len(asistente.historial_compras) if asistente.historial_compras else 0,
            'preferences': asistente.preferencias or {},
        }


class OrganizadorRepository:
    """Repositorio para gestionar el acceso a datos de organizadores."""

    @staticmethod
    def find_by_user_id(user_id: int) -> Optional[Organizador]:
        """
        Obtiene el perfil de organizador por ID de usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Optional[Organizador]: Perfil de organizador o None
        """
        return Organizador.objects.filter(usuario_id=user_id).first()

    @staticmethod
    def find_all() -> List[Organizador]:
        """
        Obtiene todos los organizadores.

        Returns:
            List[Organizador]: Lista de todos los organizadores
        """
        return Organizador.objects.all().select_related('usuario').order_by('usuario__nombre')

    @staticmethod
    def find_by_company(company_name: str) -> List[Organizador]:
        """
        Obtiene organizadores por nombre de empresa.

        Args:
            company_name: Nombre de la empresa

        Returns:
            List[Organizador]: Lista de organizadores de la empresa
        """
        return Organizador.objects.filter(
            empresa__icontains=company_name
        ).select_related('usuario')

    @staticmethod
    def get_organizer_stats(user_id: int) -> dict:
        """
        Obtiene estadísticas de un organizador.

        Args:
            user_id: ID del usuario organizador

        Returns:
            dict: Diccionario con estadísticas del organizador
        """
        organizador = Organizador.objects.filter(usuario_id=user_id).first()
        if not organizador:
            return {}

        eventos = organizador.eventos_publicados.all()

        return {
            'user_id': user_id,
            'company': organizador.empresa,
            'events_count': eventos.count(),
            'published_events': eventos.filter(estado='publicado').count(),
            'draft_events': eventos.filter(estado='borrador').count(),
        }

    @staticmethod
    def find_with_published_events() -> List[Organizador]:
        """
        Obtiene organizadores que tienen eventos publicados.

        Returns:
            List[Organizador]: Lista de organizadores con eventos
        """
        return Organizador.objects.filter(
            eventos_publicados__estado='publicado'
        ).distinct().select_related('usuario')
