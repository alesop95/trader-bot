#!/usr/bin/env python3
"""Manda un lotto di compiti meccanici a un modello locale servito da colibri, al posto di un agente a pagamento.

E' il pezzo che rende concreto l'offload: invece di far vedere a Claude molti elementi uno per uno, bruciando
token e contesto, uno script li manda tutti al modello locale e ne raccoglie gli esiti su disco. Gli elementi
non entrano mai nel contesto di Claude, quindi non costano token; costano corrente e tempo in differita.

Si compone con `lavoro-a-lotti`: l'ingresso e l'uscita sono JSONL, una riga per elemento, e il lavoro e'
RIPRENDIBILE, perche' legge gli esiti gia' scritti e salta gli elementi fatti. Una sessione che cade a meta'
riparte da dove era. La verifica a valle resta compito di chi usa gli esiti, perche' nemmeno un buon modello
locale e' esatto sempre: per questo l'uscita conserva l'elemento e la risposta grezza, non una decisione presa.

Ingresso: un JSONL con, per riga, almeno {"id": <univoco>, "prompt": <testo>}. Campi extra si conservano.
Uscita: un JSONL con, per riga, l'elemento piu' {"risposta": <testo>, "modello": <id>, "errore": <se c'e'>}.

Uso:
    python3 offload-lotto.py --base-url http://127.0.0.1:8000/v1 --model <id> \
        --ingresso lotto.jsonl --uscita esiti.jsonl [--max-tokens 64] [--ogni 25]
"""
from __future__ import annotations
import argparse, json, sys, time, urllib.request, urllib.error


def chiedi(base_url, model, api_key, prompt, max_tokens):
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
               "temperature": 0, "max_tokens": max_tokens}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        d = json.load(resp)
    return d["choices"][0]["message"]["content"]


def id_gia_fatti(percorso):
    fatti = set()
    try:
        with open(percorso, encoding="utf-8") as f:
            for r in f:
                r = r.strip()
                if not r:
                    continue
                try:
                    fatti.add(json.loads(r)["id"])
                except (json.JSONDecodeError, KeyError):
                    continue
    except FileNotFoundError:
        pass
    return fatti


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--api-key", default="local")
    ap.add_argument("--ingresso", required=True)
    ap.add_argument("--uscita", required=True)
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--ogni", type=int, default=25, help="ogni quanti elementi stampare un avanzamento")
    a = ap.parse_args()

    with open(a.ingresso, encoding="utf-8") as f:
        elementi = [json.loads(r) for r in f if r.strip()]
    for i, el in enumerate(elementi):
        if "id" not in el or "prompt" not in el:
            print(f"riga {i+1}: manca 'id' o 'prompt'", file=sys.stderr)
            return 2

    fatti = id_gia_fatti(a.uscita)
    da_fare = [el for el in elementi if el["id"] not in fatti]
    print(f"lotto: {len(elementi)} elementi, {len(fatti)} gia' fatti, {len(da_fare)} da fare", file=sys.stderr)

    t0 = time.time()
    with open(a.uscita, "a", encoding="utf-8") as out:
        for n, el in enumerate(da_fare, 1):
            riga = dict(el)
            try:
                riga["risposta"] = chiedi(a.base_url, a.model, a.api_key, el["prompt"], a.max_tokens).strip()
                riga["modello"] = a.model
            except (urllib.error.URLError, KeyError, TimeoutError) as e:
                riga["risposta"] = None
                riga["errore"] = str(e)
            out.write(json.dumps(riga, ensure_ascii=False) + "\n")
            out.flush()
            if n % a.ogni == 0 or n == len(da_fare):
                dt = time.time() - t0
                print(f"  {n}/{len(da_fare)} in {dt:.0f}s ({n/dt:.2f} elem/s)", file=sys.stderr)
    print("fatto. Esiti in:", a.uscita, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
