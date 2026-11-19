#!/usr/bin/env python3
"""Monitor do carrinho CitizenTech: lê o /state por Wi-Fi, grava CSV e gera relatório.

Uso básico (carrinho e computador na mesma rede Wi-Fi):
    python monitor_ia.py --host 192.168.0.50

O IP aparece no monitor serial do ESP32 ("# wifi,connected,http://<ip>").

Sem custo: use --sem-llm (relatório gerado localmente, sem internet).
Com LLM: pip install anthropic e defina a variável ANTHROPIC_API_KEY. O uso da
API é pago; se a chave faltar ou a chamada falhar, o script cai para o relatório local.
"""
import argparse
import csv
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

CSV_FIELDS = [
    "hora", "timestamp_ms", "distance_cm", "sensor_valid", "armed", "class",
    "confidence", "action", "temperature_c", "humidity_pct", "dht_valid", "ambiente",
]
OBSTACULO_CM = 20.0  # mesma distância de parada do firmware (OBSTACLE_STOP_CM)


def buscar_estado(host, timeout):
    with urllib.request.urlopen(f"http://{host}/state", timeout=timeout) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def classificar_ambiente(temp, umid, limite_calor):
    """Classificação por regras: serve de linha de base até existir um modelo treinado."""
    if temp is None or umid is None:
        return "sem_leitura"
    if temp >= limite_calor:
        return "quente"
    if temp >= 28.0 and umid >= 70.0:
        return "abafado"
    if umid < 30.0:
        return "seco"
    return "confortavel"


def resumir(linhas):
    """Resume uma janela de leituras em números que o relatório pode usar."""
    temps = [l["temperature_c"] for l in linhas if l["temperature_c"] is not None]
    umids = [l["humidity_pct"] for l in linhas if l["humidity_pct"] is not None]
    dists = [l["distance_cm"] for l in linhas if l["distance_cm"] is not None]

    def stats(valores):
        if not valores:
            return None
        return {"min": round(min(valores), 1), "max": round(max(valores), 1),
                "media": round(statistics.fmean(valores), 1)}

    return {
        "inicio": linhas[0]["hora"],
        "fim": linhas[-1]["hora"],
        "amostras": len(linhas),
        "amostras_dht_invalidas": sum(1 for l in linhas if not l["dht_valid"]),
        "temperatura_c": stats(temps),
        "umidade_pct": stats(umids),
        "variacao_temperatura_c": round(temps[-1] - temps[0], 1) if len(temps) >= 2 else None,
        "ambiente_contagem": dict(Counter(l["ambiente"] for l in linhas)),
        "classe_tinyml_contagem": dict(Counter(str(l["class"]) for l in linhas)),
        "leituras_obstaculo_proximo": sum(1 for d in dists if d <= OBSTACULO_CM),
        "distancia_media_cm": round(statistics.fmean(dists), 1) if dists else None,
    }


def montar_prompt(resumo):
    return (
        "Você é o assistente de um carrinho robô que monitora temperatura e umidade do ar "
        "em ambientes comunitários (projeto CitizenTech). Escreva um relatório curto em "
        "português para moradores e gestores, usando SOMENTE os dados abaixo. Não invente "
        "valores, locais ou causas. Se houver muitas leituras inválidas do sensor, avise "
        "que os dados são pouco confiáveis. Estrutura: 1) situação geral, 2) pontos de "
        "atenção, 3) recomendação prática. Máximo de 120 palavras.\n\n"
        f"Dados da janela de monitoramento (JSON):\n{json.dumps(resumo, ensure_ascii=False, indent=2)}"
    )


