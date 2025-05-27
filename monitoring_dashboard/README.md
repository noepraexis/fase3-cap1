# Dashboard de Monitoramento de Solo

Dashboard interativo em Streamlit para visualização em tempo real dos dados do sistema de irrigação inteligente ESP32.

## 🚀 Início Rápido

```bash
# Modo demonstração (recomendado para teste)
python dashboard_demo.py

# Ou execução direta
streamlit run dashboard.py
```

## 📋 Funcionalidades

- 📊 **Visualização em Tempo Real** - Medidores gauge para sensores
- 📈 **Gráficos Históricos** - Análise temporal dos dados
- 🚨 **Sistema de Alertas** - Notificações categorizadas
- 🔮 **Análise Preditiva** - Tendências e recomendações
- 🔄 **Auto-refresh** - Atualização automática configurável

## 🖼️ Interface

### Seções Principais

1. **Status Atual**
   - Medidores de umidade, temperatura e pH
   - Estado da bomba de irrigação
   - Níveis de nutrientes (NPK)

2. **Dados Históricos**
   - Gráficos de série temporal
   - Matriz de correlação
   - Eventos de irrigação

3. **Alertas**
   - 🔴 Críticos - Ação imediata
   - 🟡 Avisos - Monitorar
   - 🔵 Informativos - Conhecimento

4. **Análise**
   - Estatísticas do período
   - Tendências identificadas
   - Recomendações automáticas

## 🔧 Instalação

### Requisitos
- Python 3.8+
- Streamlit 1.28+

### Passos

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar dashboard
streamlit run dashboard.py
```

## 💻 Uso

### Configurações

**Barra Lateral:**
- Período: 1h, 6h, 24h, 7d, 30d
- Auto-refresh: 5-60 segundos
- Estatísticas do sistema

### Modo Demonstração

Para testar sem hardware:

```bash
python dashboard_demo.py
```

Isso irá:
- Gerar dados simulados de 24h
- Popular banco de teste
- Abrir dashboard automaticamente

## 🔗 Integração

O dashboard se conecta ao banco SQLite em:
```
../monitoring_database/soil_monitoring.db
```

### Fluxo de Dados
```
ESP32 → monitoring_database → SQLite → Dashboard
```

## 📊 Interpretação

### Medidores Gauge
- **Verde**: Dentro da faixa ideal
- **Cinza**: Fora do ideal
- **Linha vermelha**: Limite crítico

### Faixas Ideais
| Sensor | Mínimo | Ideal | Máximo |
|--------|--------|-------|--------|
| Umidade | 30% | 40-60% | 70% |
| Temperatura | 15°C | 20-30°C | 35°C |
| pH | 6.0 | 6.0-7.0 | 8.0 |

## 🛠️ Troubleshooting

### Dashboard não abre
```bash
# Verificar porta
lsof -i :8501

# Usar porta alternativa
streamlit run dashboard.py --server.port 8502
```

### Sem dados
1. Verifique o banco: `../monitoring_database/soil_monitoring.db`
2. Execute o pipeline: `cd ../monitoring_database && python data_pipeline.py`
3. Use modo demo: `python dashboard_demo.py`

### Performance
- Limite de 1000 pontos por gráfico
- Cache de 15 minutos
- Queries otimizadas com índices

## 📁 Estrutura

```
monitoring_dashboard/
├── dashboard.py         # Dashboard principal
├── dashboard_demo.py    # Modo demonstração
├── requirements.txt     # Dependências
├── README.md           # Este arquivo
└── TECHNICAL.md        # Detalhes técnicos
```

## 📝 Documentação

- [Sistema de Captura](../monitoring_database/README.md)
- [Documentação Técnica](TECHNICAL.md)
- [Projeto Principal](../README.md)

## 📄 Licença

Projeto educacional - FIAP 2025