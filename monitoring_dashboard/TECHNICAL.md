# Documentação Técnica - Dashboard de Monitoramento

## 📋 Visão Geral Técnica

Este documento detalha a implementação técnica do dashboard Streamlit para visualização de dados do sistema de monitoramento de solo.

## 🏗️ Arquitetura

### Fluxo de Dados

```
SQLite Database
      │
      ▼
┌─────────────────┐
│ DashboardApp    │
│   __init__()    │──────> Session State
│   get_data()    │        Management
│   render()      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Streamlit UI    │
│ - Sidebar       │
│ - Main Area     │
│ - Components    │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Plotly Charts   │
│ - Gauge         │
│ - Time Series   │
│ - Correlation   │
└─────────────────┘
```

## 📦 Componentes Principais

### 1. **DashboardApp Class**

Classe principal que gerencia todo o dashboard:

```python
class DashboardApp:
    def __init__(self):
        self.db_path = Path("../monitoring_database/soil_monitoring.db")
        self.init_session_state()
    
    def init_session_state(self):
        # Gerencia estado persistente entre reloads
        
    def get_connection(self):
        # Conexão segura com SQLite
        
    def load_sensor_data(self, hours=1):
        # Carrega dados com período configurável
```

### 2. **Visualizações**

#### Gauge Charts (Medidores)
```python
def create_gauge_chart(self, value, title, min_val, max_val, 
                      optimal_range=None, unit=""):
    # Usa plotly.graph_objects.Indicator
    # Suporta faixas ideais visuais
    # Threshold de alerta em 90%
```

#### Time Series (Séries Temporais)
```python
def create_time_series_chart(self, df, columns, title):
    # Múltiplas séries no mesmo gráfico
    # Rangeslider para zoom
    # Hover unificado
```

#### Correlation Matrix (Matriz de Correlação)
```python
# Usa plotly.express.imshow
# Escala de cores RdBu
# Valores de correlação visíveis
```

### 3. **Sistema de Cache**

O Streamlit implementa cache automático:

```python
@st.cache_data(ttl=900)  # 15 minutos
def load_data():
    # Queries pesadas são cacheadas
```

## 🗄️ Queries SQL

### Otimizações Implementadas

1. **Índices**
   ```sql
   CREATE INDEX idx_sensor_timestamp ON sensor_readings(timestamp);
   CREATE INDEX idx_alerts_severity ON alerts(severity, resolved);
   ```

2. **Queries com Limite**
   ```sql
   SELECT * FROM sensor_readings 
   WHERE timestamp > datetime('now', '-N hours')
   ORDER BY timestamp DESC
   LIMIT 1000;  -- Previne sobrecarga
   ```

3. **Agregações Eficientes**
   ```sql
   SELECT 
       AVG(temperature) as avg_temp,
       MIN(temperature) as min_temp,
       MAX(temperature) as max_temp
   FROM sensor_readings
   WHERE timestamp >= datetime('now', '-24 hours');
   ```

## 🎨 Customização CSS

### Estilos Inline
```css
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #2E7D32;
}

.alert-critical {
    background-color: #ffebee;
    border-left: 5px solid #f44336;
}
```

### Classes de Status
- `.status-on`: Verde (#4caf50)
- `.status-off`: Vermelho (#f44336)
- `.alert-warning`: Amarelo (#ff9800)

## 🔄 Auto-refresh

### Implementação

```python
if st.session_state.auto_refresh:
    time.sleep(st.session_state.refresh_interval)
    st.rerun()
```

### Limitações
- Mínimo: 5 segundos (previne sobrecarga)
- Máximo: 60 segundos
- Desabilitado por padrão

## 📊 Análise Preditiva

### Cálculo de Tendências

```python
# Regressão linear simples
humidity_trend = np.polyfit(range(len(df)), df['humidity'], 1)[0]

# Interpretação
if humidity_trend > 0:
    trend = "↑ Aumentando"
else:
    trend = "↓ Diminuindo"
```

### Previsão de Irrigação

```python
# Taxa de perda de umidade
humidity_rate = (current - previous) / time_delta

# Estimativa até threshold
hours_to_irrigation = (current_humidity - 40) / abs(humidity_rate)
```

## 🚀 Performance

### Otimizações

1. **Limitação de Dados**
   - Máximo 1000 pontos por gráfico
   - Downsampling para períodos longos

2. **Queries Assíncronas**
   - Usa threading para não bloquear UI
   - Connection pooling do SQLite

3. **Lazy Loading**
   - Abas carregam sob demanda
   - Componentes pesados com placeholder

### Métricas

- **Tempo de Carregamento**: < 2s
- **Uso de Memória**: < 100MB
- **CPU**: < 10% em idle

## 🔒 Segurança

### Validações

1. **SQL Injection**
   - Parâmetros sempre escapados
   - Uso de prepared statements

2. **Path Traversal**
   - Paths absolutos validados
   - Sem input direto do usuário

3. **Session State**
   - Isolado por usuário
   - Sem dados sensíveis

## 🐛 Debug

### Logs Detalhados

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Adicionar em pontos críticos:
logger.debug(f"Query executada: {query}")
logger.info(f"Dados carregados: {len(df)} registros")
```

### Modo Desenvolvimento

```bash
# Ativa reloading automático
streamlit run dashboard.py --server.runOnSave true

# Debug detalhado
streamlit run dashboard.py --logger.level debug
```

## 🔧 Configurações Avançadas

### Config.toml

Criar `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#2E7D32"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"

[server]
maxUploadSize = 10
enableCORS = false

[browser]
gatherUsageStats = false
```

### Variáveis de Ambiente

```bash
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_THEME_BASE="light"
```

## 📦 Dependências

### Versões Críticas

```
streamlit>=1.28.0    # Suporte st.rerun()
plotly>=5.18.0       # Gauge charts
pandas>=2.0.0        # Datetime handling
numpy>=1.24.0        # Cálculos estatísticos
```

### Compatibilidade

- Python: 3.8-3.11
- OS: Windows, macOS, Linux
- Browsers: Chrome 90+, Firefox 88+, Safari 14+

## 🚧 Limitações Conhecidas

1. **SQLite Concorrência**
   - Write locks podem causar delays
   - Solução: Migrar para PostgreSQL

2. **Streamlit State**
   - Rerun limpa variáveis locais
   - Usar st.session_state sempre

3. **Plotly Rendering**
   - Muitos pontos = lento
   - Implementar agregação server-side

## 🔮 Roadmap Técnico

### v2.0
- WebSocket para real-time
- Redis para cache distribuído
- Docker deployment

### v3.0
- Multi-tenancy
- API GraphQL
- PWA support

---

**Última atualização**: Janeiro 2025  
**Mantenedor**: FarmTech Solutions Dev Team