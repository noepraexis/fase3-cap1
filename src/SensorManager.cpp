/**
 * @file SensorManager.cpp
 * @brief Implementação do gerenciador de sensores.
 */

#include "SensorManager.h"
#include "LogSystem.h"
#include "OutputManager.h"
#include "TelemetryBuffer.h"
#include "SystemMonitor.h"
#include "WiFiManager.h"
#include "StringUtils.h"

// Define o nome do módulo para logging
#define MODULE_NAME "SensorManager"

SensorManager::SensorManager()
    : m_lastReadTime(0),
    m_lastStateCheckTime(0),
    m_readCount(0),
    m_lastPhosphorusState(false),
    m_lastPotassiumState(false),
    m_filterIndex(0) {

    // Inicializa arrays de filtro
    for (uint8_t i = 0; i < FILTER_SIZE; i++) {
        m_phReadings[i] = 0;
        m_moistureReadings[i] = 0;
    }

    // Inicializa o estado dos dados processados
    m_processedData.phosphorusPresent = false; // Inicializa como AUSENTE
    m_processedData.potassiumPresent = false; // Inicializa como AUSENTE
    m_processedData.temperature = 25.0f; // Valor padrão razoável para temperatura
    m_processedData.humidityPercent = 50.0f; // Valor padrão razoável para umidade

    // Inicializa os dados brutos
    m_rawData.phosphorusState = 0; // Inicializa como AUSENTE (0)
    m_rawData.potassiumState = 0; // Inicializa como AUSENTE (0)
    m_rawData.temperatureRaw = 25.0f; // Valor padrão razoável
    m_rawData.humidityRaw = 50.0f; // Valor padrão razoável
}

bool SensorManager::init() {
    LOG_INFO(MODULE_NAME, "Inicializando Gerenciador de Sensores");

    // Não há inicialização específica necessária para sensores neste sistema
    // Mas realizamos uma leitura inicial para popular os buffers
    readSensors();
    processSensorData();

    LOG_INFO(MODULE_NAME, "Gerenciador de sensores inicializado com sucesso");
    LOG_DEBUG(MODULE_NAME, "Buffer de filtro: %u amostras", FILTER_SIZE);

    return true;
}

uint16_t SensorManager::applyFilter(uint16_t readings[], uint16_t newValue) {
    // Atualiza o buffer circular
    readings[m_filterIndex] = newValue;

    // Calcula a média
    uint32_t sum = 0;
    for (uint8_t i = 0; i < FILTER_SIZE; i++) {
        sum += readings[i];
    }

    return static_cast<uint16_t>(sum / FILTER_SIZE);
}

float SensorManager::applyFilter(float readings[], float newValue) {
    // Implementação para valores de ponto flutuante (DHT22)

    // Atualiza o buffer circular com o novo valor
    readings[m_filterIndex] = newValue;

    // Calcula a média dos valores no buffer
    float sum = 0.0f;
    for (uint8_t i = 0; i < FILTER_SIZE; i++) {
        sum += readings[i];
    }

    return sum / FILTER_SIZE;
}

