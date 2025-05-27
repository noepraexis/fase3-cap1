#!/usr/bin/env python3
"""
Sistema principal de irrigação inteligente com integração meteorológica.

Este script integra todos os componentes: API meteorológica, lógica de
decisão e banco de dados para criar um sistema completo de irrigação
baseado em condições climáticas.
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

# Adiciona o diretório do monitoring_database ao path
sys.path.append(str(Path(__file__).parent.parent / "monitoring_database"))

from weather_api import WeatherAPI, WeatherSimulator
from irrigation_decision import IrrigationDecisionEngine, DecisionContext, IrrigationDecision
from database_integration import WeatherDatabaseManager
from monitoring_database.database_manager import SoilMonitorDatabase


class WeatherIrrigationSystem:
    """Sistema completo de irrigação com inteligência meteorológica"""

    def __init__(self, api_key: Optional[str] = None,
                 city: str = "São Paulo",
                 use_simulator: bool = False):
        """
        Inicializa o sistema.

        Args:
            api_key: Chave da API OpenWeather (opcional se usar simulador)
            city: Cidade para buscar dados meteorológicos
            use_simulator: Se True, usa simulador ao invés da API real
        """
        # Configuração de logging
        self._setup_logging()

        # Inicializa componentes
        if use_simulator:
            self.logger.info("Usando simulador de dados meteorológicos")
            self.weather_api = WeatherSimulator()
        else:
            if not api_key:
                raise ValueError("API key é necessária quando não usar simulador")
            self.weather_api = WeatherAPI(api_key, city)

        self.decision_engine = IrrigationDecisionEngine()
        self.weather_db = WeatherDatabaseManager()
        self.sensor_db = SoilMonitorDatabase("../monitoring_database/soil_monitoring.db")

        self.logger.info(f"Sistema inicializado para {city}")

    def _setup_logging(self):
        """Configura sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('weather_irrigation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def get_latest_sensor_data(self) -> Optional[Dict]:
        """Obtém dados mais recentes dos sensores"""
        try:
            # Busca última leitura do banco
            readings = self.sensor_db.get_latest_readings(limit=1)
            if readings:
                return {
                    'soil_moisture': readings[0]['moisture'],
                    'soil_ph': readings[0]['ph'],
                    'soil_nutrients': readings[0]['nutrients'],
                    'timestamp': readings[0]['timestamp']
                }

            # Se não houver dados, usa valores padrão para demonstração
            self.logger.warning("Nenhum dado de sensor encontrado, usando valores padrão")
            return {
                'soil_moisture': 45.0,
                'soil_ph': 6.5,
                'soil_nutrients': 70.0,
                'timestamp': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Erro ao obter dados dos sensores: {e}")
            return None

    def process_irrigation_decision(self) -> Optional[Dict]:
        """
        Processa decisão de irrigação completa.

        Returns:
            Dicionário com decisão e detalhes ou None em caso de erro
        """
        try:
            # 1. Obtém dados dos sensores
            sensor_data = self.get_latest_sensor_data()
            if not sensor_data:
                self.logger.error("Impossível obter dados dos sensores")
                return None

            self.logger.info(f"Dados dos sensores: Umidade={sensor_data['soil_moisture']:.1f}%, "
                           f"pH={sensor_data['soil_ph']:.1f}, "
                           f"Nutrientes={sensor_data['soil_nutrients']:.1f}%")

            # 2. Obtém dados meteorológicos
            current_weather = self.weather_api.get_current_weather()
            weather_forecast = self.weather_api.get_forecast(hours=12)

            if current_weather:
                self.logger.info(f"Clima atual: {current_weather.condition.value}, "
                               f"Temp={current_weather.temperature:.1f}°C, "
                               f"Umidade={current_weather.humidity:.0f}%, "
                               f"Chuva 1h={current_weather.rain_1h:.1f}mm")

            # 3. Salva dados meteorológicos
            weather_id = None
            if current_weather:
                weather_id = self.weather_db.save_weather_data(current_weather)

            if weather_forecast:
                self.weather_db.save_weather_forecasts(weather_forecast)

            # 4. Obtém última irrigação
            last_irrigation = self.weather_db.get_last_irrigation_time()

            # 5. Cria contexto de decisão
            context = DecisionContext(
                soil_moisture=sensor_data['soil_moisture'],
                soil_ph=sensor_data['soil_ph'],
                soil_nutrients=sensor_data['soil_nutrients'],
                weather_current=current_weather,
                weather_forecast=weather_forecast,
                last_irrigation=last_irrigation
            )

            # 6. Toma decisão
            decision = self.decision_engine.make_decision(context)
            self.logger.info(f"Decisão: {decision.decision.value} "
                           f"(confiança: {decision.confidence*100:.0f}%)")
            self.logger.info(f"Motivo: {decision.reason}")

            # 7. Salva decisão no banco
            decision_id = self.weather_db.save_irrigation_decision(
                decision, sensor_data, weather_id
            )

            # 8. Executa ação se necessário
            action_result = self._execute_decision(decision, decision_id)

            # 9. Prepara resultado
            result = {
                'timestamp': datetime.now().isoformat(),
                'sensor_data': sensor_data,
                'weather': {
                    'current': {
                        'condition': current_weather.condition.value if current_weather else None,
                        'temperature': current_weather.temperature if current_weather else None,
                        'humidity': current_weather.humidity if current_weather else None,
                        'rain_1h': current_weather.rain_1h if current_weather else None
                    } if current_weather else None,
                    'will_rain_soon': self.weather_api.will_rain_soon(hours=6)
                },
                'decision': {
                    'action': decision.decision.value,
                    'confidence': decision.confidence,
                    'reason': decision.reason,
                    'duration_minutes': decision.duration_minutes,
                    'postpone_hours': decision.postpone_hours,
                    'water_reduction_percent': decision.water_reduction_percent
                },
                'executed': action_result
            }

            return result

        except Exception as e:
            self.logger.error(f"Erro ao processar decisão: {e}", exc_info=True)
            return None

    def _execute_decision(self, decision, decision_id: int) -> bool:
        """
        Executa a decisão tomada.

        Args:
            decision: Resultado da decisão
            decision_id: ID da decisão no banco

        Returns:
            True se executado com sucesso
        """
        try:
            if decision.decision == IrrigationDecision.IRRIGATE:
                # Registra evento de irrigação
                duration = decision.duration_minutes or 30
                self.sensor_db.insert_irrigation_event(
                    event_type="start",
                    duration=duration,
                    reason=f"Weather-based: {decision.reason}"
                )

                self.logger.info(f"🚿 Irrigação iniciada por {duration} minutos")

                # Marca decisão como executada
                self.weather_db.mark_decision_executed(decision_id)
                return True

            elif decision.decision == IrrigationDecision.SKIP:
                self.logger.info("⏸️ Irrigação cancelada")
                return True

            elif decision.decision == IrrigationDecision.REDUCE:
                self.logger.info(f"⬇️ Irrigação reduzida em {decision.water_reduction_percent:.0f}%")
                return True

            elif decision.decision == IrrigationDecision.POSTPONE:
                self.logger.info(f"⏰ Irrigação adiada por {decision.postpone_hours} horas")
                return True

        except Exception as e:
            self.logger.error(f"Erro ao executar decisão: {e}")
            return False

    def run_continuous(self, interval_minutes: int = 30):
        """
        Executa o sistema continuamente.

        Args:
            interval_minutes: Intervalo entre verificações
        """
        self.logger.info(f"Iniciando modo contínuo (intervalo: {interval_minutes} min)")

        while True:
            try:
                self.logger.info("=" * 60)
                self.logger.info("Processando ciclo de decisão...")

                result = self.process_irrigation_decision()

                if result:
                    # Exibe resumo
                    summary = self.decision_engine.get_recommendation_summary(
                        self.decision_engine.make_decision(
                            DecisionContext(
                                soil_moisture=result['sensor_data']['soil_moisture'],
                                soil_ph=result['sensor_data']['soil_ph'],
                                soil_nutrients=result['sensor_data']['soil_nutrients'],
                                weather_current=None,
                                weather_forecast=None,
                                last_irrigation=None
                            )
                        )
                    )
                    print("\n" + summary + "\n")

                # Aguarda próximo ciclo
                self.logger.info(f"Próxima verificação em {interval_minutes} minutos...")
                time.sleep(interval_minutes * 60)

            except KeyboardInterrupt:
                self.logger.info("Sistema interrompido pelo usuário")
                break
            except Exception as e:
                self.logger.error(f"Erro no ciclo: {e}", exc_info=True)
                time.sleep(60)  # Aguarda 1 minuto em caso de erro

    def get_system_report(self, days: int = 7) -> Dict:
        """Gera relatório do sistema"""
        try:
            stats = self.weather_db.get_decision_statistics(days)
            impact = self.weather_db.get_weather_impact_analysis(days)
            recent_decisions = self.weather_db.get_recent_decisions(24)

            report = {
                'period': f"Últimos {days} dias",
                'statistics': stats,
                'weather_impact': impact,
                'recent_decisions': recent_decisions[:10],  # Últimas 10 decisões
                'system_health': {
                    'weather_api': 'OK' if self.weather_api.get_current_weather() else 'ERROR',
                    'database': 'OK',
                    'decision_engine': 'OK'
                }
            }

            return report

        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            return {'error': str(e)}


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Sistema de Irrigação Inteligente com Dados Meteorológicos"
    )
    parser.add_argument(
        '--api-key',
        help='Chave da API OpenWeather (obtenha em openweathermap.org/api)'
    )
    parser.add_argument(
        '--city',
        default='São Paulo',
        help='Cidade para dados meteorológicos (padrão: São Paulo)'
    )
    parser.add_argument(
        '--simulator',
        action='store_true',
        help='Usar simulador ao invés da API real'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Executar continuamente'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Intervalo em minutos para modo contínuo (padrão: 30)'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Gerar relatório do sistema'
    )
    parser.add_argument(
        '--scenario',
        choices=['normal', 'rain', 'drought', 'storm'],
        default='normal',
        help='Cenário para o simulador'
    )

    args = parser.parse_args()

    # Verifica API key
    api_key = args.api_key or os.getenv('OPENWEATHER_API_KEY')
    if not args.simulator and not api_key:
        print("ERRO: API key necessária. Use --api-key ou defina OPENWEATHER_API_KEY")
        print("Obtenha uma chave gratuita em: https://openweathermap.org/api")
        print("Ou use --simulator para modo de demonstração")
        sys.exit(1)

    # Cria sistema
    system = WeatherIrrigationSystem(
        api_key=api_key,
        city=args.city,
        use_simulator=args.simulator
    )

    # Define cenário do simulador se aplicável
    if args.simulator and hasattr(system.weather_api, 'set_scenario'):
        system.weather_api.set_scenario(args.scenario)

    # Executa comando apropriado
    if args.report:
        report = system.get_system_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.continuous:
        system.run_continuous(args.interval)
    else:
        # Executa uma vez
        result = system.process_irrigation_decision()
        if result:
            print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()