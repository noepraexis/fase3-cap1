#!/usr/bin/env python3
"""
Módulo de decisão inteligente de irrigação baseado em dados meteorológicos.

Este módulo combina dados dos sensores com informações meteorológicas
para tomar decisões mais eficientes sobre quando irrigar.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from weather_api import WeatherData, WeatherForecast, WeatherCondition


class IrrigationDecision(Enum):
    """Decisões possíveis do sistema"""
    IRRIGATE = "irrigate"
    SKIP = "skip"
    REDUCE = "reduce"
    POSTPONE = "postpone"


@dataclass
class DecisionContext:
    """Contexto para tomada de decisão"""
    soil_moisture: float  # 0-100%
    soil_ph: float  # 0-14
    soil_nutrients: float  # 0-100%
    weather_current: Optional[WeatherData]
    weather_forecast: Optional[list[WeatherForecast]]
    last_irrigation: Optional[datetime]


@dataclass
class DecisionResult:
    """Resultado da análise de decisão"""
    decision: IrrigationDecision
    confidence: float  # 0-1
    reason: str
    duration_minutes: Optional[int] = None
    postpone_hours: Optional[int] = None
    water_reduction_percent: Optional[float] = None


class IrrigationDecisionEngine:
    """Motor de decisão inteligente para irrigação"""

    # Limiares configuráveis
    MOISTURE_CRITICAL_LOW = 20.0  # Umidade crítica baixa
    MOISTURE_LOW = 30.0  # Umidade baixa
    MOISTURE_OPTIMAL = 60.0  # Umidade ótima
    MOISTURE_HIGH = 80.0  # Umidade alta

    TEMP_HOT = 30.0  # Temperatura quente
    TEMP_COLD = 15.0  # Temperatura fria

    RAIN_THRESHOLD_MM = 5.0  # Chuva significativa
    RAIN_PROBABILITY_HIGH = 0.7  # Alta probabilidade de chuva

    def __init__(self):
        """Inicializa motor de decisão"""
        self.logger = logging.getLogger(__name__)

    def make_decision(self, context: DecisionContext) -> DecisionResult:
        """
        Toma decisão de irrigação baseada no contexto completo.

        Args:
            context: Dados dos sensores e meteorológicos

        Returns:
            Resultado da decisão com justificativa
        """
        # Verifica condições críticas primeiro
        critical_result = self._check_critical_conditions(context)
        if critical_result:
            return critical_result

        # Analisa previsão de chuva
        rain_result = self._analyze_rain_forecast(context)
        if rain_result and rain_result.decision != IrrigationDecision.IRRIGATE:
            return rain_result

        # Analisa condições atuais
        current_result = self._analyze_current_conditions(context)
        if current_result:
            return current_result

        # Decisão padrão baseada apenas na umidade
        return self._moisture_based_decision(context)

    def _check_critical_conditions(self, context: DecisionContext) -> Optional[DecisionResult]:
        """Verifica condições que requerem ação imediata"""
        # Solo extremamente seco sempre requer irrigação
        if context.soil_moisture < self.MOISTURE_CRITICAL_LOW:
            duration = self._calculate_irrigation_duration(
                context.soil_moisture,
                urgent=True
            )
            return DecisionResult(
                decision=IrrigationDecision.IRRIGATE,
                confidence=1.0,
                reason="Umidade do solo criticamente baixa - irrigação urgente necessária",
                duration_minutes=duration
            )

        # Tempestade atual - nunca irrigar
        if (context.weather_current and
            context.weather_current.condition == WeatherCondition.THUNDERSTORM):
            return DecisionResult(
                decision=IrrigationDecision.SKIP,
                confidence=1.0,
                reason="Tempestade em andamento - irrigação cancelada por segurança"
            )

        # Chuva forte atual
        if (context.weather_current and
            context.weather_current.rain_1h > self.RAIN_THRESHOLD_MM):
            return DecisionResult(
                decision=IrrigationDecision.SKIP,
                confidence=0.95,
                reason=f"Chuva atual de {context.weather_current.rain_1h:.1f}mm/h - irrigação desnecessária"
            )

        return None

    def _analyze_rain_forecast(self, context: DecisionContext) -> Optional[DecisionResult]:
        """Analisa previsão de chuva para as próximas horas"""
        if not context.weather_forecast:
            return None

        # Verifica chuva nas próximas 6 horas
        rain_soon = False
        max_rain_prob = 0.0
        total_expected_rain = 0.0
        hours_until_rain = None

        for i, forecast in enumerate(context.weather_forecast[:2]):  # 6 horas
            if forecast.rain_probability > max_rain_prob:
                max_rain_prob = forecast.rain_probability

            total_expected_rain += forecast.rain_volume * forecast.rain_probability

            if (forecast.rain_probability > self.RAIN_PROBABILITY_HIGH or
                forecast.rain_volume > self.RAIN_THRESHOLD_MM):
                rain_soon = True
                if hours_until_rain is None:
                    hours_until_rain = i * 3  # Previsões de 3 em 3 horas

        # Decisão baseada na previsão
        if rain_soon and context.soil_moisture > self.MOISTURE_LOW:
            if hours_until_rain and hours_until_rain <= 3:
                return DecisionResult(
                    decision=IrrigationDecision.SKIP,
                    confidence=0.8,
                    reason=f"Chuva prevista em {hours_until_rain}h com {max_rain_prob*100:.0f}% de probabilidade"
                )
            else:
                return DecisionResult(
                    decision=IrrigationDecision.POSTPONE,
                    confidence=0.7,
                    reason=f"Chuva esperada em {hours_until_rain}h - adiar irrigação",
                    postpone_hours=hours_until_rain
                )

        # Chuva moderada esperada - reduzir irrigação
        if total_expected_rain > 2.0 and context.soil_moisture > self.MOISTURE_CRITICAL_LOW:
            reduction = min(50, total_expected_rain * 10)  # 10% por mm esperado
            return DecisionResult(
                decision=IrrigationDecision.REDUCE,
                confidence=0.6,
                reason=f"Chuva moderada esperada ({total_expected_rain:.1f}mm) - reduzir irrigação",
                water_reduction_percent=reduction
            )

        return None

    def _analyze_current_conditions(self, context: DecisionContext) -> Optional[DecisionResult]:
        """Analisa condições meteorológicas atuais"""
        if not context.weather_current:
            return None

        weather = context.weather_current

        # Alta umidade do ar + solo úmido = não irrigar
        if (weather.humidity > 85 and
            context.soil_moisture > self.MOISTURE_OPTIMAL):
            return DecisionResult(
                decision=IrrigationDecision.SKIP,
                confidence=0.7,
                reason=f"Alta umidade do ar ({weather.humidity:.0f}%) e solo adequado"
            )

        # Temperatura muito alta - irrigação reduzida para evitar evaporação
        if weather.temperature > self.TEMP_HOT:
            if context.soil_moisture < self.MOISTURE_LOW:
                # Solo seco + calor = irrigar com mais água
                duration = self._calculate_irrigation_duration(
                    context.soil_moisture,
                    temperature_factor=1.3
                )
                return DecisionResult(
                    decision=IrrigationDecision.IRRIGATE,
                    confidence=0.8,
                    reason=f"Temperatura alta ({weather.temperature:.1f}°C) e solo seco - irrigação aumentada",
                    duration_minutes=duration
                )
            else:
                # Solo ok + calor = irrigar menos frequentemente mas com mais volume
                return DecisionResult(
                    decision=IrrigationDecision.REDUCE,
                    confidence=0.6,
                    reason=f"Temperatura alta ({weather.temperature:.1f}°C) - irrigar no período mais fresco",
                    water_reduction_percent=20
                )

        # Neblina/orvalho - reduzir irrigação
        if weather.condition == WeatherCondition.MIST and weather.humidity > 90:
            return DecisionResult(
                decision=IrrigationDecision.REDUCE,
                confidence=0.5,
                reason="Neblina/orvalho presente - reduzir irrigação",
                water_reduction_percent=30
            )

        return None

    def _moisture_based_decision(self, context: DecisionContext) -> DecisionResult:
        """Decisão baseada principalmente na umidade do solo"""
        moisture = context.soil_moisture

        if moisture < self.MOISTURE_LOW:
            duration = self._calculate_irrigation_duration(moisture)
            return DecisionResult(
                decision=IrrigationDecision.IRRIGATE,
                confidence=0.7,
                reason=f"Umidade do solo baixa ({moisture:.1f}%) - irrigação necessária",
                duration_minutes=duration
            )

        elif moisture > self.MOISTURE_HIGH:
            return DecisionResult(
                decision=IrrigationDecision.SKIP,
                confidence=0.8,
                reason=f"Umidade do solo adequada ({moisture:.1f}%) - irrigação desnecessária"
            )

        else:
            # Umidade ok - verificar outros fatores
            if self._should_preventive_irrigation(context):
                duration = self._calculate_irrigation_duration(moisture, preventive=True)
                return DecisionResult(
                    decision=IrrigationDecision.IRRIGATE,
                    confidence=0.5,
                    reason="Irrigação preventiva baseada no histórico",
                    duration_minutes=duration
                )
            else:
                return DecisionResult(
                    decision=IrrigationDecision.SKIP,
                    confidence=0.6,
                    reason=f"Umidade do solo adequada ({moisture:.1f}%) - monitorar"
                )

    def _calculate_irrigation_duration(self, moisture: float,
                                     urgent: bool = False,
                                     temperature_factor: float = 1.0,
                                     preventive: bool = False) -> int:
        """
        Calcula duração da irrigação em minutos.

        Args:
            moisture: Umidade atual do solo
            urgent: Se é irrigação urgente
            temperature_factor: Fator de ajuste por temperatura
            preventive: Se é irrigação preventiva
        """
        # Cálculo base: quanto mais seco, mais tempo
        base_duration = max(5, int(60 - moisture))  # 5-60 minutos

        if urgent:
            base_duration = int(base_duration * 1.5)
        elif preventive:
            base_duration = int(base_duration * 0.5)

        # Aplica fator de temperatura
        duration = int(base_duration * temperature_factor)

        # Limita entre 5 e 90 minutos
        return max(5, min(90, duration))

    def _should_preventive_irrigation(self, context: DecisionContext) -> bool:
        """Determina se irrigação preventiva é recomendada"""
        # Se não irrigou nas últimas 24h e umidade está caindo
        if context.last_irrigation:
            hours_since_irrigation = (datetime.now() - context.last_irrigation).total_seconds() / 3600
            if hours_since_irrigation > 24 and context.soil_moisture < self.MOISTURE_OPTIMAL:
                return True

        # Se temperatura vai subir muito
        if context.weather_forecast:
            future_temps = [f.temperature for f in context.weather_forecast[:4]]  # 12h
            if future_temps and max(future_temps) > self.TEMP_HOT:
                return True

        return False

    def get_recommendation_summary(self, result: DecisionResult) -> str:
        """Gera resumo textual da recomendação"""
        summaries = {
            IrrigationDecision.IRRIGATE: f"✅ IRRIGAR por {result.duration_minutes} minutos",
            IrrigationDecision.SKIP: "❌ NÃO IRRIGAR",
            IrrigationDecision.REDUCE: f"⬇️ REDUZIR irrigação em {result.water_reduction_percent:.0f}%",
            IrrigationDecision.POSTPONE: f"⏰ ADIAR irrigação por {result.postpone_hours} horas"
        }

        summary = summaries.get(result.decision, "❓ Decisão desconhecida")
        summary += f"\n📊 Confiança: {result.confidence*100:.0f}%"
        summary += f"\n💬 Motivo: {result.reason}"

        return summary