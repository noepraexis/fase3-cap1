#!/usr/bin/env python3
"""
Serial Reader para ESP32 - Sistema de Monitoramento de Solo
Captura dados do monitor serial e processa telemetria JSON
"""

import serial
import json
import time
import logging
from datetime import datetime
from typing import Dict, Optional
import sys
import threading
from queue import Queue

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ESP32SerialReader:
    """Classe para leitura de dados seriais do ESP32"""

    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200):
        """
        Inicializa o leitor serial

        Args:
            port: Porta serial (ex: COM3 no Windows, /dev/ttyUSB0 no Linux)
            baudrate: Taxa de transmissão (deve corresponder ao ESP32)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.data_queue = Queue()
        self.running = False
        self.reader_thread = None

    def connect(self) -> bool:
        """Estabelece conexão com o ESP32"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            logger.info(f"Conectado ao ESP32 na porta {self.port}")
            return True
        except serial.SerialException as e:
            logger.error(f"Erro ao conectar: {e}")
            return False

    def disconnect(self):
        """Fecha a conexão serial"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("Conexão serial fechada")

    def parse_telemetry(self, line: str) -> Optional[Dict]:
        """
        Processa linha de telemetria JSON do ESP32

        Args:
            line: Linha recebida do serial

        Returns:
            Dicionário com dados parseados ou None se inválido
        """
        # Procura por JSON na linha (formato: {...})
        start_idx = line.find('{')
        end_idx = line.rfind('}')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = line[start_idx:end_idx + 1]
            try:
                data = json.loads(json_str)
                # Adiciona timestamp local
                data['timestamp_local'] = datetime.now().isoformat()
                return data
            except json.JSONDecodeError as e:
                logger.debug(f"JSON inválido: {e}")
                return None
        return None

    def _reader_worker(self):
        """Thread worker para leitura contínua"""
        logger.info("Thread de leitura iniciada")

        while self.running:
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    if self.serial_conn.in_waiting > 0:
                        line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()

                        if line:
                            # Log de debug para todas as linhas
                            logger.debug(f"Serial RX: {line}")

                            # Tenta parsear como telemetria JSON
                            data = self.parse_telemetry(line)
                            if data:
                                logger.info(f"Telemetria recebida: sensores={data.get('sensors', {})}")
                                self.data_queue.put(data)
                            # Procura por logs específicos do ESP32
                            elif "[INFO]" in line or "[WARN]" in line or "[ERROR]" in line:
                                logger.info(f"ESP32 Log: {line}")

            except Exception as e:
                logger.error(f"Erro na leitura: {e}")
                time.sleep(0.1)

        logger.info("Thread de leitura finalizada")

    def start_reading(self):
        """Inicia leitura assíncrona em thread separada"""
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("Conexão serial não estabelecida")
            return False

        self.running = True
        self.reader_thread = threading.Thread(target=self._reader_worker)
        self.reader_thread.daemon = True
        self.reader_thread.start()
        logger.info("Leitura serial iniciada")
        return True

    def stop_reading(self):
        """Para a leitura assíncrona"""
        self.running = False
        if self.reader_thread:
            self.reader_thread.join(timeout=2.0)
        logger.info("Leitura serial parada")

    def get_data(self, timeout: float = 1.0) -> Optional[Dict]:
        """
        Obtém próximo dado da fila

        Args:
            timeout: Tempo máximo de espera

        Returns:
            Dados telemetria ou None se timeout
        """
        try:
            return self.data_queue.get(timeout=timeout)
        except:
            return None


def simulate_esp32_data() -> Dict:
    """
    Simula dados do ESP32 para testes sem hardware

    Returns:
        Dicionário com estrutura idêntica à telemetria real
    """
    import random

    return {
        "sensors": {
            "temperature": round(20 + random.uniform(-5, 10), 1),
            "humidity": round(40 + random.uniform(-20, 30), 1),
            "ph": round(6.5 + random.uniform(-1.5, 1.5), 1),
            "phosphorus": random.choice([True, False]),
            "potassium": random.choice([True, False]),
            "timestamp": int(time.time() * 1000)
        },
        "irrigation": {
            "active": random.choice([True, False]),
            "uptime": random.randint(0, 300),
            "dailyActivations": random.randint(0, 10),
            "threshold": 30.0
        },
        "system": {
            "freeHeap": random.randint(100000, 200000),
            "uptime": random.randint(0, 86400),
            "wifi": "Connected"
        },
        "timestamp_local": datetime.now().isoformat()
    }


def main():
    """Função principal para teste do leitor serial"""

    # Configurações
    SERIAL_PORT = '/dev/ttyUSB0'  # Ajuste conforme sua porta
    USE_SIMULATOR = True  # True para usar simulador

    if not USE_SIMULATOR:
        # Modo real - conexão com ESP32
        reader = ESP32SerialReader(port=SERIAL_PORT)

        if not reader.connect():
            logger.error("Falha na conexão. Verifique a porta serial.")
            sys.exit(1)

        try:
            reader.start_reading()
            logger.info("Lendo dados do ESP32... (Ctrl+C para parar)")

            while True:
                data = reader.get_data(timeout=2.0)
                if data:
                    print("\n" + "="*60)
                    print(json.dumps(data, indent=2))
                    print("="*60)

        except KeyboardInterrupt:
            logger.info("\nParando leitura...")
        finally:
            reader.stop_reading()
            reader.disconnect()

    else:
        # Modo simulador
        logger.info("Modo simulador ativado")
        logger.info("Gerando dados simulados... (Ctrl+C para parar)")

        try:
            while True:
                data = simulate_esp32_data()
                print("\n" + "="*60)
                print(json.dumps(data, indent=2))
                print("="*60)
                time.sleep(2)  # Simula taxa de atualização

        except KeyboardInterrupt:
            logger.info("\nSimulação parada")


if __name__ == "__main__":
    main()