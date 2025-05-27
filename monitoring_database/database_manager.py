#!/usr/bin/env python3
"""
Gerenciador de Banco de Dados SQL
Sistema de armazenamento para dados do monitoramento de solo
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager
import os

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SoilMonitorDatabase:
    """Gerenciador de banco de dados para o sistema de monitoramento de solo"""

    def __init__(self, db_path: str = "soil_monitoring.db"):
        """
        Inicializa o gerenciador de banco de dados

        Args:
            db_path: Caminho para o arquivo do banco SQLite
        """
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager para conexões seguras ao banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro na transação: {e}")
            raise
        finally:
            conn.close()

    def init_database(self):
        """Cria as tabelas do banco de dados se não existirem"""

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Tabela principal de leituras dos sensores
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    temperature REAL NOT NULL,
                    humidity REAL NOT NULL,
                    ph REAL NOT NULL,
                    phosphorus BOOLEAN NOT NULL,
                    potassium BOOLEAN NOT NULL,
                    esp_timestamp INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabela de eventos de irrigação
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS irrigation_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type VARCHAR(20) NOT NULL,
                    duration_seconds INTEGER,
                    trigger_source VARCHAR(20),
                    moisture_level REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabela de estatísticas do sistema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    free_heap INTEGER,
                    uptime_seconds INTEGER,
                    wifi_status VARCHAR(20),
                    irrigation_active BOOLEAN,
                    daily_activations INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabela de alertas e anomalias
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    alert_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    message TEXT,
                    sensor_value REAL,
                    threshold_value REAL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Índices para otimização de consultas
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_timestamp ON sensor_readings(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_irrigation_timestamp ON irrigation_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity, resolved)")

            logger.info("Banco de dados inicializado com sucesso")

    # ==================== OPERAÇÕES CRUD ====================

    # CREATE - Inserção de dados
    def insert_sensor_reading(self, data: Dict) -> int:
        """
        Insere uma nova leitura de sensores

        Args:
            data: Dicionário com dados dos sensores

        Returns:
            ID do registro inserido
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            sensors = data.get('sensors', {})
            cursor.execute("""
                INSERT INTO sensor_readings
                (temperature, humidity, ph, phosphorus, potassium, esp_timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sensors.get('temperature', 0),
                sensors.get('humidity', 0),
                sensors.get('ph', 7),
                sensors.get('phosphorus', False),
                sensors.get('potassium', False),
                sensors.get('timestamp', 0)
            ))

            reading_id = cursor.lastrowid
            logger.info(f"Leitura de sensores inserida com ID: {reading_id}")

            # Verifica alertas baseados nos valores
            self._check_alerts(sensors)

            return reading_id

    def insert_irrigation_event(self, event_type: str, duration: int = None,
                              trigger: str = "manual", moisture: float = None) -> int:
        """
        Registra um evento de irrigação

        Args:
            event_type: Tipo do evento (start, stop, error)
            duration: Duração em segundos (para eventos stop)
            trigger: Fonte do acionamento (manual, auto, emergency)
            moisture: Nível de umidade no momento

        Returns:
            ID do evento inserido
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO irrigation_events
                (event_type, duration_seconds, trigger_source, moisture_level)
                VALUES (?, ?, ?, ?)
            """, (event_type, duration, trigger, moisture))

            event_id = cursor.lastrowid
            logger.info(f"Evento de irrigação '{event_type}' registrado com ID: {event_id}")

            return event_id

    def insert_system_stats(self, data: Dict) -> int:
        """
        Insere estatísticas do sistema

        Args:
            data: Dicionário com dados do sistema

        Returns:
            ID do registro inserido
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            system = data.get('system', {})
            irrigation = data.get('irrigation', {})

            cursor.execute("""
                INSERT INTO system_stats
                (free_heap, uptime_seconds, wifi_status, irrigation_active, daily_activations)
                VALUES (?, ?, ?, ?, ?)
            """, (
                system.get('freeHeap', 0),
                system.get('uptime', 0),
                system.get('wifi', 'Unknown'),
                irrigation.get('active', False),
                irrigation.get('dailyActivations', 0)
            ))

            return cursor.lastrowid

    # READ - Consulta de dados
    def get_latest_readings(self, limit: int = 10) -> List[Dict]:
        """
        Obtém as últimas leituras dos sensores

        Args:
            limit: Número máximo de registros

        Returns:
            Lista de leituras ordenadas por timestamp
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sensor_readings
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_readings_by_period(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Obtém leituras em um período específico

        Args:
            start_date: Data inicial (YYYY-MM-DD HH:MM:SS)
            end_date: Data final (YYYY-MM-DD HH:MM:SS)

        Returns:
            Lista de leituras no período
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sensor_readings
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            """, (start_date, end_date))

            return [dict(row) for row in cursor.fetchall()]

    def get_irrigation_history(self, days: int = 7) -> List[Dict]:
        """
        Obtém histórico de irrigação

        Args:
            days: Número de dias para consultar

        Returns:
            Lista de eventos de irrigação
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM irrigation_events
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
                ORDER BY timestamp DESC
            """, (days,))

            return [dict(row) for row in cursor.fetchall()]

    def get_active_alerts(self) -> List[Dict]:
        """
        Obtém alertas não resolvidos

        Returns:
            Lista de alertas ativos
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM alerts
                WHERE resolved = FALSE
                ORDER BY severity DESC, timestamp DESC
            """)

            return [dict(row) for row in cursor.fetchall()]

    # UPDATE - Atualização de dados
    def update_sensor_reading(self, reading_id: int, **kwargs) -> bool:
        """
        Atualiza uma leitura específica

        Args:
            reading_id: ID da leitura
            **kwargs: Campos a atualizar

        Returns:
            True se atualizado com sucesso
        """
        valid_fields = ['temperature', 'humidity', 'ph', 'phosphorus', 'potassium']
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}

        if not updates:
            logger.warning("Nenhum campo válido para atualizar")
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()

            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [reading_id]

            cursor.execute(f"""
                UPDATE sensor_readings
                SET {set_clause}
                WHERE id = ?
            """, values)

            success = cursor.rowcount > 0
            if success:
                logger.info(f"Leitura {reading_id} atualizada com sucesso")

            return success

    def resolve_alert(self, alert_id: int, resolution_message: str = None) -> bool:
        """
        Marca um alerta como resolvido

        Args:
            alert_id: ID do alerta
            resolution_message: Mensagem de resolução opcional

        Returns:
            True se resolvido com sucesso
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE alerts
                SET resolved = TRUE,
                    resolved_at = CURRENT_TIMESTAMP,
                    message = COALESCE(?, message)
                WHERE id = ?
            """, (resolution_message, alert_id))

            success = cursor.rowcount > 0
            if success:
                logger.info(f"Alerta {alert_id} resolvido")

            return success

    # DELETE - Remoção de dados
    def delete_old_readings(self, days_to_keep: int = 30) -> int:
        """
        Remove leituras antigas do banco

        Args:
            days_to_keep: Número de dias para manter

        Returns:
            Número de registros removidos
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM sensor_readings
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            """, (days_to_keep,))

            deleted = cursor.rowcount
            if deleted > 0:
                logger.info(f"{deleted} leituras antigas removidas")

            return deleted

    def delete_reading(self, reading_id: int) -> bool:
        """
        Remove uma leitura específica

        Args:
            reading_id: ID da leitura

        Returns:
            True se removido com sucesso
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM sensor_readings WHERE id = ?", (reading_id,))

            success = cursor.rowcount > 0
            if success:
                logger.info(f"Leitura {reading_id} removida")

            return success

    # ==================== OPERAÇÕES ANALÍTICAS ====================

    def get_statistics(self, hours: int = 24) -> Dict:
        """
        Calcula estatísticas dos sensores

        Args:
            hours: Período em horas para análise

        Returns:
            Dicionário com estatísticas
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    AVG(temperature) as avg_temp,
                    MIN(temperature) as min_temp,
                    MAX(temperature) as max_temp,
                    AVG(humidity) as avg_humidity,
                    MIN(humidity) as min_humidity,
                    MAX(humidity) as max_humidity,
                    AVG(ph) as avg_ph,
                    MIN(ph) as min_ph,
                    MAX(ph) as max_ph,
                    COUNT(*) as total_readings
                FROM sensor_readings
                WHERE timestamp >= datetime('now', '-' || ? || ' hours')
            """, (hours,))

            stats = dict(cursor.fetchone())

            # Estatísticas de irrigação
            cursor.execute("""
                SELECT
                    COUNT(*) as irrigation_count,
                    SUM(duration_seconds) as total_duration
                FROM irrigation_events
                WHERE timestamp >= datetime('now', '-' || ? || ' hours')
                AND event_type = 'stop'
            """, (hours,))

            irrigation_stats = dict(cursor.fetchone())
            stats.update(irrigation_stats)

            return stats

    def _check_alerts(self, sensor_data: Dict):
        """
        Verifica e cria alertas baseados em limiares

        Args:
            sensor_data: Dados dos sensores
        """
        alerts = []

        # Verifica temperatura
        temp = sensor_data.get('temperature', 25)
        if temp > 35:
            alerts.append(('high_temperature', 'warning', f'Temperatura alta: {temp}°C', temp, 35))
        elif temp < 15:
            alerts.append(('low_temperature', 'warning', f'Temperatura baixa: {temp}°C', temp, 15))

        # Verifica pH
        ph = sensor_data.get('ph', 7)
        if ph < 6 or ph > 8:
            severity = 'critical' if ph < 5 or ph > 9 else 'warning'
            alerts.append(('ph_out_of_range', severity, f'pH fora da faixa ideal: {ph}', ph, 7))

        # Verifica umidade
        humidity = sensor_data.get('humidity', 50)
        if humidity < 30:
            alerts.append(('low_humidity', 'warning', f'Umidade baixa: {humidity}%', humidity, 30))
        elif humidity > 70:
            alerts.append(('high_humidity', 'info', f'Umidade alta: {humidity}%', humidity, 70))

        # Insere alertas no banco
        if alerts:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany("""
                    INSERT INTO alerts
                    (alert_type, severity, message, sensor_value, threshold_value)
                    VALUES (?, ?, ?, ?, ?)
                """, alerts)

                logger.info(f"{len(alerts)} alertas criados")


def main():
    """Função principal para demonstração"""

    # Cria instância do banco
    db = SoilMonitorDatabase()

    # Dados de exemplo
    sample_data = {
        "sensors": {
            "temperature": 25.5,
            "humidity": 45.2,
            "ph": 6.8,
            "phosphorus": True,
            "potassium": False,
            "timestamp": int(time.time() * 1000)
        },
        "irrigation": {
            "active": True,
            "uptime": 120,
            "dailyActivations": 3
        },
        "system": {
            "freeHeap": 145632,
            "uptime": 3600,
            "wifi": "Connected"
        }
    }

    # Demonstra operações CRUD
    print("\n=== DEMONSTRAÇÃO CRUD ===\n")

    # CREATE
    print("1. INSERT - Inserindo leitura de sensores...")
    reading_id = db.insert_sensor_reading(sample_data)
    print(f"   Leitura inserida com ID: {reading_id}")

    # READ
    print("\n2. SELECT - Consultando últimas leituras...")
    readings = db.get_latest_readings(5)
    print(f"   Encontradas {len(readings)} leituras")

    # UPDATE
    print("\n3. UPDATE - Atualizando temperatura...")
    success = db.update_sensor_reading(reading_id, temperature=28.5)
    print(f"   Atualização: {'Sucesso' if success else 'Falhou'}")

    # DELETE
    print("\n4. DELETE - Removendo leituras antigas...")
    deleted = db.delete_old_readings(365)
    print(f"   {deleted} registros removidos")

    # Estatísticas
    print("\n=== ESTATÍSTICAS (24h) ===")
    stats = db.get_statistics(24)
    print(f"   Temperatura: {stats['avg_temp']:.1f}°C (min: {stats['min_temp']:.1f}, max: {stats['max_temp']:.1f})")
    print(f"   Umidade: {stats['avg_humidity']:.1f}% (min: {stats['min_humidity']:.1f}, max: {stats['max_humidity']:.1f})")
    print(f"   pH: {stats['avg_ph']:.1f} (min: {stats['min_ph']:.1f}, max: {stats['max_ph']:.1f})")
    print(f"   Total de leituras: {stats['total_readings']}")


if __name__ == "__main__":
    import time
    main()