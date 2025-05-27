#!/bin/bash
# Script para executar o sistema de monitoramento

echo "🌱 SISTEMA DE MONITORAMENTO DE SOLO"
echo "===================================="
echo ""

# Verifica se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado!"
    echo "   Instale com: sudo apt install python3 python3-pip"
    exit 1
fi

# Menu de opções
echo "Selecione uma opção:"
echo "1) Configurar sistema (primeira vez)"
echo "2) Executar captura de dados (modo simulador)"
echo "3) Executar captura de dados (hardware real)"
echo "4) Testar operações CRUD"
echo "5) Visualizar dashboard"
echo "6) Sair"
echo ""

read -p "Opção: " choice

case $choice in
    1)
        echo "🔧 Executando configuração..."
        python3 setup.py
        ;;
    2)
        echo "🤖 Iniciando captura em modo simulador..."
        python3 data_pipeline.py
        ;;
    3)
        echo "📡 Iniciando captura com hardware real..."
        echo "Digite a porta serial (ex: /dev/ttyUSB0):"
        read -p "Porta: " port
        # Modifica temporariamente o data_pipeline.py para usar a porta
        sed -i.bak "s/SERIAL_PORT = None/SERIAL_PORT = '$port'/g" data_pipeline.py
        python3 data_pipeline.py
        # Restaura o arquivo original
        mv data_pipeline.py.bak data_pipeline.py
        ;;
    4)
        echo "🧪 Executando testes CRUD..."
        python3 test_crud.py
        ;;
    5)
        echo "📊 Abrindo dashboard..."
        echo "Navegue para: ../monitoring_dashboard"
        echo "Execute: streamlit run dashboard.py"
        cd ../monitoring_dashboard && streamlit run dashboard.py
        ;;
    6)
        echo "👋 Até logo!"
        exit 0
        ;;
    *)
        echo "❌ Opção inválida!"
        exit 1
        ;;
esac