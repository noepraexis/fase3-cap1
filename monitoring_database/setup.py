#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Configuração e Inicialização
======================================

Prepara o ambiente e inicializa o sistema de monitoramento de solo.

Funcionalidades:
- Verifica dependências
- Cria estrutura de diretórios
- Inicializa banco de dados
- Configura permissões
- Valida conexão serial
- Executa testes básicos
"""

import os
import sys
import subprocess
import platform
import sqlite3
import json
from pathlib import Path
import serial.tools.list_ports
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemSetup:
    """Classe para configuração do sistema"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.db_path = self.base_dir / "soil_monitoring.db"
        self.reports_dir = self.base_dir / "reports"
        self.logs_dir = self.base_dir / "logs"

    def check_python_version(self):
        """Verifica versão do Python"""
        print("🐍 Verificando versão do Python...")

        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            logger.error("Python 3.8+ é necessário")
            return False

        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True

    def check_dependencies(self):
        """Verifica dependências instaladas"""
        print("\n📦 Verificando dependências...")

        required_packages = [
            'serial',
            'sqlite3',
            'pandas',
            'numpy'
        ]

        missing = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"   ✅ {package}")
            except ImportError:
                missing.append(package)
                print(f"   ❌ {package}")

        if missing:
            print(f"\n❗ Pacotes faltando: {', '.join(missing)}")
            print("   Execute: pip install -r requirements.txt")
            return False

        return True

    def create_directories(self):
        """Cria estrutura de diretórios"""
        print("\n📁 Criando estrutura de diretórios...")

        dirs = [self.reports_dir, self.logs_dir]

        for dir_path in dirs:
            if not dir_path.exists():
                dir_path.mkdir(parents=True)
                print(f"   ✅ Criado: {dir_path}")
            else:
                print(f"   ℹ️  Existente: {dir_path}")

        return True

    def initialize_database(self):
        """Inicializa o banco de dados"""
        print("\n🗄️  Inicializando banco de dados...")

        try:
            # Importa o gerenciador de banco
            from database_manager import SoilMonitorDatabase

            # Cria instância
            db = SoilMonitorDatabase(str(self.db_path))

            # Testa conexão
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

            print(f"   ✅ Banco criado: {self.db_path}")
            print(f"   📊 Tabelas criadas: {len(tables)}")

            for table in tables:
                print(f"      - {table[0]}")

            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar banco: {e}")
            return False

    def check_serial_ports(self):
        """Lista portas seriais disponíveis"""
        print("\n🔌 Verificando portas seriais...")

        ports = serial.tools.list_ports.comports()

        if not ports:
            print("   ⚠️  Nenhuma porta serial detectada")
            print("   ℹ️  O sistema funcionará em modo simulador")
            return True

        print(f"   📡 {len(ports)} porta(s) encontrada(s):")

        for port in ports:
            print(f"      - {port.device}: {port.description}")

            # Tenta identificar ESP32
            if "USB" in port.device or "tty" in port.device:
                if "CP210" in port.description or "CH340" in port.description:
                    print(f"        🎯 Possível ESP32 detectado!")

        return True

    def test_components(self):
        """Testa componentes do sistema"""
        print("\n🧪 Testando componentes...")

        # Testa serial reader
        try:
            from serial_reader import simulate_esp32_data
            data = simulate_esp32_data()
            print("   ✅ Serial Reader (simulador)")
        except Exception as e:
            print(f"   ❌ Serial Reader: {e}")
            return False

        # Testa database manager
        try:
            from database_manager import SoilMonitorDatabase
            db = SoilMonitorDatabase(str(self.db_path))
            print("   ✅ Database Manager")
        except Exception as e:
            print(f"   ❌ Database Manager: {e}")
            return False

        # Testa data pipeline
        try:
            from data_pipeline import DataPipeline
            print("   ✅ Data Pipeline")
        except Exception as e:
            print(f"   ❌ Data Pipeline: {e}")
            return False

        return True

    def create_config_file(self):
        """Cria arquivo de configuração padrão"""
        print("\n⚙️  Criando arquivo de configuração...")

        config = {
            "serial": {
                "port": None,  # None para simulador
                "baudrate": 115200,
                "timeout": 1.0
            },
            "database": {
                "path": "soil_monitoring.db",
                "cleanup_days": 30
            },
            "monitoring": {
                "update_interval": 2,
                "alert_thresholds": {
                    "temperature_min": 15,
                    "temperature_max": 35,
                    "humidity_min": 30,
                    "humidity_max": 70,
                    "ph_min": 6.0,
                    "ph_max": 8.0
                }
            }
        }

        config_path = self.base_dir / "config.json"

        if not config_path.exists():
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"   ✅ Criado: {config_path}")
        else:
            print(f"   ℹ️  Existente: {config_path}")

        return True

    def display_instructions(self):
        """Exibe instruções de uso"""
        print("\n" + "="*60)
        print("🎉 CONFIGURAÇÃO CONCLUÍDA!")
        print("="*60)

        print("\n📚 PRÓXIMOS PASSOS:")
        print("\n1. Para capturar dados do ESP32:")
        print("   python data_pipeline.py")

        print("\n2. Para visualizar o dashboard:")
        print("   cd ../monitoring_dashboard")
        print("   streamlit run dashboard.py")

        print("\n3. Para modo demonstração:")
        print("   cd ../monitoring_dashboard")
        print("   python dashboard_demo.py")

        print("\n4. Para testar CRUD:")
        print("   python test_crud.py")

        print("\n📡 CONFIGURAÇÃO SERIAL:")
        if platform.system() == "Linux":
            print("   - Porta típica: /dev/ttyUSB0 ou /dev/ttyACM0")
            print("   - Permissões: sudo usermod -a -G dialout $USER")
        elif platform.system() == "Windows":
            print("   - Porta típica: COM3, COM4, etc.")
            print("   - Instale drivers CH340 ou CP2102 se necessário")
        elif platform.system() == "Darwin":  # macOS
            print("   - Porta típica: /dev/tty.usbserial-*")

        print("\n💡 DICAS:")
        print("   - Use o modo simulador para testes sem hardware")
        print("   - Monitore os logs em ./logs/ para depuração")
        print("   - Relatórios são salvos em ./reports/")
        print("\n" + "="*60)

    def run(self):
        """Executa todas as etapas de configuração"""
        print("="*60)
        print("🌱 SISTEMA DE MONITORAMENTO DE SOLO - SETUP")
        print("="*60)

        steps = [
            ("Versão Python", self.check_python_version),
            ("Dependências", self.check_dependencies),
            ("Diretórios", self.create_directories),
            ("Banco de Dados", self.initialize_database),
            ("Portas Seriais", self.check_serial_ports),
            ("Componentes", self.test_components),
            ("Configuração", self.create_config_file)
        ]

        for step_name, step_func in steps:
            if not step_func():
                print(f"\n❌ Erro na etapa: {step_name}")
                print("   Corrija o problema e execute novamente.")
                return False

        self.display_instructions()
        return True


def main():
    """Função principal"""
    setup = SystemSetup()

    try:
        success = setup.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()