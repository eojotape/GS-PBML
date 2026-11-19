# Relatório do carrinho (local)

> **Exemplo gerado com `python/simulador_carrinho.py` (dados sintéticos)**, para mostrar o formato da saída do `monitor_ia.py`. Comando: `python monitor_ia.py --host 127.0.0.1:8765 --sem-llm --intervalo 1 --relatorio-a-cada 60`. Substitua por um relatório do carrinho real após o teste físico.

Período 15:11:53 a 15:12:54 (61 amostras).
Temperatura: média 30.4 °C (mín 27.3, máx 33.6).
Umidade: média 65.3% (mín 61.8, máx 67.8).
Ambiente: {'confortavel': 45, 'sem_leitura': 1, 'quente': 15}.
Leituras com obstáculo a até 20 cm: 9.
Atenção: 1 amostras sem leitura válida do DHT22.

## Resumo dos dados

```json
{
  "inicio": "15:11:53",
  "fim": "15:12:54",
  "amostras": 61,
  "amostras_dht_invalidas": 1,
  "temperatura_c": {
    "min": 27.3,
    "max": 33.6,
    "media": 30.4
  },
  "umidade_pct": {
    "min": 61.8,
    "max": 67.8,
    "media": 65.3
  },
  "variacao_temperatura_c": 6.2,
  "ambiente_contagem": {
    "confortavel": 45,
    "sem_leitura": 1,
    "quente": 15
  },
  "classe_tinyml_contagem": {
    "livre": 39,
    "aproximando": 13,
    "bloqueado": 9
  },
  "leituras_obstaculo_proximo": 9,
  "distancia_media_cm": 60.1
}
```
