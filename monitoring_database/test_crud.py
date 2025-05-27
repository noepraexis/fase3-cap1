#!/usr/bin/env python3
"""
Script de Teste para Operações CRUD
Demonstra todas as operações do banco de dados
"""

import time
import json
from datetime import datetime, timedelta
from database_manager import SoilMonitorDatabase

def print_section(title):
    """Imprime seção formatada"""
    print(f"\n{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}\n")

def test_crud_operations():
    """Testa todas as operações CRUD"""

    # Inicializa banco
    db = SoilMonitorDatabase("test_crud.db")

    print_section("TESTE DE OPERAÇÕES CRUD")

    # ============ CREATE ============
    print_section("1. CREATE - Inserindo Dados")

    # Dados de teste
    test_data = [
        {
            "sensors": {
                "temperature": 25.5,
                "humidity": 45.0,
                "ph": 6.8,
                "phosphorus": True,
                "potassium": False,
                "timestamp": int(time.time() * 1000)
            },
            "irrigation": {
                "active": False,
                "uptime": 0,
                "dailyActivations": 0
            },
            "system": {
                "freeHeap": 150000,
                "uptime": 3600,
                "wifi": "Connected"
            }
        },
        {
            "sensors": {
                "temperature": 32.0,  # Alta temperatura
                "humidity": 25.0,     # Baixa umidade
                "ph": 5.5,           # pH baixo
                "phosphorus": False,
                "potassium": True,
                "timestamp": int(time.time() * 1000) + 1000
            },
            "irrigation": {
                "active": True,
                "uptime": 120,
                "dailyActivations": 1
            },
            "system": {
                "freeHeap": 145000,
                "uptime": 3720,
                "wifi": "Connected"
            }
        },
        {
            "sensors": {
                "temperature": 18.0,
                "humidity": 65.0,
                "ph": 7.2,
                "phosphorus": True,
                "potassium": True,
                "timestamp": int(time.time() * 1000) + 2000
            },
            "irrigation": {
                "active": False,
                "uptime": 0,
                "dailyActivations": 1
            },
            "system": {
                "freeHeap": 148000,
                "uptime": 3840,
                "wifi": "Connected"
            }
        }
    ]

    inserted_ids = []

    for i, data in enumerate(test_data):
        # Insere leitura de sensores
        reading_id = db.insert_sensor_reading(data)
        inserted_ids.append(reading_id)
        print(f"✅ Leitura #{i+1} inserida - ID: {reading_id}")

        # Insere estatísticas do sistema
        stats_id = db.insert_system_stats(data)
        print(f"   Estatísticas do sistema - ID: {stats_id}")

        # Simula evento de irrigação
        if i == 0:  # Início da irrigação
            event_id = db.insert_irrigation_event(
                event_type="start",
                trigger="auto",
                moisture=data['sensors']['humidity']
            )
            print(f"   🚿 Evento irrigação START - ID: {event_id}")
        elif i == 2:  # Fim da irrigação
            event_id = db.insert_irrigation_event(
                event_type="stop",
                duration=120,
                trigger="auto",
                moisture=data['sensors']['humidity']
            )
            print(f"   💧 Evento irrigação STOP - ID: {event_id}")

    # ============ READ ============
    print_section("2. READ - Consultando Dados")

    # Consulta últimas leituras
    print("📊 Últimas 5 leituras:")
    readings = db.get_latest_readings(5)
    for reading in readings:
        print(f"   ID {reading['id']}: Temp={reading['temperature']}°C, "
              f"Umidade={reading['humidity']}%, pH={reading['ph']}")

    # Consulta por período
    print("\n📅 Leituras do último minuto:")
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=1)
    period_readings = db.get_readings_by_period(
        start_time.strftime('%Y-%m-%d %H:%M:%S'),
        end_time.strftime('%Y-%m-%d %H:%M:%S')
    )
    print(f"   Encontradas {len(period_readings)} leituras")

    # Histórico de irrigação
    print("\n💧 Histórico de irrigação (7 dias):")
    irrigation_events = db.get_irrigation_history(7)
    for event in irrigation_events:
        duration = event.get('duration_seconds', 'N/A')
        print(f"   {event['event_type'].upper()}: {event['timestamp']} "
              f"(duração: {duration}s)")

    # Alertas ativos
    print("\n⚠️  Alertas ativos:")
    alerts = db.get_active_alerts()
    if alerts:
        for alert in alerts:
            print(f"   [{alert['severity'].upper()}] {alert['message']}")
    else:
        print("   Nenhum alerta ativo")

    # Estatísticas
    print("\n📈 Estatísticas (últimas 24h):")
    stats = db.get_statistics(24)
    print(f"   Temperatura: {stats['avg_temp']:.1f}°C "
          f"(min: {stats['min_temp']:.1f}, max: {stats['max_temp']:.1f})")
    print(f"   Umidade: {stats['avg_humidity']:.1f}% "
          f"(min: {stats['min_humidity']:.1f}, max: {stats['max_humidity']:.1f})")
    print(f"   pH: {stats['avg_ph']:.1f} "
          f"(min: {stats['min_ph']:.1f}, max: {stats['max_ph']:.1f})")
    print(f"   Total de leituras: {stats['total_readings']}")
    print(f"   Eventos de irrigação: {stats['irrigation_count']}")

    # ============ UPDATE ============
    print_section("3. UPDATE - Atualizando Dados")

    if inserted_ids:
        # Atualiza primeira leitura
        update_id = inserted_ids[0]
        print(f"🔄 Atualizando leitura ID {update_id}...")

        # Valores antes
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT temperature, humidity FROM sensor_readings WHERE id = ?",
                         (update_id,))
            before = cursor.fetchone()
            print(f"   Antes: Temp={before[0]}°C, Umidade={before[1]}%")

        # Atualiza
        success = db.update_sensor_reading(
            update_id,
            temperature=28.5,
            humidity=50.0
        )

        if success:
            # Valores depois
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT temperature, humidity FROM sensor_readings WHERE id = ?",
                             (update_id,))
                after = cursor.fetchone()
                print(f"   Depois: Temp={after[0]}°C, Umidade={after[1]}%")
                print("   ✅ Atualização bem-sucedida!")
        else:
            print("   ❌ Falha na atualização")

    # Resolve alertas
    print("\n🔧 Resolvendo alertas...")
    alerts = db.get_active_alerts()
    if alerts:
        alert_id = alerts[0]['id']
        success = db.resolve_alert(alert_id, "Problema corrigido manualmente")
        if success:
            print(f"   ✅ Alerta ID {alert_id} resolvido")
    else:
        print("   Nenhum alerta para resolver")

    # ============ DELETE ============
    print_section("4. DELETE - Removendo Dados")

    # Remove uma leitura específica
    if len(inserted_ids) > 2:
        delete_id = inserted_ids[-1]
        print(f"🗑️  Removendo leitura ID {delete_id}...")
        success = db.delete_reading(delete_id)
        if success:
            print("   ✅ Leitura removida com sucesso")
        else:
            print("   ❌ Falha na remoção")

    # Simula limpeza de dados antigos
    print("\n🧹 Limpando dados antigos...")
    # Insere dados "antigos" para teste
    with db.get_connection() as conn:
        cursor = conn.cursor()
        old_date = (datetime.now() - timedelta(days=40)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO sensor_readings
            (timestamp, temperature, humidity, ph, phosphorus, potassium, created_at)
            VALUES (?, 20, 50, 7, 0, 0, ?)
        """, (old_date, old_date))

    # Remove dados > 30 dias
    deleted = db.delete_old_readings(30)
    print(f"   {deleted} registros antigos removidos")

    # ============ RESUMO ============
    print_section("RESUMO FINAL")

    # Conta registros finais
    with db.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        sensor_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM irrigation_events")
        irrigation_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM system_stats")
        stats_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM alerts WHERE resolved = 0")
        alert_count = cursor.fetchone()[0]

    print(f"📊 Total de registros no banco:")
    print(f"   Leituras de sensores: {sensor_count}")
    print(f"   Eventos de irrigação: {irrigation_count}")
    print(f"   Estatísticas do sistema: {stats_count}")
    print(f"   Alertas ativos: {alert_count}")

    print("\n✅ Teste CRUD concluído com sucesso!")

    # Gera arquivo de exemplo JSON
    print("\n📄 Gerando arquivo de exemplo...")
    example_data = {
        "latest_readings": db.get_latest_readings(3),
        "statistics": db.get_statistics(24),
        "irrigation_history": db.get_irrigation_history(1),
        "active_alerts": db.get_active_alerts()
    }

    with open("crud_test_results.json", "w") as f:
        json.dump(example_data, f, indent=2, default=str)

    print("   Arquivo 'crud_test_results.json' criado")


if __name__ == "__main__":
    test_crud_operations()