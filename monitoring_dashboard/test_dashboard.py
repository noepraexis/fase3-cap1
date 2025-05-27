#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste do Dashboard
============================

Valida a integridade do dashboard e suas dependências.

Autor: FarmTech Solutions
Data: Janeiro 2025
"""

import sys
import os
import sqlite3
from pathlib import Path

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    print("🔍 Verificando dependências...")
    
    required = {
        'streamlit': 'streamlit',
        'plotly': 'plotly',
        'pandas': 'pandas',
        'numpy': 'numpy'
    }
    
    missing = []
    for name, module in required.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            missing.append(name)
            print(f"   ❌ {name}")
    
    if missing:
        print("\n❗ Instale as dependências com:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def check_database():
    """Verifica se o banco de dados existe e tem dados"""
    print("\n🗄️  Verificando banco de dados...")
    
    db_path = Path("../monitoring_database/soil_monitoring.db")
    
    if not db_path.exists():
        print(f"   ❌ Banco não encontrado: {db_path}")
        print("   Execute primeiro: cd ../monitoring_database && python setup.py")
        return False
    
    print(f"   ✅ Banco encontrado: {db_path}")
    
    # Verifica tabelas
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tables = ['sensor_readings', 'irrigation_events', 'alerts']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   📊 {table}: {count} registros")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao acessar banco: {e}")
        return False

def check_dashboard_files():
    """Verifica se os arquivos do dashboard existem"""
    print("\n📁 Verificando arquivos...")
    
    required_files = [
        'dashboard.py',
        'dashboard_demo.py',
        'requirements.txt',
        'README.md',
        'TECHNICAL.md'
    ]
    
    missing = []
    for file in required_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            missing.append(file)
            print(f"   ❌ {file}")
    
    return len(missing) == 0

def test_dashboard_import():
    """Testa importação do dashboard"""
    print("\n🧪 Testando importação do dashboard...")
    
    try:
        # Adiciona diretório ao path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Tenta importar
        from dashboard import DashboardApp
        print("   ✅ Dashboard importado com sucesso")
        
        # Testa criação de instância
        app = DashboardApp()
        print("   ✅ Instância criada com sucesso")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao importar: {e}")
        return False

def main():
    """Função principal"""
    print("="*60)
    print("🌱 TESTE DO DASHBOARD DE MONITORAMENTO")
    print("="*60)
    
    tests = [
        ("Dependências", check_dependencies),
        ("Banco de Dados", check_database),
        ("Arquivos", check_dashboard_files),
        ("Importação", test_dashboard_import)
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 Dashboard pronto para uso!")
        print("\nExecute:")
        print("  streamlit run dashboard.py      # Com dados reais")
        print("  python dashboard_demo.py        # Modo demonstração")
    else:
        print("\n⚠️  Corrija os erros antes de executar o dashboard")
        sys.exit(1)

if __name__ == "__main__":
    main()