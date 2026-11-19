# Testes

Legenda de status: ✅ passou · ❌ falhou · ⏳ a executar.

Os testes **T-SW** já foram executados no computador com o simulador
([`python/simulador_carrinho.py`](../python/simulador_carrinho.py)), com dados
sintéticos. Os testes **T-HW** dependem do carrinho montado com o DHT22 e
devem ser preenchidos pela equipe durante o ensaio físico (anote data,
resultado observado e, se possível, um trecho do monitor serial ou foto).

## Software (sem hardware)

| ID | Teste | Procedimento | Resultado esperado | Resultado observado | Status |
| --- | --- | --- | --- | --- | --- |
| T-SW1 | Leitura do `/state` | `simulador_carrinho.py --porta 8765` + `monitor_ia.py --host 127.0.0.1:8765 --sem-llm --intervalo 1` | Uma linha por segundo no terminal e no CSV | 68 linhas gravadas em `dados/leituras_exemplo.csv` em ~68 s | ✅ (18/11/2026) |
| T-SW2 | Leitura inválida do DHT | Simulador devolve `dht_valid=false` em ~5% das leituras | Linha gravada com temperatura/umidade vazias e `ambiente=sem_leitura` | 1 amostra `sem_leitura`, contada em `amostras_dht_invalidas` | ✅ (18/11/2026) |
| T-SW3 | Classificação "quente" | Simulador aquece 6 °C/min a partir de 27 °C | Leituras ≥ 32 °C classificadas `quente` e alerta no terminal | 22 leituras `quente` no CSV | ✅ (18/11/2026) |
| T-SW4 | Relatório local | `--relatorio-a-cada 60 --sem-llm` | Arquivo `.md` com resumo após 60 s | [`relatorios/exemplo_relatorio.md`](../relatorios/exemplo_relatorio.md) | ✅ (18/11/2026) |
| T-SW5 | Queda para relatório local | Rodar sem `ANTHROPIC_API_KEY` e sem `--sem-llm` | Mensagem "LLM indisponível" e relatório local gerado | Mensagem exibida; relatório `(local)` salvo | ✅ (18/11/2026) |
| T-SW6 | Relatório com LLM | `pip install anthropic`, definir `ANTHROPIC_API_KEY`, rodar sem `--sem-llm` | Relatório em português, ≤ 120 palavras, só com dados do resumo | | ⏳ |
| T-SW7 | Carrinho fora do ar | Rodar o monitor com IP errado | Mensagens "falha N" e dica de rede após 5 falhas, sem travar | "falha 1…5" e dica de rede na 5ª falha; continuou tentando | ✅ (18/11/2026) |

## Hardware (carrinho montado)

| ID | Teste | Procedimento | Resultado esperado | Resultado observado | Status |
| --- | --- | --- | --- | --- | --- |
| T-HW1 | DHT22 isolado | Gravar `firmware/teste_dht`, monitor serial 115200 por 1 min | Leituras válidas a cada 2,5 s, 0 inválidas, valores coerentes com o ambiente | | ⏳ |
| T-HW2 | Compilação do firmware completo | Arduino IDE, placa *ESP32 Dev Module*, bibliotecas instaladas | Compila e grava sem erros | | ⏳ |
| T-HW3 | DHT no firmware completo | Monitor serial com o carrinho parado (`S`) | `# dht,temp_c=..,umid_pct=..` a cada 5 s | | ⏳ |
| T-HW4 | Resposta do sensor | Segurar o DHT22 na mão / soprar ar quente por 30 s | Temperatura e umidade sobem e depois voltam | | ⏳ |
| T-HW5 | Wi-Fi e `/state` | Abrir `http://<IP>/state` no navegador | JSON com `temperature_c`, `humidity_pct`, `dht_valid=true` | | ⏳ |
| T-HW6 | Navegação não foi afetada | Carrinho no chão, obstáculo à frente | Reduz entre 40–20 cm; a 20 cm para, dá ré e gira (igual ao CP2) | | ⏳ |
| T-HW7 | DHT desconectado (falha) | Tirar o fio DATA com o carrinho ligado | Serial mostra `# dht,invalido`, `/state` com `dht_valid=false`, **motores continuam funcionando** | | ⏳ |
| T-HW8 | Monitor com o carrinho real | `monitor_ia.py --host <IP> --sem-llm` por 5 min andando pelo ambiente | CSV e relatório gerados com dados reais | | ⏳ |
| T-HW9 | Alerta de calor | `--limite-calor` 2 °C acima da temperatura ambiente e aquecer o sensor | `*** ALERTA ***` no terminal | | ⏳ |
| T-HW10 | Autonomia | Carrinho com powerbank + pilhas, sem PC | Arma sozinho após 5 s e navega; Wi-Fi opcional | | ⏳ |

## Testes herdados do CP2

A navegação (HC-SR04 + TinyML) foi testada no CP2 — classificação
`livre`/`aproximando`/`bloqueado` com **88,89%** de acerto no conjunto de teste
real do Edge Impulse (projeto público
[1140184](https://studio.edgeimpulse.com/public/1140184/live)), redução de PWM
entre 40 e 20 cm e manobra de ré/giro a 20 cm. Esses resultados valem para o
firmware do CP2; o T-HW6 confirma que continuam valendo com o DHT22 adicionado.
