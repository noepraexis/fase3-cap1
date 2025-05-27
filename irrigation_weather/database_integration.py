#!/usr/bin/env python3
"""
Módulo de integração com o banco de dados do sistema de monitoramento.

Este módulo conecta o sistema de decisão meteorológica com o banco
de dados existente para armazenar decisões e recuperar histórico.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from contextlib import contextmanager

from irrigation_decision import DecisionResult, IrrigationDecision
from weather_api import WeatherData, WeatherForecast


class WeatherDatabaseManager:
    """Gerenciador de banco de dados para dados meteorológicos e decisões"""

    def __init__(self, db_path: str = "../monitoring_database/soil_monitoring.db"):
        """
        Inicializa gerenciador do banco de dados.

        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        self.db_path = Path(db_path).resolve()
        self.logger = logging.getLogger(__name__)

        # Verifica se o banco existe
        if not self.db_path.exists():
            self.logger.warning(f"Banco de dados não encontrado em {self.db_path}")
            self.logger.info("Criando novo banco de dados...")
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_tables()

    @contextmanager
    def get_connection(self):
        """Context manager para conexão com o banco"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Erro na transação do banco: {e}")
            raise
        finally:
            conn.close()

    def _init_tables(self):
        """Cria tabelas necessárias se não existirem"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Tabela de dados meteorológicos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    temperature REAL NOT NULL,
                    humidity REAL NOT NULL,
                    pressure REAL NOT NULL,
                    condition TEXT NOT NULL,
                    description TEXT,
                    wind_speed REAL,
                    rain_1h REAL,
                    rain_3h REAL,
                    clouds INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabela de previsões meteorológicas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather_forecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    forecast_time DATETIME NOT NULL,
                    temperature REAL NOT NULL,
                    humidity REAL NOT NULL,
                    condition TEXT NOT NULL,
                    rain_probability REAL,
                    rain_volume REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabela de decisões de irrigação
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS irrigation_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    decision TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reason TEXT NOT NULL,
                    duration_minutes INTEGER,
                    postpone_hours INTEGER,
                    water_reduction_percent REAL,
                    soil_moisture REAL,
                    soil_ph REAL,
                    soil_nutrients REAL,
                    weather_data_id INTEGER,
                    executed BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (weather_data_id) REFERENCES weather_data (id)
                )
            """)

            # Índices para melhor performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_weather_timestamp
                ON weather_data(timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_decisions_timestamp
                ON irrigation_decisions(timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_decisions_executed
                ON irrigation_decisions(executed)
            """)

    def save_weather_data(self, weather: WeatherData) -> int:
        """
        Salva dados meteorológicos atuais.

        Returns:
            ID do registro inserido
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO weather_data (
                    timestamp, temperature, humidity, pressure,
                    condition, description, wind_speed,
                    rain_1h, rain_3h, clouds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                weather.timestamp,
                weather.temperature,
                weather.humidity,
                weather.pressure,
                weather.condition.value,
                weather.description,
                weather.wind_speed,
                weather.rain_1h,
                weather.rain_3h,
                weather.clouds
            ))

            return cursor.lastrowid

    def save_weather_forecasts(self, forecasts: List[WeatherForecast]):
        """Salva previsões meteorológicas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Remove previsões antigas
            cursor.execute("""
                DELETE FROM weather_forecasts
                WHERE created_at < datetime('now', '-1 day')
            """)

            # Insere novas previsões
            for forecast in forecasts:
                cursor.execute("""
                    INSERT INTO weather_forecasts (
                        forecast_time, temperature, humidity,
                        condition, rain_probability, rain_volume
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    forecast.timestamp,
                    forecast.temperature,
                    forecast.humidity,
                    forecast.condition.value,
                    forecast.rain_probability,
                    forecast.rain_volume
                ))

    def save_irrigation_decision(self, decision: DecisionResult,
                               context_data: Dict,
                               weather_data_id: Optional[int] = None) -> int:
        """
        Salva decisão de irrigação.

        Args:
            decision: Resultado da decisão
            context_data: Dados do contexto (sensores)
            weather_data_id: ID dos dados meteorológicos relacionados

        Returns:
            ID do registro inserido
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO irrigation_decisions (
                    timestamp, decision, confidence, reason,
                    duration_minutes, postpone_hours, water_reduction_percent,
                    soil_moisture, soil_ph, soil_nutrients,
                    weather_data_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                decision.decision.value,
                decision.confidence,
                decision.reason,
                decision.duration_minutes,
                decision.postpone_hours,
                decision.water_reduction_percent,
                context_data.get('soil_moisture'),
                context_data.get('soil_ph'),
                context_data.get('soil_nutrients'),
                weather_data_id
            ))

            return cursor.lastrowid

    def mark_decision_executed(self, decision_id: int):
        """Marca uma decisão como executada"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE irrigation_decisions
                SET executed = TRUE
                WHERE id = ?
            """, (decision_id,))

    def get_last_irrigation_time(self) -> Optional[datetime]:
        """Obtém horário da última irrigação executada"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            result = cursor.execute("""
                SELECT timestamp
                FROM irrigation_decisions
                WHERE decision = 'irrigate' AND executed = TRUE
                ORDER BY timestamp DESC
                LIMIT 1
            """).fetchone()

            if result:
                return datetime.fromisoformat(result['timestamp'])
            return None

    def get_recent_decisions(self, hours: int = 24) -> List[Dict]:
        """Obtém decisões recentes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            results = cursor.execute("""
                SELECT * FROM irrigation_decisions
                WHERE timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            """.format(hours)).fetchall()

            return [dict(row) for row in results]

    def get_decision_statistics(self, days: int = 7) -> Dict:
        """Calcula estatísticas das decisões"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Total de decisões por tipo
            decisions = cursor.execute("""
                SELECT decision, COUNT(*) as count
                FROM irrigation_decisions
                WHERE timestamp > datetime('now', '-{} days')
                GROUP BY decision
            """.format(days)).fetchall()

            # Taxa de execução
            execution_rate = cursor.execute("""
                SELECT
                    COUNT(CASE WHEN executed = TRUE THEN 1 END) * 100.0 / COUNT(*) as rate
                FROM irrigation_decisions
                WHERE decision = 'irrigate'
                    AND timestamp > datetime('now', '-{} days')
            """.format(days)).fetchone()

            # Economia de água estimada
            water_saved = cursor.execute("""
                SELECT
                    SUM(CASE
                        WHEN decision = 'skip' THEN 30
                        WHEN decision = 'reduce' THEN duration_minutes * water_reduction_percent / 100
                        WHEN decision = 'postpone' THEN 20
                        ELSE 0
                    END) as total_saved
                FROM irrigation_decisions
                WHERE timestamp > datetime('now', '-{} days')
            """.format(days)).fetchone()

            stats = {
                'period_days': days,
                'decisions_by_type': {row['decision']: row['count'] for row in decisions},
                'execution_rate': execution_rate['rate'] if execution_rate['rate'] else 0,
                'estimated_water_saved_minutes': water_saved['total_saved'] if water_saved['total_saved'] else 0
            }

            return stats

    def get_weather_impact_analysis(self, days: int = 30) -> Dict:
        """Analisa impacto das condições meteorológicas nas decisões"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Decisões por condição meteorológica
            by_condition = cursor.execute("""
                SELECT
                    w.condition,
                    d.decision,
                    COUNT(*) as count
                FROM irrigation_decisions d
                JOIN weather_data w ON d.weather_data_id = w.id
                WHERE d.timestamp > datetime('now', '-{} days')
                GROUP BY w.condition, d.decision
            """.format(days)).fetchall()

            # Correlação chuva vs decisões
            rain_impact = cursor.execute("""
                SELECT
                    CASE
                        WHEN w.rain_1h > 5 THEN 'heavy_rain'
                        WHEN w.rain_1h > 0 THEN 'light_rain'
                        ELSE 'no_rain'
                    END as rain_status,
                    d.decision,
                    COUNT(*) as count
                FROM irrigation_decisions d
                JOIN weather_data w ON d.weather_data_id = w.id
                WHERE d.timestamp > datetime('now', '-{} days')
                GROUP BY rain_status, d.decision
            """.format(days)).fetchall()

            return {
                'decisions_by_weather': [dict(row) for row in by_condition],
                'rain_impact': [dict(row) for row in rain_impact]
            }