# Sistema de Monitoramento de Solo - Captura e Armazenamento

Sistema Python para captura de dados do ESP32 e armazenamento em banco de dados SQL, parte do projeto de irrigação inteligente da FarmTech Solutions.

## 🚀 Início Rápido

```bash
# 1. Configure o sistema (primeira vez)
python3 setup.py

# 2. Execute o sistema
./run_system.sh
```

## 📋 Funcionalidades

- ✅ Captura de dados via serial do ESP32
- ✅ Armazenamento em banco SQLite
- ✅ CRUD completo (Create, Read, Update, Delete)
- ✅ Sistema de alertas automático
- ✅ Modo simulador para testes
- ✅ Geração de relatórios

## 📁 Estrutura

```
monitoring_database/
├── setup.py              # Configuração inicial
├── run_system.sh         # Menu interativo
├── serial_reader.py      # Captura serial
├── database_manager.py   # Gerenciamento SQL
├── data_pipeline.py      # Pipeline integrado
├── test_crud.py          # Testes CRUD
├── requirements.txt      # Dependências
├── MER_justification.md  # Modelo de dados
└── TECHNICAL.md          # Documentação técnica
```

## 🔧 Instalação

### Requisitos
- Python 3.8+
- pip (gerenciador de pacotes)
- Acesso à porta serial (para hardware real)

### Passos

1. **Clone o repositório**
   ```bash
   git clone <repository-url>
   cd monitoring_database
   ```

2. **Execute o setup**
   ```bash
   python3 setup.py
   ```

   O setup irá:
   - Verificar dependências
   - Criar diretórios necessários
   - Inicializar o banco de dados
   - Detectar portas seriais
   - Gerar arquivo de configuração

3. **Inicie o sistema**
   ```bash
   ./run_system.sh
   ```

## 💻 Uso

### Menu Principal

O script `run_system.sh` oferece as seguintes opções:

1. **Configurar sistema** - Executa setup completo
2. **Modo simulador** - Testa sem hardware
3. **Hardware real** - Conecta ao ESP32
4. **Testar CRUD** - Valida operações do banco
5. **Dashboard** - Abre visualização (requer monitoring_dashboard)
6. **Sair**

### Modo Simulador

Ideal para desenvolvimento e testes:

```bash
python3 data_pipeline.py
```

### Hardware Real

Para ESP32 conectado:

```bash
# Linux/Mac
SERIAL_PORT='/dev/ttyUSB0' python3 data_pipeline.py

# Windows
SERIAL_PORT='COM3' python3 data_pipeline.py
```

## 📊 Dados Capturados

### Sensores
- Temperatura (°C)
- Umidade do solo (%)
- pH do solo
- Nutrientes: Fósforo (P) e Potássio (K)

### Sistema
- Estado da irrigação
- Tempo de operação
- Status WiFi
- Memória disponível

### Eventos
- Início/fim de irrigação
- Duração
- Gatilho (manual/automático)

## 🗄️ Banco de Dados

O sistema usa SQLite com 4 tabelas principais:

- **sensor_readings** - Leituras dos sensores
- **irrigation_events** - Eventos de irrigação
- **system_stats** - Estatísticas do sistema
- **alerts** - Alertas e notificações

Localização: `monitoring_database/soil_monitoring.db`

## 🚨 Alertas

O sistema gera alertas automáticos para:

| Sensor | Mínimo | Máximo | Severidade |
|--------|--------|--------|------------|
| Temperatura | 15°C | 35°C | Warning |
| Umidade | 30% | 70% | Warning/Info |
| pH | 6.0 | 8.0 | Critical/Warning |

## 🔍 Troubleshooting

### Porta serial não encontrada

**Linux/Mac:**
```bash
ls /dev/tty*
sudo chmod 666 /dev/ttyUSB0
```

**Windows:**
- Verifique no Gerenciador de Dispositivos
- Instale drivers CH340 ou CP2102

### Permissão negada

```bash
# Linux
sudo usermod -a -G dialout $USER
# Fazer logout e login
```

### Dados não aparecem

1. Verifique baudrate (115200)
2. Confirme formato JSON no monitor serial
3. Use modo simulador para testar

## 📈 Visualização

Para visualizar os dados em tempo real:

```bash
cd ../monitoring_dashboard
streamlit run dashboard.py
```

## 🤝 Integração

Este módulo se integra com:

- **ESP32** - Via comunicação serial
- **monitoring_dashboard** - Dashboard Streamlit
- **Sistema de irrigação** - Controle automático

## 📝 Documentação

- [Documentação Técnica](TECHNICAL.md) - Detalhes de implementação
- [Justificativa MER](MER_justification.md) - Modelo de dados
- [Dashboard](../monitoring_dashboard/README.md) - Visualização

## 📋 Licença

[![Licença CC](https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1)](http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1)
[![Atribuição BY](https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1)](http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1)

[FASE 3 - CAP 1](https://github.com/noepraexis/fase3-cap1) está licenciado sob a [Creative Commons Atribuição 4.0 Internacional](http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1).