void SensorManager::readSensors() {
    // Atualiza contador
    m_readCount++;

    // Obtém timestamp atual
    m_rawData.timestamp = millis();

    // Lê os botões - os pinos estão configurados como INPUT_PULLUP
    // Estado LOW (0) = botão pressionado = nutriente PRESENTE (1)
    // Estado HIGH (1) = botão não pressionado = nutriente AUSENTE (0)
    bool phosphorusButtonPressed = Hardware::readButtonDebounced(Hardware::PIN_PHOSPHORUS_BTN, LOW);
    bool potassiumButtonPressed = Hardware::readButtonDebounced(Hardware::PIN_POTASSIUM_BTN, LOW);

    // Atualiza os estados com base na leitura dos botões
    m_rawData.phosphorusState = phosphorusButtonPressed ? 1 : 0;
    m_rawData.potassiumState = potassiumButtonPressed ? 1 : 0;

    // Lê sensor analógico de pH com média de amostras para reduzir ruído
    uint16_t phRaw = Hardware::readAnalogAverage(Hardware::PIN_PH_SENSOR, 3);

    // Lê o sensor DHT22 para temperatura e umidade
    float temperature = Hardware::readTemperature();
    float humidity = Hardware::readHumidity();

    // Aplica filtro de média móvel ao pH
    m_rawData.phRaw = applyFilter(m_phReadings, phRaw);

    // Aplica filtro de média móvel também à temperatura e umidade do DHT22
    // para suavizar flutuações em leituras consecutivas
    static float tempBuffer[FILTER_SIZE] = {0.0f};
    static float humidityBuffer[FILTER_SIZE] = {0.0f};

    // Somente aplica o filtro se as leituras forem válidas
    if (temperature > -50.0f && temperature < 100.0f) {
        m_rawData.temperatureRaw = applyFilter(tempBuffer, temperature);
    } else {
        m_rawData.temperatureRaw = temperature; // Mantém o valor mesmo sendo inválido
    }

    if (humidity >= 0.0f && humidity <= 100.0f) {
        m_rawData.humidityRaw = applyFilter(humidityBuffer, humidity);
    } else {
        m_rawData.humidityRaw = humidity; // Mantém o valor mesmo sendo inválido
    }

    // Avança o índice do filtro
    m_filterIndex = (m_filterIndex + 1) % FILTER_SIZE;

    // Atualiza timestamp da última leitura
    m_lastReadTime = m_rawData.timestamp;

    // Leituras serão exibidas de forma centralizada no método update()
    // com técnica de atualização da mesma linha
}

void SensorManager::processSensorData() {
    // Converte dados brutos para unidades físicas
    m_processedData.fromRaw(m_rawData);

    // Leituras processadas serão exibidas de forma centralizada em update()
    // usando técnica de atualização na mesma linha
}

void SensorManager::checkStateChanges() {
    // Detecta mudanças de estado nos sensores digitais
    bool phosphorusChanged = (m_rawData.phosphorusState != 0) != m_lastPhosphorusState;
    bool potassiumChanged = (m_rawData.potassiumState != 0) != m_lastPotassiumState;

    if (phosphorusChanged) {
        m_lastPhosphorusState = (m_rawData.phosphorusState != 0);

        // Registra mudança de estado com o novo sistema de logging
        LOG_INFO(MODULE_NAME, "Mudança de Estado: Fósforo: %s",
                m_lastPhosphorusState ? "PRESENTE" : "AUSENTE");
    }

    if (potassiumChanged) {
        m_lastPotassiumState = (m_rawData.potassiumState != 0);

        // Registra mudança de estado com o novo sistema de logging
        LOG_INFO(MODULE_NAME, "Mudança de Estado: Potássio: %s",
                m_lastPotassiumState ? "PRESENTE" : "AUSENTE");
    }

    m_lastStateCheckTime = millis();
}

TelemetryBuffer SensorManager::prepareTelemetry() {
    // Prepara buffer de telemetria com dados atuais
    TelemetryBuffer telemetry;

    // Preenche com dados dos sensores
    telemetry.temperature = m_processedData.temperature;
    telemetry.humidity = m_processedData.humidityPercent;
    telemetry.ph = m_processedData.ph;
    telemetry.phosphorusPresent = m_processedData.phosphorusPresent;
    telemetry.potassiumPresent = m_processedData.potassiumPresent;

    // Preenche estatísticas do sistema
    SystemStats stats = SystemMonitor::getInstance().getStats();
    telemetry.freeHeap = stats.freeHeap;
    telemetry.heapFragmentation = stats.heapFragmentation;
    telemetry.uptime = stats.uptime;

    // Preenche dados de WiFi
    WiFiManager& wifiManager = WiFiManager::getInstance();
    telemetry.wifiRssi = wifiManager.getRSSI();

    // Converte o IP para string
    char ipStr[16];
    IPAddress ip = wifiManager.getIP();
    snprintf(ipStr, sizeof(ipStr), "%d.%d.%d.%d", ip[0], ip[1], ip[2], ip[3]);

    // Copia para o buffer de telemetria
    StringUtils::safeCopyString(telemetry.ipAddress, ipStr, sizeof(telemetry.ipAddress));

    // Preenche metadados
    telemetry.timestamp = millis();
    telemetry.readCount = m_readCount;

    // Retorna o buffer de telemetria para que o AsyncSoilWebServer
    // possa enviá-lo no momento apropriado
    return telemetry;
}

