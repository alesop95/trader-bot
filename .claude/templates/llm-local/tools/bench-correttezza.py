#!/usr/bin/env python3
"""Banco di correttezza di un modello locale servito da colibri.

Risponde alla domanda che decide se conviene scaricare il lavoro meccanico su un modello locale:
non quanto e' veloce, ma quante risposte su un lotto a risposta nota sono esatte. Un modello
veloce che sbaglia troppo non scarica lavoro, lo sposta, e la correzione costa piu' del risparmio.

Legge un file JSONL con una riga per elemento, ciascuna {"prompt": ..., "atteso": ...}, interroga
l'endpoint compatibile OpenAI del modello locale con temperatura 0, normalizza la risposta e la
confronta con l'attesa. Stampa l'accuratezza e scrive il dettaglio. Usa solo la libreria standard,
come l'harness ufficiale, quindi non richiede dipendenze.

Uso:
    python3 bench-correttezza.py --base-url http://127.0.0.1:8000/v1 --model <id> \
        --lotto fixtures/classi-esempio.jsonl [--max-tokens 24]
"""
from __future__ import annotations
import argparse, json, re, sys, urllib.request, urllib.error


def chiedi(base_url, model, api_key, prompt, max_tokens):
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
               "temperature": 0, "max_tokens": max_tokens}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.load(resp)
    return d["choices"][0]["message"]["content"]


def norma(s):
    # Normalizza per il confronto: minuscole, senza punteggiatura ai bordi, prima parola-etichetta.
    s = s.strip().lower()
    m = re.search(r"[a-z0-9_-]+", s)
    return m.group(0) if m else s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--api-key", default="local")
    ap.add_argument("--lotto", required=True)
    ap.add_argument("--max-tokens", type=int, default=24)
    a = ap.parse_args()

    with open(a.lotto, encoding="utf-8") as f:
        righe = [json.loads(r) for r in f if r.strip()]

    giusti = 0
    dettaglio = []
    for i, el in enumerate(righe, 1):
        try:
            out = chiedi(a.base_url, a.model, a.api_key, el["prompt"], a.max_tokens)
        except (urllib.error.URLError, KeyError, TimeoutError) as e:
            out = f"<errore: {e}>"
        ok = norma(out) == norma(el["atteso"])
        giusti += ok
        dettaglio.append({"n": i, "atteso": el["atteso"], "ottenuto": out.strip()[:80], "ok": ok})

    tot = len(righe)
    acc = giusti / tot if tot else 0.0
    print(json.dumps({"modello": a.model, "lotto": a.lotto, "totale": tot,
                      "giusti": giusti, "accuratezza": round(acc, 3),
                      "dettaglio": dettaglio}, ensure_ascii=False, indent=2))
    # La soglia d'uso la decide il progetto: un lavoro meccanico verificabile a valle tollera piu' errori
    # di uno che si fida. Qui si esce 0 sempre: il numero e' il risultato, non un pass/fail.
    return 0


if __name__ == "__main__":
    sys.exit(main())