def relatorio_llm(resumo, modelo):
    """Retorna o texto do LLM, ou None se não for possível usá-lo."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("# LLM indisponível: ANTHROPIC_API_KEY não definida. Usando relatório local.")
        return None
    try:
        import anthropic  # importado aqui para o script funcionar sem a biblioteca
        cliente = anthropic.Anthropic()
        resposta = cliente.messages.create(
            model=modelo,
            max_tokens=500,
            messages=[{"role": "user", "content": montar_prompt(resumo)}],
        )
        return "".join(b.text for b in resposta.content if getattr(b, "type", "") == "text").strip()
    except Exception as erro:  # rede, chave inválida, biblioteca ausente, etc.
        print(f"# LLM indisponível ({type(erro).__name__}: {erro}). Usando relatório local.")
        return None


def relatorio_local(resumo):
    t, u = resumo["temperatura_c"], resumo["umidade_pct"]
    if t is None or u is None:
        return "Sem leituras válidas do DHT22 nesta janela. Verifique a ligação do sensor."
    partes = [
        f"Período {resumo['inicio']} a {resumo['fim']} ({resumo['amostras']} amostras).",
        f"Temperatura: média {t['media']} °C (mín {t['min']}, máx {t['max']}).",
        f"Umidade: média {u['media']}% (mín {u['min']}, máx {u['max']}).",
        f"Ambiente: {resumo['ambiente_contagem']}.",
        f"Leituras com obstáculo a até {OBSTACULO_CM:.0f} cm: {resumo['leituras_obstaculo_proximo']}.",
    ]
    invalidas = resumo["amostras_dht_invalidas"]
    if invalidas:
        partes.append(f"Atenção: {invalidas} amostras sem leitura válida do DHT22.")
    return "\n".join(partes)


def gerar_relatorio(linhas, args, pasta):
    if len(linhas) < 3:
        print("# Poucas amostras para gerar relatório.")
        return
    resumo = resumir(linhas)
    texto = None if args.sem_llm else relatorio_llm(resumo, args.modelo)
    origem = "LLM" if texto else "local"
    texto = texto or relatorio_local(resumo)
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / f"relatorio_{datetime.now():%Y%m%d_%H%M%S}.md"
    arquivo.write_text(
        f"# Relatório do carrinho ({origem})\n\n{texto}\n\n"
        f"## Resumo dos dados\n\n```json\n{json.dumps(resumo, ensure_ascii=False, indent=2)}\n```\n",
        encoding="utf-8",
    )
    print(f"\n===== RELATÓRIO ({origem}) =====\n{texto}\n(salvo em {arquivo})\n")


def numero_ou_none(valor):
    return float(valor) if isinstance(valor, (int, float)) else None


def main():
    p = argparse.ArgumentParser(description="Monitor e relatório do carrinho (DHT22 + ultrassônico).")
    p.add_argument("--host", required=True, help="IP do ESP32 (ex.: 192.168.0.50)")
    p.add_argument("--intervalo", type=float, default=3.0, help="segundos entre leituras (padrão 3)")
    p.add_argument("--relatorio-a-cada", type=int, default=120, help="segundos entre relatórios (padrão 120)")
    p.add_argument("--limite-calor", type=float, default=32.0, help="°C para classificar como quente")
    p.add_argument("--csv", default="leituras.csv", help="arquivo CSV de saída")
    p.add_argument("--pasta-relatorios", default="relatorios")
    p.add_argument("--sem-llm", action="store_true", help="não usa LLM (relatório local, sem custo)")
    p.add_argument("--modelo", default=os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5"))
    args = p.parse_args()

    caminho_csv = Path(args.csv)
    novo = not caminho_csv.exists()
    janela, falhas, ultimo_alerta = [], 0, 0.0
    proximo_relatorio = time.time() + args.relatorio_a_cada
    pasta = Path(args.pasta_relatorios)

    print(f"Monitorando http://{args.host}/state a cada {args.intervalo}s. Ctrl+C para encerrar.")
    with caminho_csv.open("a", newline="", encoding="utf-8") as arq:
        escritor = csv.DictWriter(arq, fieldnames=CSV_FIELDS)
        if novo:
            escritor.writeheader()
        try:
            while True:
                try:
                    estado = buscar_estado(args.host, timeout=4)
                    falhas = 0
                except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError) as erro:
                    falhas += 1
                    print(f"# falha {falhas} ao ler o carrinho: {erro}")
                    if falhas in (5, 20):
                        print("# Confira se o IP está certo e se o computador está na mesma rede.")
                    time.sleep(args.intervalo)
                    continue

                dht_ok = bool(estado.get("dht_valid"))
                temp = numero_ou_none(estado.get("temperature_c")) if dht_ok else None
                umid = numero_ou_none(estado.get("humidity_pct")) if dht_ok else None
                linha = {
                    "hora": datetime.now().strftime("%H:%M:%S"),
                    "timestamp_ms": estado.get("timestamp_ms"),
                    "distance_cm": numero_ou_none(estado.get("distance_cm")),
                    "sensor_valid": bool(estado.get("sensor_valid")),
                    "armed": bool(estado.get("armed")),
                    "class": estado.get("class"),
                    "confidence": estado.get("confidence"),
                    "action": estado.get("action"),
                    "temperature_c": temp,
                    "humidity_pct": umid,
                    "dht_valid": dht_ok,
                    "ambiente": classificar_ambiente(temp, umid, args.limite_calor),
                }
                escritor.writerow(linha)
                arq.flush()
                janela.append(linha)

                temp_txt = f"{temp:.1f}°C" if temp is not None else "--"
                umid_txt = f"{umid:.1f}%" if umid is not None else "--"
                dist = linha["distance_cm"]
                dist_txt = f"{dist:.0f}cm" if dist is not None else "--"
                print(f"{linha['hora']}  T={temp_txt}  U={umid_txt}  dist={dist_txt}  "
                      f"tinyml={linha['class']}  ambiente={linha['ambiente']}")

                if linha["ambiente"] == "quente" and time.time() - ultimo_alerta > 30:
                    print(f"*** ALERTA: temperatura acima de {args.limite_calor:.0f}°C ***")
                    ultimo_alerta = time.time()

                if time.time() >= proximo_relatorio:
                    gerar_relatorio(janela, args, pasta)
                    janela = []
                    proximo_relatorio = time.time() + args.relatorio_a_cada
                time.sleep(args.intervalo)
        except KeyboardInterrupt:
            print("\nEncerrando...")
            gerar_relatorio(janela, args, pasta)


if __name__ == "__main__":
    sys.exit(main())
