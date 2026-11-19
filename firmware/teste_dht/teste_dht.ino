// Teste isolado do DHT22, sem motores, ultrassom ou TinyML.
// Use antes de gravar firmware/carrinho para confirmar a ligacao do sensor.
//
// Ligacao: DHT22 VCC -> 3V3, DATA -> GPIO 4 (+10 kOhm DATA-3V3 se o sensor for solto), GND -> GND.
// Monitor serial: 115200 baud. Saida em CSV: millis,temp_c,umid_pct,valido
#include <DHT.h>

constexpr int DHT_PIN = 4;
DHT dht(DHT_PIN, DHT22);
unsigned long leituras = 0;
unsigned long invalidas = 0;

void setup() {
  Serial.begin(115200);
  dht.begin();
  delay(2000);  // o DHT22 precisa de ~2 s apos energizar
  Serial.println("millis,temp_c,umid_pct,valido");
}

void loop() {
  const float umidade = dht.readHumidity();
  const float temperatura = dht.readTemperature();
  const bool valido = !isnan(umidade) && !isnan(temperatura);
  ++leituras;
  if (!valido) ++invalidas;
  if (valido) Serial.printf("%lu,%.1f,%.1f,1\n", millis(), temperatura, umidade);
  else Serial.printf("%lu,,,0\n", millis());
  if (leituras % 10 == 0) {
    Serial.printf("# %lu leituras, %lu invalidas\n", leituras, invalidas);
  }
  delay(2500);
}
