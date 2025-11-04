"""
Tests para el servicio de Geocoding.

Pruebas unitarias para verificar que el servicio de Geocoding
funciona correctamente con OpenStreetMap Nominatim.

Autor: Sistema de Arquitectura - TICKIO
"""

import unittest
from unittest.mock import patch, MagicMock
from events.geocoding_service import (
    GeocodingService,
    GeocodingServiceWithCache,
    CIUDADES_COLOMBIA
)


class TestGeocodingService(unittest.TestCase):
    """Tests para GeocodingService"""

    @patch('events.geocoding_service.requests.get')
    def test_get_coordinates_success(self, mock_get):
        """Test que obtiene coordenadas exitosamente"""
        # Mock de respuesta exitosa
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                'lat': '6.2442',
                'lon': '-75.5898'
            }
        ]
        mock_get.return_value = mock_response

        coords = GeocodingService.get_coordinates(
            "Estadio Atanasio Girardot",
            "Medellín"
        )

        self.assertIsNotNone(coords)
        self.assertEqual(coords[0], 6.2442)
        self.assertEqual(coords[1], -75.5898)

    @patch('events.geocoding_service.requests.get')
    def test_get_coordinates_not_found(self, mock_get):
        """Test cuando no se encuentra la ubicación"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        coords = GeocodingService.get_coordinates("LugarInexistente")

        self.assertIsNone(coords)

    @patch('events.geocoding_service.requests.get')
    def test_get_coordinates_network_error(self, mock_get):
        """Test cuando hay error de red"""
        mock_get.side_effect = Exception("Network error")

        coords = GeocodingService.get_coordinates("Algún lugar")

        self.assertIsNone(coords)

    def test_cache_functionality(self):
        """Test que el caché funciona"""
        with patch('events.geocoding_service.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {'lat': '6.2442', 'lon': '-75.5898'}
            ]
            mock_get.return_value = mock_response

            # Primera llamada
            coords1 = GeocodingService.get_coordinates("Estadio Girardot")

            # Segunda llamada (debe venir del caché)
            coords2 = GeocodingService.get_coordinates("Estadio Girardot")

            # Verificar que get fue llamado una sola vez
            self.assertEqual(mock_get.call_count, 1)
            self.assertEqual(coords1, coords2)


class TestGeocodingServiceWithCache(unittest.TestCase):
    """Tests para GeocodingServiceWithCache"""

    @patch('events.geocoding_service.requests.get')
    def test_get_coordinates_cached_success(self, mock_get):
        """Test obtener coordenadas con caché exitoso"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {'lat': '6.2442', 'lon': '-75.5898'}
        ]
        mock_get.return_value = mock_response

        result = GeocodingServiceWithCache.get_coordinates_cached(
            "Estadio Atanasio Girardot",
            "Medellín"
        )

        self.assertEqual(result['latitud'], 6.2442)
        self.assertEqual(result['longitud'], -75.5898)

    @patch('events.geocoding_service.requests.get')
    def test_get_coordinates_cached_fallback_city(self, mock_get):
        """Test fallback a coordenadas de ciudad"""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = GeocodingServiceWithCache.get_coordinates_cached(
            "LugarNoEncontrado",
            "Medellín"
        )

        # Debe retornar coordenadas por defecto de Medellín
        self.assertEqual(result['latitud'], CIUDADES_COLOMBIA['medellín'][0])
        self.assertEqual(result['longitud'], CIUDADES_COLOMBIA['medellín'][1])

    def test_ciudades_conocidas(self):
        """Test que las ciudades conocidas tienen coordenadas"""
        for ciudad, (lat, lon) in CIUDADES_COLOMBIA.items():
            self.assertIsInstance(lat, (int, float))
            self.assertIsInstance(lon, (int, float))
            self.assertGreater(lat, -90)
            self.assertLess(lat, 90)
            self.assertGreater(lon, -180)
            self.assertLess(lon, 180)

    @patch('events.geocoding_service.requests.get')
    def test_get_coordinates_cached_network_error(self, mock_get):
        """Test que fallback funciona con error de red"""
        mock_get.side_effect = Exception("Network error")

        result = GeocodingServiceWithCache.get_coordinates_cached(
            "Cualquier lugar",
            "Bogota"
        )

        # Debe retornar coordenadas por defecto de Bogotá
        self.assertEqual(result['latitud'], CIUDADES_COLOMBIA['bogota'][0])
        self.assertEqual(result['longitud'], CIUDADES_COLOMBIA['bogota'][1])


class TestCiudadesColombia(unittest.TestCase):
    """Tests para verificar las coordenadas de ciudades"""

    def test_medellin_coordinates(self):
        """Test coordenadas de Medellín"""
        self.assertAlmostEqual(
            CIUDADES_COLOMBIA['medellín'][0],
            6.2442,
            places=4
        )

    def test_bogota_coordinates(self):
        """Test coordenadas de Bogotá"""
        self.assertAlmostEqual(
            CIUDADES_COLOMBIA['bogota'][0],
            4.7110,
            places=4
        )

    def test_all_cities_have_valid_coordinates(self):
        """Test que todas las ciudades tienen coordenadas válidas"""
        for ciudad, (lat, lon) in CIUDADES_COLOMBIA.items():
            # Latitud debe estar entre -90 y 90
            self.assertGreaterEqual(lat, -90, f"Latitud inválida para {ciudad}")
            self.assertLessEqual(lat, 90, f"Latitud inválida para {ciudad}")

            # Longitud debe estar entre -180 y 180
            self.assertGreaterEqual(lon, -180, f"Longitud inválida para {ciudad}")
            self.assertLessEqual(lon, 180, f"Longitud inválida para {ciudad}")


if __name__ == '__main__':
    unittest.main()
