#!/usr/bin/env python3
"""
Pipeline de Dados - Integração Serial Reader + Database
Conecta a leitura serial do ESP32 ao armazenamento SQL
"""

import json
import time
import logging
import signal
import sys
from datetime import datetime
from threading import Thread, Event
from typing import Optional

from serial_reader import ESP32SerialReader, simulate_esp32_data
from database_manager import SoilMonitorDatabase

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPipeline:
    """Pipeline para captura e armazenamento de dados do ESP32"""

    def __init__(self, serial_port: str = None, db_path: str = "soil_monitoring.db"):
        """
        Inicializa o pipeline de dados

        Args:
            serial_port: Porta serial do ESP32 (None para simulador)
            db_path: Caminho do banco de dados SQLite
        """
        self.serial_port = serial_port
        self.use_simulator = serial_port is None

        # Componentes
        self.reader = None if self.use_simulator else ESP32SerialReader(serial_port)
        self.database = SoilMonitorDatabase(db_path)

        # Controle de execução
        self.running = False
        self.stop_event = Event()
        self.pipeline_thread = None

        # Estatísticas
        self.stats = {
            'readings_received': 0,
            'readings_stored': 0,
            'errors': 0,
            'start_time': None
        }

        # Estado da irrigação para detecção de mudanças
        self.last_irrigation_state = None
        self.irrigation_start_time = None

    def start(self):
        """Inicia o pipeline de dados"""
        logger.info("Iniciando pipeline de dados...")

        # Conecta ao ESP32 se não estiver em modo simulador
        if not self.use_simulator:
            if not self.reader.connect():
                logger.error("Falha ao conectar com ESP32")
                return False

            self.reader.start_reading()

        # Inicia thread do pipeline
        self.running = True
        self.stats['start_time'] = datetime.now()
        self.pipeline_thread = Thread(target=self._pipeline_worker)
        self.pipeline_thread.daemon = True
        self.pipeline_thread.start()

        logger.info(f"Pipeline iniciado ({'Simulador' if self.use_simulator else 'Hardware real'})")
        return True

    def stop(self):
        """Para o pipeline de dados"""
        logger.info("Parando pipeline de dados...")

        self.running = False
        self.stop_event.set()

        if self.pipeline_thread:
            self.pipeline_thread.join(timeout=5.0)

        if self.reader:
            self.reader.stop_reading()
            self.reader.disconnect()

        # Mostra estatísticas finais
        self._print_statistics()

        logger.info("Pipeline parado")

    def _pipeline_worker(self):
        """Worker principal do pipeline"""
        logger.info("Pipeline worker iniciado")

        while self.running and not self.stop_event.is_set():
            try:
                # Obtém dados (simulados ou reais)
                if self.use_simulator:
                    data = simulate_esp32_data()
                    time.sleep(2)  # Taxa de simulação
                else:
                    data = self.reader.get_data(timeout=2.0)

                if data:
                    self.stats['readings_received'] += 1

                    # Processa e armazena dados
                    self._process_data(data)

            except Exception as e:
                logger.error(f"Erro no pipeline: {e}")
                self.stats['errors'] += 1
                time.sleep(1)

        logger.info("Pipeline worker finalizado")

    def _process_data(self, data: dict):
        """
        Processa e armazena dados recebidos

        Args:
            data: Dados telemetria do ESP32
        """
        try:
            # Armazena leitura dos sensores
            reading_id = self.database.insert_sensor_reading(data)

            # Armazena estatísticas do sistema
            self.database.insert_system_stats(data)

            # Detecta mudanças no estado da irrigação
            self._check_irrigation_changes(data)

            self.stats['readings_stored'] += 1

            # Log a cada 10 leituras
            if self.stats['readings_stored'] % 10 == 0:
                logger.info(f"Leituras armazenadas: {self.stats['readings_stored']}")

            # Mostra dados em tempo real (opcional)
            if logger.level <= logging.DEBUG:
                self._display_realtime_data(data)

        except Exception as e:
            logger.error(f"Erro ao processar dados: {e}")
            self.stats['errors'] += 1

    def _check_irrigation_changes(self, data: dict):
        """
        Detecta e registra mudanças no estado da irrigação

        Args:
            data: Dados com informações de irrigação
        """
        irrigation = data.get('irrigation', {})
        current_state = irrigation.get('active', False)

        # Primeira leitura
        if self.last_irrigation_state is None:
            self.last_irrigation_state = current_state
            if current_state:
                self.irrigation_start_time = datetime.now()
            return

        # Detecta mudança de estado
        if current_state != self.last_irrigation_state:
            sensors = data.get('sensors', {})

            if current_state:
                # Irrigação iniciada
                self.irrigation_start_time = datetime.now()
                self.database.insert_irrigation_event(
                    event_type='start',
                    trigger='auto' if sensors.get('humidity', 50) < 30 else 'manual',
                    moisture=sensors.get('humidity')
                )
                logger.info("🚿 Irrigação INICIADA")

            else:
                # Irrigação parada
                duration = None
                if self.irrigation_start_time:
                    duration = int((datetime.now() - self.irrigation_start_time).total_seconds())

                self.database.insert_irrigation_event(
                    event_type='stop',
                    duration=duration,
                    moisture=sensors.get('humidity')
                )
                logger.info(f"💧 Irrigação PARADA (duração: {duration}s)")

            self.last_irrigation_state = current_state

    def _display_realtime_data(self, data: dict):
        """
        Exibe dados em tempo real no console

        Args:
            data: Dados para exibição
        """
        sensors = data.get('sensors', {})
        irrigation = data.get('irrigation', {})

        print("\n" + "="*50)
        print(f"🌡️  Temperatura: {sensors.get('temperature', 0):.1f}°C")
        print(f"💧 Umidade: {sensors.get('humidity', 0):.1f}%")
        print(f"🧪 pH: {sensors.get('ph', 7):.1f}")
        print(f"🌱 Nutrientes - P: {'✓' if sensors.get('phosphorus') else '✗'} | K: {'✓' if sensors.get('potassium') else '✗'}")
        print(f"🚿 Irrigação: {'LIGADA' if irrigation.get('active') else 'DESLIGADA'}")
        print("="*50)

    def _print_statistics(self):
        """Exibe estatísticas do pipeline"""
        if self.stats['start_time']:
            runtime = (datetime.now() - self.stats['start_time']).total_seconds()

            print("\n" + "="*60)
            print("📊 ESTATÍSTICAS DO PIPELINE")
            print("="*60)
            print(f"Tempo de execução: {runtime:.0f}s")
            print(f"Leituras recebidas: {self.stats['readings_received']}")
            print(f"Leituras armazenadas: {self.stats['readings_stored']}")
            print(f"Erros: {self.stats['errors']}")
            print(f"Taxa de sucesso: {(self.stats['readings_stored'] / max(self.stats['readings_received'], 1)) * 100:.1f}%")

            # Estatísticas do banco
            db_stats = self.database.get_statistics(hours=1)
            print("\n📈 ÚLTIMAS ESTATÍSTICAS (1h):")
            print(f"Temperatura média: {db_stats['avg_temp']:.1f}°C")
            print(f"Umidade média: {db_stats['avg_humidity']:.1f}%")
            print(f"pH médio: {db_stats['avg_ph']:.1f}")
            print(f"Eventos de irrigação: {db_stats['irrigation_count']}")
            print("="*60)

    def generate_report(self, hours: int = 24) -> dict:
        """
        Gera relatório analítico

        Args:
            hours: Período para análise

        Returns:
            Dicionário com relatório completo
        """
        stats = self.database.get_statistics(hours)
        alerts = self.database.get_active_alerts()
        irrigation_history = self.database.get_irrigation_history(days=1)

        report = {
            'period_hours': hours,
            'generated_at': datetime.now().isoformat(),
            'sensor_statistics': stats,
            'active_alerts': len(alerts),
            'alert_details': alerts[:5],  # Top 5 alertas
            'irrigation_events': len(irrigation_history),
            'pipeline_stats': self.stats.copy()
        }

        return report


