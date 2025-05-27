# Sistema de Irrigação Inteligente com Integração Meteorológica

## Ir Além 2: Integração Python com API Pública

Este módulo implementa uma integração inteligente entre o sistema de irrigação e dados meteorológicos reais, permitindo decisões mais eficientes sobre quando e quanto irrigar.

## 🎯 Objetivo

Criar uma integração entre o sistema de irrigação e uma fonte de dados meteorológicos reais utilizando a API OpenWeather. O sistema analisa condições climáticas atuais e previsões futuras para tomar decisões inteligentes sobre irrigação, evitando desperdício de água e otimizando o crescimento das plantas.

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Sensores ESP32    │────▶│  Banco de Dados  │◀────│  API OpenWeather │
└─────────────────────┘     └──────────────────┘     └─────────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Motor de Decisão │
                            └─────────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Sistema Irrigação│
                            └─────────────────┘
```

## 📋 Componentes Principais

### 1. **weather_api.py**
- Integração com API OpenWeather
- Cache inteligente para reduzir requisições
- Simulador para testes sem API key
- Suporte a dados atuais e previsões

### 2. **irrigation_decision.py**
- Motor de decisão baseado em regras
- Análise multi-fatorial (solo + clima)
- Quatro tipos de decisão: IRRIGAR, PULAR, REDUZIR, ADIAR
- Cálculo de confiança nas decisões

### 3. **database_integration.py**
- Armazenamento de dados meteorológicos
- Histórico de decisões
- Análise estatística
- Integração com banco existente

### 4. **weather_irrigation_system.py**
- Script principal de execução
- Modo contínuo ou execução única
- Geração de relatórios
- Interface de linha de comando

## 🔧 Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure sua API key da OpenWeather:
```bash
export OPENWEATHER_API_KEY="sua_chave_aqui"
```

Obtenha uma chave gratuita em: https://openweathermap.org/api

## 🚀 Uso

### Modo Simulador (sem API key)
```bash
# Execução única com simulador
python weather_irrigation_system.py --simulator

# Modo contínuo (verifica a cada 30 minutos)
python weather_irrigation_system.py --simulator --continuous

# Simular cenário de chuva
python weather_irrigation_system.py --simulator --scenario rain
```

### Modo Real (com API)
```bash
# Execução única
python weather_irrigation_system.py --api-key SUA_CHAVE --city "São Paulo"

# Modo contínuo
python weather_irrigation_system.py --continuous --interval 60
```

### Gerar Relatório
```bash
python weather_irrigation_system.py --report
```

## 📊 Lógica de Decisão

### Condições Críticas (Prioridade Máxima)
1. **Solo criticamente seco (<20%)**: Irrigação urgente
2. **Tempestade em andamento**: Nunca irrigar (segurança)
3. **Chuva forte atual (>5mm/h)**: Cancelar irrigação

### Análise de Previsão
- **Chuva em <3h**: Cancelar irrigação
- **Chuva em 3-6h**: Adiar irrigação
- **Chuva moderada esperada**: Reduzir volume

### Condições Ambientais
- **Alta temperatura + solo seco**: Aumentar irrigação (+30%)
- **Alta umidade do ar (>85%)**: Reduzir ou cancelar
- **Neblina/orvalho**: Reduzir irrigação (-30%)

### Decisão por Umidade do Solo
- **<30%**: Irrigar
- **30-60%**: Avaliar outros fatores
- **>80%**: Não irrigar

## 📈 Cenários de Exemplo

### Cenário 1: Manhã com Previsão de Chuva
```
Dados: Solo 40%, Temperatura 22°C, Chuva prevista em 4h (70%)
Decisão: ADIAR irrigação por 4 horas
Confiança: 70%
```

### Cenário 2: Tarde Quente e Seca
```
Dados: Solo 25%, Temperatura 32°C, Sem chuva prevista
Decisão: IRRIGAR por 45 minutos (aumento por calor)
Confiança: 80%
```

### Cenário 3: Durante Chuva
```
Dados: Solo 50%, Chuva atual 8mm/h
Decisão: CANCELAR irrigação
Confiança: 95%
```

## 🗄️ Estrutura do Banco de Dados

### Tabelas Criadas

#### weather_data
- Armazena dados meteorológicos atuais
- Temperatura, umidade, pressão, condição, chuva

#### weather_forecasts
- Previsões meteorológicas
- Probabilidade e volume de chuva esperado

#### irrigation_decisions
- Histórico de todas as decisões tomadas
- Contexto completo (sensores + clima)
- Status de execução

## 📊 Estatísticas e Análise

O sistema calcula automaticamente:
- Taxa de economia de água
- Decisões por tipo de clima
- Impacto da chuva nas decisões
- Taxa de execução das irrigações

## 🔍 Monitoramento

Logs detalhados em `weather_irrigation.log`:
- Todas as decisões tomadas
- Dados meteorológicos coletados
- Erros e avisos
- Estatísticas de execução

## 🎯 Benefícios

1. **Economia de Água**: Evita irrigação desnecessária antes da chuva
2. **Proteção das Plantas**: Evita excesso de água
3. **Eficiência Energética**: Reduz uso desnecessário da bomba
4. **Decisões Inteligentes**: Combina múltiplos fatores
5. **Histórico Completo**: Análise de padrões e melhorias

## 🧪 Testes

Execute com diferentes cenários:
```bash
# Simular seca
python weather_irrigation_system.py --simulator --scenario drought

# Simular tempestade
python weather_irrigation_system.py --simulator --scenario storm

# Simular condições normais
python weather_irrigation_system.py --simulator --scenario normal
```

## 📝 Comentários sobre a Implementação

A integração foi desenvolvida seguindo princípios de:
- **Modularidade**: Componentes independentes e reutilizáveis
- **Robustez**: Tratamento de erros e fallbacks
- **Eficiência**: Cache para reduzir chamadas à API
- **Flexibilidade**: Suporte a simulador e API real
- **Rastreabilidade**: Logs detalhados e histórico completo

O sistema toma decisões considerando não apenas os dados atuais, mas também o contexto histórico e previsões futuras, resultando em uma irrigação verdadeiramente inteligente.