# Justificativa do Modelo Entidade-Relacionamento (MER)

## Sistema de Monitoramento de Solo - Estrutura de Dados

### 1. Visão Geral

O modelo de dados foi projetado para capturar, armazenar e analisar informações provenientes do sistema de monitoramento de solo baseado em ESP32. A estrutura reflete os requisitos funcionais do sistema e permite análises temporais, correlações entre variáveis e tomada de decisão baseada em dados.

### 2. Diagrama Entidade-Relacionamento

```
┌─────────────────────┐
│  sensor_readings    │
├─────────────────────┤
│ id (PK)            │
│ timestamp          │
│ temperature        │
│ humidity           │
│ ph                 │
│ phosphorus         │
│ potassium          │
│ esp_timestamp      │
│ created_at         │
└─────────────────────┘
          │
          │ 1:N
          ↓
┌─────────────────────┐
│ irrigation_events   │
├─────────────────────┤
│ id (PK)            │
│ timestamp          │
│ event_type         │
│ duration_seconds   │
│ trigger_source     │
│ moisture_level     │
│ created_at         │
└─────────────────────┘
          │
          │ 1:N
          ↓
┌─────────────────────┐
│   system_stats     │
├─────────────────────┤
│ id (PK)            │
│ timestamp          │
│ free_heap          │
│ uptime_seconds     │
│ wifi_status        │
│ irrigation_active  │
│ daily_activations  │
│ created_at         │
└─────────────────────┘
          │
          │ 1:N
          ↓
┌─────────────────────┐
│      alerts        │
├─────────────────────┤
│ id (PK)            │
│ timestamp          │
│ alert_type         │
│ severity           │
│ message            │
│ sensor_value       │
│ threshold_value    │
│ resolved           │
│ resolved_at        │
│ created_at         │
└─────────────────────┘
```

### 3. Justificativa das Entidades

#### 3.1 sensor_readings (Leituras dos Sensores)
**Propósito**: Armazenar dados brutos coletados pelos sensores em intervalos regulares.

**Campos principais**:
- `temperature`, `humidity`, `ph`: Valores numéricos dos sensores ambientais
- `phosphorus`, `potassium`: Estados booleanos dos sensores de nutrientes
- `esp_timestamp`: Timestamp do ESP32 para sincronização temporal
- `timestamp`, `created_at`: Controle temporal no servidor

**Justificativa**: Esta é a tabela central que captura o estado do solo em cada momento. A granularidade temporal permite análises de tendências e correlações.

#### 3.2 irrigation_events (Eventos de Irrigação)
**Propósito**: Registrar todas as ações do sistema de irrigação para auditoria e análise.

**Campos principais**:
- `event_type`: Tipo do evento (start, stop, error)
- `duration_seconds`: Duração da irrigação (calculada no evento stop)
- `trigger_source`: Origem do comando (manual, auto, emergency)
- `moisture_level`: Umidade no momento do evento

**Justificativa**: Permite rastrear o comportamento do sistema de irrigação, calcular consumo de água, identificar padrões de acionamento e otimizar a lógica de controle.

#### 3.3 system_stats (Estatísticas do Sistema)
**Propósito**: Monitorar a saúde e performance do sistema embarcado.

**Campos principais**:
- `free_heap`: Memória disponível (detecta vazamentos)
- `uptime_seconds`: Tempo de operação (identifica reinicializações)
- `wifi_status`: Estado da conectividade
- `irrigation_active`: Estado atual da irrigação
- `daily_activations`: Contador de ativações diárias

**Justificativa**: Essencial para manutenção preventiva, diagnóstico de problemas e garantia de disponibilidade do sistema.

#### 3.4 alerts (Alertas e Anomalias)
**Propósito**: Sistema de notificações para condições anormais ou críticas.

**Campos principais**:
- `alert_type`: Tipo do alerta (temperatura, pH, umidade, etc.)
- `severity`: Nível de severidade (info, warning, critical)
- `sensor_value`, `threshold_value`: Valores para análise
- `resolved`, `resolved_at`: Controle de resolução

**Justificativa**: Permite resposta rápida a condições adversas, histórico de problemas e análise de padrões de falha.

### 4. Relacionamento com a Fase 2

Este modelo expande e implementa fisicamente o MER conceitual da Fase 2:

1. **Detalhamento dos Sensores**: Na Fase 2, os sensores eram abstrações. Aqui, cada tipo tem seu campo específico com tipo de dado apropriado.

2. **Temporal Design**: Adição de múltiplos timestamps para rastreabilidade completa e sincronização entre ESP32 e servidor.

3. **Eventos como Entidade**: A irrigação, que era um atributo na Fase 2, tornou-se uma entidade própria para capturar o aspecto temporal dos eventos.

4. **Sistema de Alertas**: Nova entidade não prevista na Fase 2, mas essencial para operação em produção.

### 5. Decisões de Design

#### 5.1 Normalização
- **1NF**: Todos os atributos são atômicos
- **2NF**: Não há dependências parciais (chave primária simples)
- **3NF**: Não há dependências transitivas

#### 5.2 Desnormalização Proposital
- Mantemos `irrigation_active` em `system_stats` além dos eventos para consultas rápidas do estado atual
- `esp_timestamp` duplica informação temporal mas garante sincronização

#### 5.3 Índices
- `idx_sensor_timestamp`: Otimiza consultas temporais (mais comuns)
- `idx_irrigation_timestamp`: Acelera análise de eventos
- `idx_alerts_severity`: Prioriza alertas críticos

### 6. Operações CRUD Implementadas

#### CREATE (Insert)
- `insert_sensor_reading()`: Dados dos sensores com validação automática
- `insert_irrigation_event()`: Eventos com cálculo de duração
- `insert_system_stats()`: Métricas do sistema
- Criação automática de alertas baseada em thresholds

#### READ (Select)
- `get_latest_readings()`: Consultas paginadas
- `get_readings_by_period()`: Análise temporal
- `get_irrigation_history()`: Histórico de irrigação
- `get_active_alerts()`: Alertas pendentes
- `get_statistics()`: Agregações estatísticas

#### UPDATE
- `update_sensor_reading()`: Correção de dados
- `resolve_alert()`: Gestão de alertas

#### DELETE
- `delete_old_readings()`: Limpeza automática
- `delete_reading()`: Remoção específica

### 7. Vantagens do Modelo

1. **Escalabilidade**: Estrutura permite milhões de registros com performance adequada
2. **Flexibilidade**: Fácil adicionar novos tipos de sensores ou eventos
3. **Integridade**: Constraints e tipos garantem dados válidos
4. **Análise**: Estrutura otimizada para queries analíticas
5. **Manutenibilidade**: Separação clara de conceitos

### 8. Evolução Futura

Possíveis extensões do modelo:
- Tabela de `calibrations` para ajustes dos sensores
- Tabela de `predictions` para ML/AI
- Tabela de `maintenance_logs` para rastreabilidade
- Views materializadas para dashboards
- Particionamento temporal para grandes volumes

### 9. Conclusão

O modelo implementado representa fielmente o domínio do problema, captura todos os aspectos relevantes do sistema de monitoramento e fornece base sólida para análises avançadas e tomada de decisão automatizada. A estrutura SQL escolhida oferece confiabilidade, consistência ACID e facilidade de integração com ferramentas analíticas.