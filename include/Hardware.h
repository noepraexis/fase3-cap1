/**
 * @file Hardware.h
 * @brief Define as constantes e funções relacionadas ao hardware.
 */

#ifndef HARDWARE_H
#define HARDWARE_H

#include <Arduino.h>
#include <DHT.h>
#include <Adafruit_Sensor.h>
#include "Config.h"

namespace Hardware {
    // Pinos dos sensores
    constexpr uint8_t PIN_PHOSPHORUS_BTN = 12;  // Botão para fósforo
    constexpr uint8_t PIN_POTASSIUM_BTN = 13;   // Botão para potássio
    constexpr uint8_t PIN_PH_SENSOR = 34;       // Sensor analógico para pH
    constexpr uint8_t PIN_DHT22_SENSOR = 23;    // Sensor digital DHT22 para temperatura e umidade (pino 23 é bidirecional)
    constexpr uint8_t PIN_LED_INDICATOR = 26;   // LED indicador

    // Tipo do sensor DHT
    constexpr uint8_t DHT_TYPE = DHT22;         // Usar DHT22 em vez de DHT11

    // Estados de LED
    enum LedState {
        LED_OFF = LOW,
        LED_ON  = HIGH
    };

    /**
     * Configura todos os pinos necessários para o sistema.
     */
    void setupPins();

    /**
     * Define o estado do LED indicador.
     *
     * @param state Estado desejado para o LED (HIGH ou LOW).
     */
    void IRAM_ATTR setLedState(LedState state);

    /**
     * Alterna o estado do LED indicador.
     *
     * Função otimizada para execução rápida.
     */
    void IRAM_ATTR toggleLed();

    /**
     * Lê valor analógico com múltiplas amostras para reduzir ruído.
     *
     * @param pin Pino a ser lido.
     * @param samples Número de amostras para média.
     * @return Média das leituras.
     */
    uint16_t readAnalogAverage(uint8_t pin, uint8_t samples = 5);

    /**
     * Lê o botão com debounce por software.
     *
     * @param pin Pino do botão.
     * @param activeState Estado ativo do botão (HIGH ou LOW).
     * @return true se o botão está pressionado, false caso contrário.
     */
    bool readButtonDebounced(uint8_t pin, int activeState = LOW);

    /**
     * Inicializa o sensor DHT22.
     *
     * @return true se a inicialização foi bem-sucedida.
     */
    bool initDHT();

    /**
     * Lê a temperatura do sensor DHT22.
     *
     * @return Temperatura em graus Celsius calibrada ou NAN se ocorrer erro.
     */
    float readTemperature();

    /**
     * Lê a umidade do sensor DHT22.
     *
     * @return Umidade relativa (0-100%) ou NAN se ocorrer erro.
     */
    float readHumidity();

    /**
     * Obtém a temperatura calibrada para exibição na web.
     *
     * @param rawTemp Temperatura bruta do sensor
     * @return Temperatura calibrada para exibição
     */
    float getCalibrationTemperature(float rawTemp);

} // namespace Hardware

#endif // HARDWARE_H
