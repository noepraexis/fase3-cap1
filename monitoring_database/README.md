# Sistema de Armazenamento de Dados - Entrega 2

## 📋 Descrição

Este módulo implementa a captura de dados do monitor serial do ESP32 e seu armazenamento em banco de dados SQL, cumprindo os requisitos da **Entrega 2** do projeto de monitoramento de solo.

## 🎯 Objetivos Alcançados

- ✅ Script Python que obtém dados do monitor serial do ESP32
- ✅ Armazenamento em banco de dados SQL (SQLite)
- ✅ Operações CRUD completas (Create, Read, Update, Delete)
- ✅ Justificativa do MER relacionada com a Fase 2

## 📁 Estrutura dos Arquivos

```
data_storage/
├── serial_reader.py      # Captura dados do ESP32 via serial
├── database_manager.py   # Gerenciamento do banco SQL
├── data_pipeline.py      # Pipeline integrado serial→banco
├── MER_justification.md  # Justificativa do modelo de dados
├── requirements.txt      # Dependências Python
└── README.md            # Este arquivo
```

## 🗄️ Modelo de Dados

### Tabelas Principais

1. **sensor_readings**: Leituras dos sensores (temperatura, umidade, pH, nutrientes)
2. **irrigation_events**: Eventos de irrigação (início, parada, duração)
3. **system_stats**: Estatísticas do sistema (memória, uptime, WiFi)
4. **alerts**: Alertas e anomalias detectadas

### Diagrama Simplificado

```
sensor_readings → irrigation_events → system_stats → alerts
     ↓                    ↓                ↓            ↓
   Dados              Eventos          Sistema      Notificações
```

## 🚀 Como Usar

### 1. Instalação de Dependências

```bash
pip install -r requirements.txt
```

### 2. Modo Simulador (Sem Hardware)

```bash
# Executa com dados simulados
python data_pipeline.py
```

### 3. Modo Hardware Real

```bash
# Edite data_pipeline.py e configure:
SERIAL_PORT = '/dev/ttyUSB0'  # Sua porta serial

# Execute
python data_pipeline.py
```

### 4. Operações CRUD Diretas

```python
from database_manager import SoilMonitorDatabase

# Criar instância
db = SoilMonitorDatabase()

# CREATE - Inserir dados
data = {
    "sensors": {
        "temperature": 25.5,
        "humidity": 45.2,
        "ph": 6.8,
        "phosphorus": True,
        "potassium": False
    }
}
reading_id = db.insert_sensor_reading(data)

# READ - Consultar dados
latest = db.get_latest_readings(10)
stats = db.get_statistics(24)  # Últimas 24 horas

# UPDATE - Atualizar dados
db.update_sensor_reading(reading_id, temperature=26.0)

# DELETE - Remover dados
db.delete_old_readings(30)  # Remove dados > 30 dias
```

## 📊 Funcionalidades

### Serial Reader
- Conexão automática com ESP32
- Parser de telemetria JSON
- Modo simulador para testes
- Thread assíncrona para leitura contínua
- Queue para buffer de dados

### Database Manager
- CRUD completo com validações
- Índices otimizados para consultas
- Sistema de alertas automático
- Estatísticas agregadas
- Limpeza automática de dados antigos

### Data Pipeline
- Integração serial → banco
- Detecção de mudanças de estado
- Registro automático de eventos
- Estatísticas em tempo real
- Geração de relatórios JSON

## 🔍 Exemplos de Consultas

### Últimas Leituras
```python
readings = db.get_latest_readings(limit=20)
```

### Leituras por Período
```python
readings = db.get_readings_by_period(
    start_date='2024-01-01 00:00:00',
    end_date='2024-01-31 23:59:59'
)
```

### Histórico de Irrigação
```python
events = db.get_irrigation_history(days=7)
```

### Alertas Ativos
```python
alerts = db.get_active_alerts()
```

### Estatísticas
```python
stats = db.get_statistics(hours=24)
# Retorna: média, mínimo, máximo de cada sensor
```

## 📈 Análise de Dados

O sistema detecta e alerta automaticamente:
- Temperatura: < 15°C ou > 35°C
- pH: < 6.0 ou > 8.0
- Umidade: < 30% ou > 70%

## 🔧 Configuração

### Porta Serial (Linux)
```bash
# Verificar porta
ls /dev/tty*

# Dar permissão
sudo chmod 666 /dev/ttyUSB0
```

### Porta Serial (Windows)
```python
SERIAL_PORT = 'COM3'  # Verificar no Gerenciador de Dispositivos
```

## 📝 Formato dos Dados

### Entrada (JSON do ESP32)
```json
{
  "sensors": {
    "temperature": 25.5,
    "humidity": 45.2,
    "ph": 6.8,
    "phosphorus": true,
    "potassium": false,
    "timestamp": 1704067200000
  },
  "irrigation": {
    "active": true,
    "uptime": 120,
    "dailyActivations": 3
  },
  "system": {
    "freeHeap": 145632,
    "uptime": 3600,
    "wifi": "Connected"
  }
}
```

### Saída (Relatório)
```json
{
  "period_hours": 24,
  "generated_at": "2024-01-01T12:00:00",
  "sensor_statistics": {
    "avg_temp": 25.5,
    "min_temp": 22.0,
    "max_temp": 28.5,
    "total_readings": 720
  },
  "irrigation_events": 5,
  "active_alerts": 2
}
```

## 🐛 Troubleshooting

### Erro de Porta Serial
- Verificar se ESP32 está conectado
- Confirmar porta correta com `ls /dev/tty*`
- Verificar permissões de acesso

### Banco de Dados Travado
```bash
# Remover lock se necessário
rm soil_monitor.db-journal
```

### Dados não Aparecem
- Verificar baudrate (115200)
- Confirmar formato JSON no Serial Monitor
- Habilitar logs com `logging.DEBUG`

## 🎓 Relação com MER da Fase 2

O modelo implementado expande o MER conceitual:
- **Sensores**: Agora com tipos de dados específicos
- **Temporal**: Múltiplos timestamps para rastreabilidade
- **Eventos**: Irrigação como entidade própria
- **Alertas**: Nova entidade para produção

Veja `MER_justification.md` para detalhes completos.

## 📊 Métricas de Sucesso

- Taxa de captura: > 95%
- Latência: < 100ms
- Armazenamento: ~1MB/dia
- Consultas: < 50ms

## 🚧 Próximos Passos

1. Migração para PostgreSQL para produção
2. API REST para consultas
3. Dashboard web em tempo real
4. Machine Learning para previsões
5. Integração com sistema de notificações