def signal_handler(sig, frame):
    """Handler para Ctrl+C"""
    print("\n\nInterrompido pelo usuário...")
    sys.exit(0)


def main():
    """Função principal"""

    # Configurações
    SERIAL_PORT = None  # None para usar simulador, ou '/dev/ttyUSB0' para hardware real
    DB_PATH = "soil_monitoring.db"

    # Configura handler de sinal
    signal.signal(signal.SIGINT, signal_handler)

    # Cria e inicia pipeline
    pipeline = DataPipeline(serial_port=SERIAL_PORT, db_path=DB_PATH)

    if not pipeline.start():
        logger.error("Falha ao iniciar pipeline")
        return

    print("\n" + "="*60)
    print("🌱 PIPELINE DE MONITORAMENTO DE SOLO")
    print("="*60)
    print(f"Modo: {'SIMULADOR' if SERIAL_PORT is None else 'HARDWARE REAL'}")
    print(f"Banco de dados: {DB_PATH}")
    print("\nCapturando dados... (Ctrl+C para parar)")
    print("="*60 + "\n")

    try:
        # Mantém o programa rodando
        while True:
            time.sleep(60)

            # Gera mini-relatório a cada minuto
            report = pipeline.generate_report(hours=1)
            print(f"\n📊 Mini-relatório: {report['sensor_statistics']['total_readings']} leituras na última hora")

    except KeyboardInterrupt:
        pass
    finally:
        pipeline.stop()

        # Gera relatório final
        print("\n📄 GERANDO RELATÓRIO FINAL...")
        report = pipeline.generate_report(hours=24)

        # Salva relatório em arquivo
        report_file = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Relatório salvo em: {report_file}")


if __name__ == "__main__":
    main()