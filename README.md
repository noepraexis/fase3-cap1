# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
    <a href= "https://www.fiap.com.br/">
        <img    src="assets/logo-fiap.png"
                alt="FIAP - Faculdade de Informática e Admnistração Paulista"
                border="0" width=40% height=40%>
    </a>
</p>

<br>

# FIAP ON 2025/IA - Fase 3 - Cap 1

## Sistema de Monitoramento e Irrigação Inteligente de Solo

## 👨‍🎓 Informações do Grupo: NOEPRÆXIS
|Nome Completo|RM|
|---|---|
|[ANA CAROLINA BELCHIOR](https://www.linkedin.com/in/ana-carolina-belchior-35a572355/)|RM563641|
|[CAIO PELLEGRINI](https://www.linkedin.com/in/caiopellegrini/)|RM565078|
|[LEONARDO DE SENA](https://www.linkedin.com/in/leonardosena)|RM563351|
|[VIVIAN NASCIMENTO SILVA AMORIM](https://www.linkedin.com/in/vivian-amorim-245a46b7)|RM565078|

## 👩‍🏫 Professores:
### Tutor(a)
- [Leonardo Ruiz Orabona](https://www.linkedin.com/in/leonardoorabona)
### Coordenador(a)
- [André Godoi Chiovato](https://www.linkedin.com/in/andregodoichiovato)

## 📜 Descrição

### Problema
A FarmTech Solutions enfrenta desafios no monitoramento eficiente das condições do solo em suas operações agrícolas. A falta de dados em tempo real sobre temperatura, umidade, pH e nutrientes do solo resulta em irrigação inadequada, desperdício de água e redução da produtividade das culturas.

### Setor de Atuação
Agronegócio - Agricultura de Precisão e IoT Agrícola

### Solução Proposta
Sistema integrado de monitoramento de solo baseado em ESP32 com controle automático de irrigação. O sistema coleta dados de múltiplos sensores, processa as informações e toma decisões inteligentes sobre quando e quanto irrigar, otimizando o uso de recursos hídricos e maximizando a produtividade.

## 🎯 Objetivos da Entrega 1

- ✅ **Circuito de sensores** simulável no Wokwi
- ✅ **Código C++** para leitura de sensores e controle de irrigação
- ✅ **Lógica de controle** baseada em limiares de umidade
- ✅ **Documentação completa** com diagramas e explicações

## 🏗 Arquitetura Geral do Sistema

### 1. Hardware:
* **Microcontrolador**: ESP32 (dual-core, 240MHz)
* **Sensores**:
    - DHT22: Temperatura e umidade do ar
    - Sensor analógico: pH do solo (0-14)
    - Botões: Simulação de detecção de fósforo e potássio
* **Atuadores**:
    - Relé (GPIO27): Controle de bomba de irrigação
    - LED integrado: Indicação de status

### 2. Software:
* **Framework**: Arduino + FreeRTOS
* **Componentes Principais**:
    - **SensorManager**: Aquisição e processamento de dados dos sensores
    - **IrrigationController**: Sistema inteligente de controle de irrigação
    - **AsyncSoilWebServer**: Interface web assíncrona com WebSockets
    - **SystemMonitor**: Monitoramento de recursos e watchdog
    - **MemoryManager**: Gerenciamento otimizado de memória
    - **WiFiManager**: Conexão e gerenciamento de WiFi
    - **Hardware**: Abstração de acesso ao hardware
    - **TelemetryBuffer**: Centralização de dados para telemetria

### 3. Organização Multitarefa:
* **Núcleo 0**: Tarefa de sensores (prioridade alta)
* **Núcleo 1**: Tarefa web e interface (prioridade normal)
* **Sincronização**: Semáforos FreeRTOS para acesso seguro aos dados

### 4. Sistema de Irrigação:

#### Características:
- **Controle Automático**: Baseado em limiar de umidade (30%-70%)
- **Controle Manual**: Via interface web com comando toggle
- **Segurança**:
  - Timeout máximo: 5 minutos de operação contínua
  - Intervalo mínimo: 1 minuto entre ativações
  - Shutdown de emergência disponível
- **Telemetria**:
  - Tempo de funcionamento em tempo real
  - Contador de ativações diárias
  - Estado atual da bomba
  - Histórico de operações

#### Configurações (Config.h):
```cpp
#define IRRIGATION_MAX_RUNTIME    300000  // 5 minutos
#define IRRIGATION_MIN_INTERVAL   60000   // 1 minuto
#define MOISTURE_THRESHOLD_LOW    30.0f   // Ativa irrigação
#define MOISTURE_THRESHOLD_HIGH   70.0f   // Desativa irrigação
#define PIN_IRRIGATION_RELAY      27      // GPIO do relé
```

### 5. Interface Web:
* **Tecnologia**: WebSockets para baixa latência
* **Formato**: JSON para troca de dados
* **Recursos**:
    - Monitoramento em tempo real de todos os sensores
    - Controle manual da bomba de irrigação
    - Visualização de estatísticas do sistema
    - Indicadores visuais de status

## 📊 Fluxo de Dados

```
Sensores → SensorManager → IrrigationController → Decisão
                ↓                    ↓
         TelemetryBuffer ← ← ← ← ← ←┘
                ↓
          OutputManager
           ↙        ↘
    WebSocket    Console
```

1. **Aquisição**: Sensores lidos a cada 200ms pela `sensorTask`
2. **Processamento**: Filtros de média móvel aplicados pelo `SensorManager`
3. **Decisão**: `IrrigationController` avalia condições e toma decisões
4. **Telemetria**: Dados centralizados no `TelemetryBuffer`
5. **Distribuição**: `OutputManager` envia para WebSocket e console
6. **Interface**: Clientes web recebem atualizações em tempo real

## 🔧 Diagrama do Circuito

![Diagrama do Circuito](assets/diagram.png)

### Conexões do Hardware:

| Componente | Pino ESP32 | Função |
|------------|------------|---------|
| DHT22 (Data) | GPIO22 | Sensor de temperatura/umidade |
| pH Sensor | GPIO34 (ADC) | Leitura analógica pH |
| Botão Fósforo | GPIO25 | Detecção nutriente P |
| Botão Potássio | GPIO26 | Detecção nutriente K |
| Relé Irrigação | GPIO27 | Controle bomba |
| LED Status | GPIO2 | Indicador interno |

## 💡 Características do Design

### Padrões de Projeto:
- **Singleton**: Controladores únicos (`IrrigationController`, `SystemMonitor`)
- **Observer**: Notificações de mudanças via WebSocket
- **Lazy Initialization**: Componentes inicializados quando necessário
- **Object Pool**: Gerenciamento de memória sem fragmentação

### Princípios SOLID:
- **S**ingle Responsibility: Cada classe tem uma única responsabilidade
- **O**pen/Closed: Extensível sem modificar código existente
- **L**iskov Substitution: Interfaces consistentes
- **I**nterface Segregation: Interfaces específicas por função
- **D**ependency Inversion: Abstrações ao invés de implementações

### Segurança e Robustez:
- Proteção contra dupla inicialização (idempotente)
- Timeouts e limites operacionais
- Recuperação automática de falhas
- Logs detalhados para diagnóstico
- Watchdog para prevenção de travamentos

## 📁 Estrutura de Diretórios

```
/
├── assets/              # Imagens e recursos
│   ├── diagram.png      # Diagrama do circuito
│   └── logo-fiap.png    # Logo institucional
├── include/             # Headers (.h)
│   ├── Config.h         # Configurações gerais
│   ├── Hardware.h       # Abstração de hardware
│   ├── IrrigationController.h  # Controlador de irrigação
│   ├── SensorManager.h  # Gerenciador de sensores
│   └── ...
├── src/                 # Implementações (.cpp)
│   ├── Main.cpp         # Ponto de entrada
│   ├── IrrigationController.cpp  # Lógica de irrigação
│   ├── SensorManager.cpp  # Processamento de sensores
│   └── ...
├── platformio.ini       # Configuração PlatformIO
├── wokwi.toml          # Configuração simulador
└── README.md           # Este arquivo
```

## 🚀 Como Executar o Projeto

### Pré-requisitos:
- Visual Studio Code
- Extensão PlatformIO
- Extensão Wokwi Simulator

### Passos:

1. **Clone o repositório:**
```bash
git clone https://github.com/noepraexis/fase3-cap1.git
cd fase3-cap1
```

2. **Abra no VS Code:**
```bash
code .
```

3. **Compile o projeto:**
```bash
pio run -e esp32dev
```

4. **Execute no simulador Wokwi:**
   - Pressione F1 → "Wokwi: Start Simulation"
   - Ou clique no ícone do Wokwi na barra de status

5. **Acesse a interface web:**
   - Abra o navegador: http://127.0.0.1:8888
   - A interface mostrará todos os sensores e controles

### Solução de Problemas:

Se houver erro de dependências:
```bash
pio upgrade --dev
pio pkg update
```

## 🔍 Monitoramento e Controle

### Interface Web:
- **URL**: http://127.0.0.1:8888 (Wokwi)
- **Atualização**: Tempo real via WebSocket
- **Controles**: Toggle para bomba de irrigação
- **Estatísticas**: Uptime, memória, ativações

### Telemetria JSON:
```json
{
  "sensors": {
    "temperature": 25.5,
    "humidity": 45.2,
    "ph": 6.8,
    "phosphorus": true,
    "potassium": false
  },
  "irrigation": {
    "active": true,
    "uptime": 120,
    "dailyActivations": 5,
    "threshold": 30.0
  },
  "system": {
    "freeHeap": 145632,
    "uptime": 3600,
    "wifi": "Connected"
  }
}
```

## 📈 Métricas de Performance

- **Taxa de amostragem**: 5Hz (200ms)
- **Latência WebSocket**: <50ms
- **Uso de memória**: ~150KB heap
- **CPU**: <30% em operação normal
- **Precisão sensores**:
  - Temperatura: ±0.5°C
  - Umidade: ±2%
  - pH: ±0.1

## 🐛 Problemas Conhecidos e Soluções

### Issue #13: Dupla Inicialização
- **Status**: ✅ RESOLVIDO
- **Problema**: IrrigationController era inicializado duas vezes
- **Solução**: Implementada proteção idempotente e lazy initialization
- **Impacto**: Nenhum após correção

## 📚 Referências

1. [ESP32 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf)
2. [DHT22 Sensor Documentation](https://www.sparkfun.com/datasheets/Sensors/Temperature/DHT22.pdf)
3. [FreeRTOS Documentation](https://www.freertos.org/Documentation/RTOS_book.html)
4. [PlatformIO Documentation](https://docs.platformio.org/)
5. [Wokwi Simulator](https://docs.wokwi.com/)

## 📋 Licença

[![Licença CC](https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1)](http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1)
[![Atribuição BY](https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1)](http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1)

[FASE 3 - CAP 1](https://github.com/noepraexis/fase3-cap1) está licenciado sob a [Creative Commons Atribuição 4.0 Internacional](http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1).