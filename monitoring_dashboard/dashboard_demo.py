#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Demonstração do Dashboard
===================================

Script para popular o banco de dados com dados de demonstração
e executar o dashboard em modo demo.

Uso:
    python dashboard_demo.py

Autor: FarmTech Solutions
Data: Janeiro 2025
"""

import sqlite3
import random
import pandas as pd
from datetime import datetime, timedelta
import subprocess
import time
import sys
from pathlib import Path

def create_demo_data():
    """Cria dados de demonstração no banco de dados"""
    print("🔧 Criando dados de demonstração...")
    
    # Usa o banco no diretório correto
    db_path = '../monitoring_database/soil_monitoring.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Limpa dados existentes
    tables = ['sensor_readings', 'irrigation_events', 'alerts']
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
        except sqlite3.OperationalError:
            # Tabela pode não existir ainda
            pass
    
    # Gera dados para últimas 24 horas
    start_time = datetime.now() - timedelta(hours=24)
    current_time = start_time
    
    humidity = 50.0
    temperature = 25.0
    ph_value = 6.5
    nitrogen = 30.0
    phosphorus = 40.0
    potassium = 35.0
    pump_state = False
    
    readings_data = []
    irrigation_events = []
    alerts_data = []
    
    while current_time < datetime.now():
        # Simula variações realistas
        humidity += random.uniform(-2, 2)
        humidity = max(20, min(80, humidity))
        
        temperature += random.uniform(-0.5, 0.5)
        temperature = max(15, min(35, temperature))
        
        ph_value += random.uniform(-0.1, 0.1)
        ph_value = max(5.5, min(7.5, ph_value))
        
        nitrogen += random.uniform(-1, 1)
        nitrogen = max(10, min(50, nitrogen))
        
        phosphorus += random.uniform(-1, 1)
        phosphorus = max(20, min(60, phosphorus))
        
        potassium += random.uniform(-1, 1)
        potassium = max(15, min(55, potassium))
        
        # Lógica de irrigação
        if humidity < 40 and not pump_state:
            pump_state = True
            irrigation_events.append({
                'event_time': current_time.isoformat(),
                'event_type': 'start',
                'duration_seconds': 0,
                'trigger_reason': 'Umidade baixa'
            })
        elif humidity > 55 and pump_state:
            pump_state = False
            if irrigation_events:
                duration = random.randint(60, 300)
                irrigation_events[-1]['duration_seconds'] = duration
                irrigation_events.append({
                    'event_time': current_time.isoformat(),
                    'event_type': 'stop',
                    'duration_seconds': duration,
                    'trigger_reason': 'Umidade adequada'
                })
        
        # Gera alertas ocasionais
        if random.random() < 0.05:  # 5% de chance
            alert_types = ['critical', 'warning', 'info']
            sensor_types = ['humidity', 'temperature', 'ph', 'nitrogen']
            
            alert_type = random.choice(alert_types)
            sensor_type = random.choice(sensor_types)
            
            sensor_values = {
                'humidity': humidity,
                'temperature': temperature,
                'ph': ph_value,
                'nitrogen': nitrogen
            }
            
            threshold_values = {
                'humidity': 40 if humidity < 40 else 60,
                'temperature': 20 if temperature < 20 else 30,
                'ph': 6 if ph_value < 6 else 7,
                'nitrogen': 20 if nitrogen < 20 else 40
            }
            
            messages = {
                'critical': f"{sensor_type} em nível crítico!",
                'warning': f"{sensor_type} próximo ao limite",
                'info': f"{sensor_type} requer atenção"
            }
            
            alerts_data.append({
                'alert_time': current_time.isoformat(),
                'alert_type': alert_type,
                'sensor_type': sensor_type,
                'sensor_value': sensor_values[sensor_type],
                'threshold_value': threshold_values[sensor_type],
                'message': messages[alert_type]
            })
        
        # Adiciona leitura
        readings_data.append({
            'timestamp': current_time.isoformat(),
            'humidity': round(humidity, 2),
            'temperature': round(temperature, 2),
            'ph': round(ph_value, 2),
            'phosphorus': phosphorus > 40,  # Boolean
            'potassium': potassium > 35,    # Boolean
            'esp_timestamp': int(current_time.timestamp() * 1000)
        })
        
        # Avança 5 minutos
        current_time += timedelta(minutes=5)
    
    # Insere dados no banco
    print("📊 Inserindo dados no banco...")
    
    # Sensor readings
    for reading in readings_data:
        cursor.execute("""
            INSERT INTO sensor_readings 
            (timestamp, humidity, temperature, ph, phosphorus, potassium, esp_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            reading['timestamp'], reading['humidity'], reading['temperature'],
            reading['ph'], reading['phosphorus'], reading['potassium'],
            reading['esp_timestamp']
        ))
    
    # Irrigation events
    for event in irrigation_events:
        if event['duration_seconds'] > 0:  # Apenas eventos completos
            cursor.execute("""
                INSERT INTO irrigation_events 
                (timestamp, event_type, duration_seconds, trigger_source)
                VALUES (?, ?, ?, ?)
            """, (
                event['event_time'], event['event_type'],
                event['duration_seconds'], event['trigger_reason']
            ))
    
    # Alerts
    for alert in alerts_data:
        cursor.execute("""
            INSERT INTO alerts 
            (timestamp, alert_type, severity, sensor_value, 
             threshold_value, message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            alert['alert_time'], alert['alert_type'], alert['alert_type'],
            alert['sensor_value'], alert['threshold_value'], alert['message']
        ))
    
    # System stats - removido pois agora é calculado dinamicamente
    # A tabela system_stats agora é uma view virtual no dashboard
    
    conn.commit()
    conn.close()
    
    print(f"✅ Dados de demonstração criados com sucesso!")
    print(f"   - {len(readings_data)} leituras de sensores")
    print(f"   - {len(irrigation_events)} eventos de irrigação")
    print(f"   - {len(alerts_data)} alertas")

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    print("🔍 Verificando dependências...")
    
    required_packages = ['streamlit', 'plotly', 'pandas', 'numpy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Pacotes faltando:", ", ".join(missing_packages))
        print("\nInstale com:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ Todas as dependências estão instaladas!")
    return True

def run_dashboard():
    """Executa o dashboard Streamlit"""
    print("\n🚀 Iniciando dashboard...")
    print("📊 Acesse em: http://localhost:8501")
    print("\nPressione Ctrl+C para parar\n")
    
    try:
        subprocess.run(['streamlit', 'run', 'dashboard.py'])
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard encerrado!")
    except Exception as e:
        print(f"❌ Erro ao executar dashboard: {e}")

def main():
    """Função principal"""
    print("=" * 60)
    print("🌱 Dashboard Demo - Sistema de Irrigação Inteligente")
    print("=" * 60)
    
    # Verifica dependências
    if not check_dependencies():
        sys.exit(1)
    
    # Cria dados de demonstração
    create_demo_data()
    
    print("\n" + "=" * 60)
    print("📌 INSTRUÇÕES DE USO:")
    print("=" * 60)
    print("1. O dashboard abrirá automaticamente no navegador")
    print("2. Use a barra lateral para configurar período e auto-refresh")
    print("3. Explore as diferentes abas e visualizações")
    print("4. Teste os filtros e análises disponíveis")
    print("5. Para parar, pressione Ctrl+C neste terminal")
    print("=" * 60)
    
    # Aguarda um momento
    time.sleep(2)
    
    # Executa dashboard
    run_dashboard()

if __name__ == "__main__":
    main()