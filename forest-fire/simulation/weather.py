"""
Módulo para la integración con la API Open-Meteo.

Consulta el tiempo actual para una ciudad dada y calcula parámetros
p y f sugeridos para la simulación de incendios.

La llamada a Open-Meteo se realiza SIEMPRE desde el servidor (no desde JS).
"""

import requests


# URL base de geocodificación y meteorología de Open-Meteo
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# Valores por defecto de p y f
DEFAULT_P = 0.05
DEFAULT_F = 0.001


def get_coordinates(city: str) -> tuple[float, float]:
    """
    Obtiene las coordenadas (latitud, longitud) de una ciudad usando Open-Meteo Geocoding.
    """
    response = requests.get(
        GEOCODING_URL,
        params={"name": city, "count": 1, "language": "es", "format": "json"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    results = data.get("results")
    if not results:
        raise ValueError(f"Ciudad '{city}' no encontrada en Open-Meteo Geocoding.")

    return results[0]["latitude"], results[0]["longitude"]


def get_current_weather(lat: float, lon: float) -> dict:
    """
    Obtiene variables meteorológicas actuales para unas coordenadas.

    Variables solicitadas -> 
        - temperature_2m: temperatura a 2m (°C)
        - relative_humidity_2m: humedad relativa (%)
        - wind_speed_10m: velocidad del viento a 10m (km/h)

    """
    response = requests.get(
        WEATHER_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "wind_speed_unit": "kmh",
            "timezone": "auto",
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    current = data["current"]

    return {
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
    }


def suggest_parameters(weather: dict) -> dict:
    """
    Calcula p y f sugeridos a partir de las condiciones meteorológicas.

    Lógica -> 
        - Viento > 30 km/h    → reduce p (los árboles caen).
        - Humedad > 70%       → aumenta p (los árboles crecen más) y f (tormentas).
        - Temperatura > 35°C  → aumenta f (más tormentas eléctricas).
    """
    p = DEFAULT_P
    f = DEFAULT_F
    reasons = []

    temp = weather["temperature"]
    humidity = weather["humidity"]
    wind = weather["wind_speed"]

    # Viento fuerte → los árboles no crecen bien
    if wind > 30:
        p = max(0.001, p * 0.5)
        reasons.append(f"Viento fuerte ({wind:.1f} km/h) → p reducida a {p:.4f}")

    # Humedad alta → más crecimiento y más tormentas eléctricas
    if humidity > 70:
        p = min(0.2, p * 1.5)
        f = min(0.01, f * 2.0)
        reasons.append(
            f"Humedad alta ({humidity:.0f}%) → p={p:.4f}, f={f:.5f}"
        )

    # Temperatura muy alta → más rayos
    if temp > 35:
        f = min(0.01, f * 3.0)
        reasons.append(f"Temperatura alta ({temp:.1f}°C) → f aumentada a {f:.5f}")

    return {
        "p": round(p, 6),
        "f": round(f, 6),
        "reasoning": "; ".join(reasons) if reasons else "Condiciones normales, valores por defecto.",
        "weather": weather,
    }


def get_suggested_params(city: str) -> dict:
    """
    Dado el nombre de una ciudad, devuelve p y f sugeridos.
    Combina geocodificación, consulta meteorológica y cálculo de parámetros.

        ValueError: Si la ciudad no existe.
        requests.RequestException: Si alguna petición HTTP falla.
    """
    lat, lon = get_coordinates(city)
    weather = get_current_weather(lat, lon)
    return suggest_parameters(weather)