bool SensorManager::update(bool forceUpdate) {
    uint32_t currentTime = millis();
    static uint32_t lastDisplayUpdate = 0;
    bool dataChanged = false;

    // Verifica se é hora de atualizar
    bool timeToUpdate = (currentTime - m_lastReadTime) >= SENSOR_CHECK_INTERVAL;

    if (timeToUpdate || forceUpdate) {
        // Faz a leitura dos sensores
        readSensors();

        // Processa os dados
        processSensorData();

        // Não fazemos mais preparação de telemetria aqui
        // A telemetria será solicitada pelo AsyncSoilWebServer quando necessário
        if (currentTime - lastDisplayUpdate >= 500) { // 2Hz é suficiente para visualização
            lastDisplayUpdate = currentTime;
        }

        // Verifica mudanças de estado
        checkStateChanges();

        dataChanged = true;
    }

    // Se não é hora de atualizar, apenas verifica mudanças nos sensores digitais
    // em intervalos mais curtos para melhor responsividade
    if (currentTime - m_lastStateCheckTime >= 50) {
        // Lê apenas os sensores digitais
        bool phosphorusButtonPressed = Hardware::readButtonDebounced(Hardware::PIN_PHOSPHORUS_BTN, LOW);
        bool potassiumButtonPressed = Hardware::readButtonDebounced(Hardware::PIN_POTASSIUM_BTN, LOW);

        // Verifica se houve mudança
        bool phosphorusChanged = (phosphorusButtonPressed != m_processedData.phosphorusPresent);
        bool potassiumChanged = (potassiumButtonPressed != m_processedData.potassiumPresent);

        if (phosphorusChanged || potassiumChanged) {
            // Atualiza os dados brutos
            m_rawData.phosphorusState = phosphorusButtonPressed ? 1 : 0;
            m_rawData.potassiumState = potassiumButtonPressed ? 1 : 0;

            // Atualiza os dados processados
            m_processedData.phosphorusPresent = phosphorusButtonPressed;
            m_processedData.potassiumPresent = potassiumButtonPressed;

            // Verifica mudanças e registra no log
            checkStateChanges();

            // Não atualizamos mais telemetria diretamente aqui
            // O AsyncSoilWebServer solicitará isso quando necessário

            dataChanged = true;
        }
    }

    return dataChanged;
}

const SensorData &SensorManager::getData() const {
    return m_processedData;
}

const SensorRawData &SensorManager::getRawData() const {
    return m_rawData;
}

bool SensorManager::getDataJson(char *buffer, size_t size) const {
    if (!buffer || size == 0) return false;

    return m_processedData.toJsonString(buffer, size);
}

bool SensorManager::sensorChanged(uint8_t sensorType, float threshold) const {
    static SensorData lastData;
    static uint32_t lastCheck = 0;

    uint32_t currentTime = millis();

    // Atualiza a referência a cada 5 segundos
    if (currentTime - lastCheck > 5000) {
        lastData = m_processedData;
        lastCheck = currentTime;
        return false;
    }

    // Verifica mudança com base no tipo de sensor
    switch (sensorType) {
        case 0: // pH
            return fabs(m_processedData.ph - lastData.ph) > threshold;

        case 1: // Umidade
            return fabs(m_processedData.humidityPercent - lastData.humidityPercent) >
                threshold;

        case 2: // Fósforo
            return m_processedData.phosphorusPresent != lastData.phosphorusPresent;

        case 3: // Potássio
            return m_processedData.potassiumPresent != lastData.potassiumPresent;

        default:
            return false;
    }
}
