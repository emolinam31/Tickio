"""
Servicio de Geocoding para convertir direcciones a coordenadas.

Utiliza la API de Google Maps Geocoding para obtener la latitud y longitud
de una dirección de evento. Este servicio es cacheable en la API para
optimizar las llamadas.

Autor: Sistema de Arquitectura - TICKIO
"""

import requests
from typing import Optional, Dict, Tuple
import os
from functools import lru_cache


class GeocodingService:
    """
    Servicio para obtener coordenadas (latitud, longitud) a partir de direcciones.

    Utiliza OpenStreetMap Nominatim (API gratuita, sin clave requerida)
    como servicio de geocoding.
    """

    # URL base de Nominatim
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

    @staticmethod
    @lru_cache(maxsize=128)
    def get_coordinates(lugar: str, ciudad: str = "Medellín", pais: str = "Colombia") -> Optional[Tuple[float, float]]:
        """
        Obtiene las coordenadas (latitud, longitud) de una dirección.

        Args:
            lugar: Nombre del lugar/recinto/estadio
            ciudad: Ciudad del evento (por defecto: Medellín)
            pais: País del evento (por defecto: Colombia)

        Returns:
            Tuple[float, float]: Tupla (latitud, longitud) o None si no se encuentra

        Ejemplo:
            >>> coords = GeocodingService.get_coordinates("Estadio Atanasio Girardot")
            >>> print(coords)
            (6.2442, -75.5898)
        """
        try:
            # Construir la dirección completa
            direccion_completa = f"{lugar}, {ciudad}, {pais}"

            # Parámetros para la API
            params = {
                'q': direccion_completa,
                'format': 'json',
                'limit': 1
            }

            # Headers para Nominatim (es recomendado identificarse)
            headers = {
                'User-Agent': 'TICKIO-EventApp/1.0'
            }

            # Hacer la solicitud
            response = requests.get(
                GeocodingService.NOMINATIM_URL,
                params=params,
                headers=headers,
                timeout=5
            )

            response.raise_for_status()

            # Procesar respuesta
            resultados = response.json()

            if resultados and len(resultados) > 0:
                resultado = resultados[0]
                latitud = float(resultado['lat'])
                longitud = float(resultado['lon'])
                return (latitud, longitud)

            return None

        except requests.exceptions.RequestException as e:
            print(f"Error al obtener coordenadas para '{lugar}': {str(e)}")
            return None
        except (KeyError, ValueError, IndexError) as e:
            print(f"Error al procesar respuesta de geocoding para '{lugar}': {str(e)}")
            return None

    @staticmethod
    def get_coordinates_with_fallback(lugar: str, ciudad: str = "Medellín") -> Dict[str, Optional[float]]:
        """
        Obtiene coordenadas con valores por defecto si falla.

        Args:
            lugar: Nombre del lugar
            ciudad: Ciudad del evento

        Returns:
            Dict con latitud y longitud (None si no se encuentra)
        """
        coords = GeocodingService.get_coordinates(lugar, ciudad)

        if coords:
            return {
                'latitud': coords[0],
                'longitud': coords[1]
            }

        return {
            'latitud': None,
            'longitud': None
        }


# Coordenadas por defecto para ciudades principales de Colombia
CIUDADES_COLOMBIA = {
    'medellín': (6.2442, -75.5898),
    'bogota': (4.7110, -74.0721),
    'cali': (3.4372, -76.5197),
    'barranquilla': (10.9639, -74.7964),
    'cartagena': (10.3910, -75.4794),
    'bucaramanga': (7.1269, -73.1122),
    'santa marta': (11.2402, -74.2197),
}


class GeocodingServiceWithCache:
    """
    Servicio de Geocoding con caché local para dirección fallidas o no encontradas.
    Primero intenta con OpenStreetMap Nominatim, luego usa coordenadas por defecto.
    """

    @staticmethod
    def get_coordinates_cached(lugar: str, ciudad: str = "Medellín") -> Dict[str, Optional[float]]:
        """
        Obtiene coordenadas usando caché como fallback.

        Args:
            lugar: Nombre del lugar
            ciudad: Ciudad del evento

        Returns:
            Dict con latitud y longitud
        """
        # Intentar obtener desde la API
        coords = GeocodingService.get_coordinates(lugar, ciudad)

        if coords:
            return {
                'latitud': coords[0],
                'longitud': coords[1]
            }

        # Si falla, usar coordenadas por defecto de la ciudad
        ciudad_lower = ciudad.lower()
        if ciudad_lower in CIUDADES_COLOMBIA:
            lat, lon = CIUDADES_COLOMBIA[ciudad_lower]
            return {
                'latitud': lat,
                'longitud': lon
            }

        # Si todo falla, retornar None
        return {
            'latitud': None,
            'longitud': None
        }
