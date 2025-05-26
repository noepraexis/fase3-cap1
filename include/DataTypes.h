/**
 * @file DataTypes.h
 * @brief Define estruturas e tipos de dados otimizados para o sistema.
 */

#ifndef DATA_TYPES_H
#define DATA_TYPES_H

#include <Arduino.h>
#include "Config.h"

/**
 * Representa os valores brutos dos sensores.
 * Estrutura compacta otimizada para uso mínimo de memória.
 */
struct SensorRawData {
    uint16_t phRaw;           // Valor bruto do sensor de pH (0-4095)
    float temperatureRaw;     // Valor bruto da temperatura do DHT22 (°C)
    float humidityRaw;        // Valor bruto da umidade do DHT22 (%)
    uint8_t phosphorusState;  // Estado do fósforo  (0 = ausente, 1 = presente)
    uint8_t potassiumState;   // Estado do potássio (0 = ausente, 1 = presente)
    uint32_t timestamp;       // Timestamp da leitura (ms desde boot)

    // Construtor com valores padrão
    SensorRawData() : phRaw(0), temperatureRaw(0.0f), humidityRaw(0.0f),
                    phosphorusState(0), potassiumState(0),
                    timestamp(0) {}
};

/**
 * Representa os valores processados dos sensores.
 * Contém os dados convertidos para unidades físicas.
 */
struct SensorData {
    float ph;                // Valor de pH (0-14)
    float temperature;       // Temperatura em graus Celsius
    float humidityPercent;   // Umidade relativa do ar em percentual (0-100%)
    bool phosphorusPresent;  // Presença de fósforo
    bool potassiumPresent;   // Presença de potássio
    uint32_t timestamp;      // Timestamp da leitura

    // Construtor com valores padrão
    SensorData() : ph(0.0f), temperature(0.0f), humidityPercent(0.0f),
                phosphorusPresent(false), potassiumPresent(false),
                timestamp(0) {}

    /**
     * Converte dados brutos para formato físico.
     *
     * @param raw Dados brutos dos sensores.
     * @return Referência para o próprio objeto.
     */
    SensorData &fromRaw(const SensorRawData &raw) {
        // Converte pH: mapeia 0-4095 para 0-14 (escala de pH)
        ph = (raw.phRaw * PH_SCALE_MAX) / 4095.0f;

        // Temperatura e umidade já vêm em unidades físicas do DHT22
        // Aplica uma correção para a temperatura (valor real do DHT22)
        temperature = raw.temperatureRaw;

        // A umidade já está correta, não precisa de ajuste
        humidityPercent = raw.humidityRaw;

        // Estados booleanos
        phosphorusPresent = (raw.phosphorusState != 0);
        potassiumPresent  = (raw.potassiumState  != 0);

        // Mantém o timestamp
        timestamp = raw.timestamp;

        return *this;
    }

    /**
     * Converte os dados para string JSON.
     *
     * @param buffer Buffer para armazenar o JSON.
     * @param size Tamanho do buffer.
     * @return true se a conversão foi bem-sucedida, false caso contrário.
     */
    bool toJsonString(char *buffer, size_t size) const {
        if (!buffer || size == 0) return false;

        int written = snprintf(buffer, size,
            "{\"ph\":%.1f,\"temperature\":%.1f,\"humidity\":%.1f,\"phosphorus\":%s,"
            "\"potassium\":%s,\"timestamp\":%u}",
            ph, temperature, humidityPercent,
            phosphorusPresent ? "true" : "false",
            potassiumPresent ? "true" : "false",
            timestamp);

        return (written > 0 && written < static_cast<int>(size));
    }
};

/**
 * Estrutura para estatísticas do sistema.
 * Monitora o desempenho do sistema.
 */
struct SystemStats {
    uint32_t freeHeap;          // Liberação de Heap em bytes
    uint32_t minFreeHeap;       // Mínimo de liberação de heap já registrado
    uint16_t heapFragmentation; // Fragmentação do heap (percentual)
    uint8_t  cpuLoad;           // Utilização da CPU (percentual)
    uint32_t uptime;            // Tempo de atividade em segundos
    uint16_t wifiRSSI;          // Força do sinal WiFi
    uint16_t sensorReadCount;   // Contagem de leituras de sensores

    // Construtor com valores padrão
    SystemStats() : freeHeap(0), minFreeHeap(0), heapFragmentation(0),
                cpuLoad(0), uptime(0), wifiRSSI(0), sensorReadCount(0) {}
};

#endif // DATA_TYPES_H
