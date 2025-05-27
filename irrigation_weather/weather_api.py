#!/usr/bin/env python3
"""
Módulo de integração com API meteorológica OpenWeather.

Este módulo busca dados meteorológicos em tempo real para auxiliar
nas decisões de irrigação inteligente do sistema.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum


class WeatherCondition(Enum):
    """Condições climáticas relevantes para irrigação"""
    CLEAR = "clear"
    CLOUDS = "clouds"
    RAIN = "rain"
    DRIZZLE = "drizzle"
    THUNDERSTORM = "thunderstorm"
    SNOW = "snow"
    MIST = "mist"
    UNKNOWN = "unknown"


@dataclass
class WeatherData:
    """Estrutura de dados meteorológicos"""
    timestamp: datetime
    temperature: float  # Celsius
    humidity: float  # Porcentagem
    pressure: float  # hPa
    condition: WeatherCondition
    description: str
    wind_speed: float  # m/s
    rain_1h: float  # mm na última hora
    rain_3h: float  # mm nas últimas 3 horas
    clouds: int  # Porcentagem de cobertura


@dataclass
class WeatherForecast:
    """Previsão meteorológica"""
    timestamp: datetime
    temperature: float
    humidity: float
    condition: WeatherCondition
    rain_probability: float  # 0-1
    rain_volume: float  # mm


class WeatherAPI:
    """Cliente para API OpenWeather"""

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key: str, city: str = "São Paulo",
                 country_code: str = "BR", units: str = "metric"):
        """
        Inicializa cliente da API.

        Args:
            api_key: Chave de API da OpenWeather
            city: Nome da cidade
            country_code: Código do país (ISO 3166)
            units: Sistema de unidades (metric/imperial)
        """
        self.api_key = api_key
        self.city = city
        self.country_code = country_code
        self.units = units
        self.logger = logging.getLogger(__name__)

        # Cache para evitar requisições excessivas
        self._cache: Dict[str, Tuple[datetime, any]] = {}
        self._cache_duration = timedelta(minutes=10)

    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Realiza requisição HTTP com tratamento de erros"""
        try:
            params['appid'] = self.api_key
            params['units'] = self.units

            url = f"{self.BASE_URL}/{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na requisição à API: {e}")
            return None

    def _get_from_cache(self, key: str) -> Optional[any]:
        """Obtém dados do cache se ainda válidos"""
        if key in self._cache:
            timestamp, data = self._cache[key]
            if datetime.now() - timestamp < self._cache_duration:
                self.logger.debug(f"Usando cache para {key}")
                return data
        return None

    def _save_to_cache(self, key: str, data: any):
        """Salva dados no cache"""
        self._cache[key] = (datetime.now(), data)

    def _parse_condition(self, weather_data: Dict) -> WeatherCondition:
        """Converte condição da API para enum"""
        main = weather_data.get('main', '').lower()

        condition_map = {
            'clear': WeatherCondition.CLEAR,
            'clouds': WeatherCondition.CLOUDS,
            'rain': WeatherCondition.RAIN,
            'drizzle': WeatherCondition.DRIZZLE,
            'thunderstorm': WeatherCondition.THUNDERSTORM,
            'snow': WeatherCondition.SNOW,
            'mist': WeatherCondition.MIST,
            'fog': WeatherCondition.MIST,
            'haze': WeatherCondition.MIST,
        }

        return condition_map.get(main, WeatherCondition.UNKNOWN)

    def get_current_weather(self) -> Optional[WeatherData]:
        """Obtém dados meteorológicos atuais"""
        cache_key = f"current_{self.city}_{self.country_code}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        params = {
            'q': f"{self.city},{self.country_code}",
            'lang': 'pt_br'
        }

        data = self._make_request('weather', params)
        if not data:
            return None

        try:
            weather = WeatherData(
                timestamp=datetime.fromtimestamp(data['dt']),
                temperature=data['main']['temp'],
                humidity=data['main']['humidity'],
                pressure=data['main']['pressure'],
                condition=self._parse_condition(data['weather'][0]),
                description=data['weather'][0].get('description', ''),
                wind_speed=data['wind']['speed'],
                rain_1h=data.get('rain', {}).get('1h', 0.0),
                rain_3h=data.get('rain', {}).get('3h', 0.0),
                clouds=data.get('clouds', {}).get('all', 0)
            )

            self._save_to_cache(cache_key, weather)
            return weather

        except (KeyError, ValueError) as e:
            self.logger.error(f"Erro ao processar dados meteorológicos: {e}")
            return None

    def get_forecast(self, hours: int = 24) -> Optional[list[WeatherForecast]]:
        """
        Obtém previsão do tempo para as próximas horas.

        Args:
            hours: Número de horas de previsão (máx 120)

        Returns:
            Lista de previsões ou None em caso de erro
        """
        cache_key = f"forecast_{self.city}_{self.country_code}_{hours}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        params = {
            'q': f"{self.city},{self.country_code}",
            'cnt': min(hours // 3, 40),  # API retorna previsões de 3 em 3 horas
            'lang': 'pt_br'
        }

        data = self._make_request('forecast', params)
        if not data:
            return None

        try:
            forecasts = []
            for item in data['list']:
                forecast = WeatherForecast(
                    timestamp=datetime.fromtimestamp(item['dt']),
                    temperature=item['main']['temp'],
                    humidity=item['main']['humidity'],
                    condition=self._parse_condition(item['weather'][0]),
                    rain_probability=item.get('pop', 0),  # Probability of precipitation
                    rain_volume=item.get('rain', {}).get('3h', 0.0)
                )
                forecasts.append(forecast)

            self._save_to_cache(cache_key, forecasts)
            return forecasts

        except (KeyError, ValueError) as e:
            self.logger.error(f"Erro ao processar previsão: {e}")
            return None

    def will_rain_soon(self, hours: int = 6) -> Tuple[bool, float]:
        """
        Verifica se vai chover nas próximas horas.

        Args:
            hours: Janela de tempo para verificar

        Returns:
            Tupla (vai_chover, probabilidade_máxima)
        """
        forecasts = self.get_forecast(hours)
        if not forecasts:
            return False, 0.0

        max_probability = 0.0
        will_rain = False

        for forecast in forecasts:
            if forecast.rain_probability > max_probability:
                max_probability = forecast.rain_probability

            # Considera que vai chover se probabilidade > 50% ou volume > 1mm
            if forecast.rain_probability > 0.5 or forecast.rain_volume > 1.0:
                will_rain = True

        return will_rain, max_probability


