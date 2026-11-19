#pragma once
// DHT22 (temperatura e umidade do ar) do firmware firmware/carrinho.
//
// Bibliotecas (Library Manager do Arduino IDE):
//   - "DHT sensor library" (Adafruit)
//   - "Adafruit Unified Sensor"
//
// Ligacao (ESP32 DevKit):
//   DHT22 VCC  -> 3V3   (3,3 V: o sinal fica em 3,3 V, nao precisa de divisor)
//   DHT22 DATA -> GPIO 4  (+ resistor de 10 kOhm entre DATA e 3V3, se o sensor for solto)
//   DHT22 GND  -> GND comum
//
// Por que uma tarefa propria: o DHT22 so le a cada ~2 s e a leitura bloqueia por
// alguns milissegundos. O loop() do carrinho descarta a janela e para os motores
// se atrasar mais de 20 ms (veja carrinho.ino), entao a leitura NAO pode ficar no loop().
#include <Arduino.h>
#include <DHT.h>

constexpr int DHT_PIN = 4;                    // GPIO livre no mapa de pinos atual
constexpr unsigned long DHT_PERIOD_MS = 2500; // DHT22 exige >= 2 s entre leituras

struct DhtReading {
  float temperatureC = NAN;
  float humidityPct = NAN;
  bool valid = false;
  unsigned long timestamp = 0;
};

class DhtMonitor {
 public:
  bool begin() {
    dht_.begin();
    return xTaskCreatePinnedToCore(task, "dht-task", 3072, this, 1, nullptr, 0) == pdPASS;
  }

  // Ultima leitura publicada pela tarefa (copia protegida por mutex).
  DhtReading latest() {
    DhtReading copy;
    portENTER_CRITICAL(&mutex_);
    copy = reading_;
    portEXIT_CRITICAL(&mutex_);
    return copy;
  }

 private:
  DHT dht_{DHT_PIN, DHT22};
  DhtReading reading_;
  portMUX_TYPE mutex_ = portMUX_INITIALIZER_UNLOCKED;

  static void task(void* argument) { static_cast<DhtMonitor*>(argument)->run(); }

  void run() {
    for (;;) {
      const float humidity = dht_.readHumidity();
      const float temperature = dht_.readTemperature();
      DhtReading next;
      next.valid = !isnan(humidity) && !isnan(temperature) &&
                   humidity >= 0.0f && humidity <= 100.0f &&
                   temperature > -40.0f && temperature < 80.0f;
      if (next.valid) {
        next.temperatureC = temperature;
        next.humidityPct = humidity;
      }
      next.timestamp = millis();
      portENTER_CRITICAL(&mutex_);
      reading_ = next;
      portEXIT_CRITICAL(&mutex_);
      vTaskDelay(pdMS_TO_TICKS(DHT_PERIOD_MS));
    }
  }
};
