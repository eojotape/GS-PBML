#!/usr/bin/env python3
"""Simula o endpoint /state do carrinho para testar monitor_ia.py sem o hardware.

Responde o mesmo JSON do firmware (network_status.h). Os dados são SINTÉTICOS:
servem para testar o pipeline de software, não como evidência do sensor real.

Uso:
    python simulador_carrinho.py --porta 8080
    python monitor_ia.py --host 127.0.0.1:8080 --sem-llm
"""
import argparse
import json
import math
import random
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

INICIO = time.monotonic()


def gerar_estado(rng, aquecimento_c_por_min):
    t = time.monotonic() - INICIO
    # Ambiente esquenta aos poucos (ex.: sala ao sol) e oscila levemente.
    temperatura = 27.0 + aquecimento_c_por_min * t / 60.0 + 0.4 * math.sin(t / 7.0) + rng.gauss(0, 0.1)
    umidade = 68.0 - 0.8 * (temperatura - 27.0) + rng.gauss(0, 0.6)
    dht_ok = rng.random() > 0.05  # ~5% de leituras falhas, como num cabo ruim
    # Carrinho circulando: distância varia com obstáculos ocasionais.
    distancia = 60.0 + 45.0 * math.sin(t / 5.0) + rng.gauss(0, 2.0)
    distancia = max(5.0, distancia)
    if distancia <= 20.0:
        classe, acao = "bloqueado", 3
    elif distancia <= 40.0:
        classe, acao = "aproximando", 1
    else:
        classe, acao = "livre", 2
    return {
        "timestamp_ms": int(t * 1000),
        "distance_cm": round(distancia, 3),
        "sensor_valid": True,
        "armed": True,
        "class": classe,
        "confidence": round(rng.uniform(0.82, 0.97), 5),
        "action": acao,
        "temperature_c": round(temperatura, 1) if dht_ok else None,
        "humidity_pct": round(umidade, 1) if dht_ok else None,
        "dht_valid": dht_ok,
    }


def main():
    p = argparse.ArgumentParser(description="Simulador do /state do carrinho (dados sintéticos).")
    p.add_argument("--porta", type=int, default=8080)
    p.add_argument("--semente", type=int, default=42)
    p.add_argument("--aquecimento", type=float, default=3.0, help="°C por minuto (padrão 3)")
    args = p.parse_args()
    rng = random.Random(args.semente)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ("/", "/state"):
                self.send_error(404)
                return
            corpo = json.dumps(gerar_estado(rng, args.aquecimento)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def log_message(self, *_):
            pass

    servidor = ThreadingHTTPServer(("127.0.0.1", args.porta), Handler)
    print(f"Simulador em http://127.0.0.1:{args.porta}/state (Ctrl+C para encerrar)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