class WeatherSimulator:
    """Simulador de dados meteorológicos para testes"""

    def __init__(self):
        """Inicializa simulador com padrões realistas"""
        self.logger = logging.getLogger(__name__)
        self._scenario = "normal"

    def set_scenario(self, scenario: str):
        """Define cenário de simulação: normal, rain, drought, storm"""
        self._scenario = scenario
        self.logger.info(f"Cenário de simulação alterado para: {scenario}")

    def get_current_weather(self) -> WeatherData:
        """Simula dados meteorológicos atuais baseado no cenário"""
        scenarios = {
            "normal": {
                "temperature": 25.0,
                "humidity": 65.0,
                "condition": WeatherCondition.CLOUDS,
                "rain_1h": 0.0,
                "rain_3h": 0.0,
                "clouds": 40
            },
            "rain": {
                "temperature": 22.0,
                "humidity": 85.0,
                "condition": WeatherCondition.RAIN,
                "rain_1h": 5.0,
                "rain_3h": 12.0,
                "clouds": 90
            },
            "drought": {
                "temperature": 32.0,
                "humidity": 30.0,
                "condition": WeatherCondition.CLEAR,
                "rain_1h": 0.0,
                "rain_3h": 0.0,
                "clouds": 10
            },
            "storm": {
                "temperature": 20.0,
                "humidity": 95.0,
                "condition": WeatherCondition.THUNDERSTORM,
                "rain_1h": 15.0,
                "rain_3h": 40.0,
                "clouds": 100
            }
        }

        data = scenarios.get(self._scenario, scenarios["normal"])

        return WeatherData(
            timestamp=datetime.now(),
            temperature=data["temperature"],
            humidity=data["humidity"],
            pressure=1013.0,
            condition=data["condition"],
            description=f"Simulação: {self._scenario}",
            wind_speed=5.0,
            rain_1h=data["rain_1h"],
            rain_3h=data["rain_3h"],
            clouds=data["clouds"]
        )

    def get_forecast(self, hours: int = 24) -> list[WeatherForecast]:
        """Simula previsão meteorológica"""
        forecasts = []

        # Gera previsões de 3 em 3 horas
        for i in range(0, hours, 3):
            timestamp = datetime.now() + timedelta(hours=i)

            if self._scenario == "rain":
                # Aumenta chance de chuva nas próximas horas
                rain_prob = min(0.8 + i * 0.01, 0.95)
                rain_vol = 5.0 + i * 0.5
                condition = WeatherCondition.RAIN
            elif self._scenario == "storm":
                rain_prob = 0.9
                rain_vol = 20.0
                condition = WeatherCondition.THUNDERSTORM
            else:
                rain_prob = 0.1
                rain_vol = 0.0
                condition = WeatherCondition.CLEAR

            forecast = WeatherForecast(
                timestamp=timestamp,
                temperature=25.0 - i * 0.1,
                humidity=70.0 + i * 0.5,
                condition=condition,
                rain_probability=rain_prob,
                rain_volume=rain_vol
            )
            forecasts.append(forecast)

        return forecasts

    def will_rain_soon(self, hours: int = 6) -> Tuple[bool, float]:
        """Simula verificação de chuva"""
        if self._scenario in ["rain", "storm"]:
            return True, 0.85
        else:
            return False, 0.15