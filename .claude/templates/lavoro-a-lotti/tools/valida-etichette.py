#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida l'esito di un agente che ha classificato molti elementi su etichette chiuse.

Zero dipendenze, libreria standard. Complementare a registro.py: quello verifica che un
artefatto esista, questo verifica che un artefatto di classificazione sia COMPLETO e
BEN FORMATO, cioe' la parte della qualita' che si puo' misurare senza un giudizio.

IL CONTRATTO
------------
L'ingresso e' una lista JSON di oggetti, ciascuno con una chiave univoca. L'agente
restituisce una mappa JSON {chiave: {campo: [etichette]}}, senza prosa, scritta su disco.
Le etichette ammesse stanno in un file JSON {campo: [etichette], "_tutti": [etichette
ammesse in ogni campo]}. Un contratto cosi' e' verificabile per costruzione: le chiavi
devono coincidere con l'ingresso e ogni etichetta deve stare nell'elenco.

CHE COSA MISURA
---------------
  mancanti   chiavi dell'ingresso assenti dall'uscita
  estranee   chiavi dell'uscita che l'ingresso non conteneva
  inventate  etichette fuori dall'elenco, che vengono scartate
  vuote      elementi senza alcuna etichetta valida

Il resoconto testuale dell'agente non e' una misura: in un caso reale un agente ha
dichiarato 500 voci scritte su un ingresso di 379, e il file ne conteneva 374.

CHE COSA NON COPRE
------------------
Un'etichetta ammessa non e' un'etichetta giusta. Per questo --campione stampa N elementi
estratti a caso con le loro etichette, da rileggere: e' la parte della qualita' che resta
umana. Un tasso di vuote alto, sopra --soglia-vuote, e' invece un segnale misurabile che
l'agente ha sostituito il giudizio con una scorciatoia, per esempio uno script per parole
chiave: si rilancia il lotto invece di usarlo.

Uso:
  python valida-etichette.py --ingresso lotto.json --uscita esito.json --etichette etichette.json
                             [--chiave chiave] [--soglia-vuote 0.10] [--campione 20] [--seme 1]
                             [--scrivi unione.json]

--scrivi unisce gli elementi validi e non vuoti in una mappa cumulativa, che si crea se
manca: e' lo stato intermedio da applicare, correggibile a mano.

Codici di uscita: 0 se il lotto e' completo e sotto la soglia di vuote, 1 altrimenti.
"""
import argparse
import json
import random
import sys
from pathlib import Path


def leggi(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(description="Valida una classificazione a etichette chiuse")
    ap.add_argument("--ingresso", required=True, help="lista JSON degli elementi dati all'agente")
    ap.add_argument("--uscita", required=True, help="mappa JSON scritta dall'agente")
    ap.add_argument("--etichette", required=True, help="JSON {campo: [etichette], _tutti: [...]}")
    ap.add_argument("--chiave", default="chiave", help="nome del campo chiave negli elementi")
    ap.add_argument("--soglia-vuote", type=float, default=0.10, help="frazione di vuote oltre cui il lotto si rilancia")
    ap.add_argument("--campione", type=int, default=0, help="elementi da stampare per la rilettura")
    ap.add_argument("--seme", type=int, default=1)
    ap.add_argument("--scrivi", help="mappa cumulativa in cui unire gli elementi validi")
    a = ap.parse_args()

    ingresso = leggi(a.ingresso)
    uscita = leggi(a.uscita)
    ammesse = leggi(a.etichette)
    comuni = set(ammesse.pop("_tutti", []))
    campi = {c: set(v) | comuni for c, v in ammesse.items()}
    chiavi = {str(x[a.chiave]) for x in ingresso}
    titoli = {str(x[a.chiave]): next((str(x[k]) for k in ("titolo", "title", "nome") if x.get(k)), "") for x in ingresso}

    mancanti = sorted(chiavi - set(uscita))
    estranee = sorted(set(uscita) - chiavi)
    valide, inventate, vuote = {}, 0, []
    for k in sorted(chiavi & set(uscita)):
        voce = uscita[k] if isinstance(uscita[k], dict) else {}
        pulita = {}
        for campo, etichette in voce.items():
            if campo not in campi or not isinstance(etichette, list):
                inventate += len(etichette) if isinstance(etichette, list) else 1
                continue
            buone = [e for e in etichette if e in campi[campo]]
            inventate += len(etichette) - len(buone)
            if buone:
                pulita[campo] = buone
        if pulita:
            valide[k] = pulita
        else:
            vuote.append(k)

    quota = len(vuote) / len(chiavi) if chiavi else 0.0
    print(f"ingresso {len(chiavi)}, uscita {len(uscita)}, mancanti {len(mancanti)}, estranee {len(estranee)}, "
          f"etichette inventate {inventate}, vuote {len(vuote)} ({quota:.0%}), valide {len(valide)}")
    for etichetta, elenco in (("mancante", mancanti), ("estranea", estranee)):
        for k in elenco[:10]:
            print(f"  {etichetta}: {k}")
    if a.campione:
        random.seed(a.seme)
        for k in random.sample(sorted(valide), min(a.campione, len(valide))):
            print(f"  campione: {titoli.get(k, k)[:70]} -> {valide[k]}")
    if a.scrivi:
        p = Path(a.scrivi)
        cumulo = leggi(p) if p.exists() else {}
        cumulo.update(valide)
        p.write_text(json.dumps(cumulo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"unite {len(valide)} voci valide in {p}, che ne conta ora {len(cumulo)}")
    esito = not mancanti and not estranee and quota <= a.soglia_vuote
    if quota > a.soglia_vuote:
        print(f"vuote oltre la soglia {a.soglia_vuote:.0%}: il lotto va rilanciato, l'agente ha probabilmente sostituito il giudizio con una scorciatoia")
    return 0 if esito else 1


if __name__ == "__main__":
    sys.exit(main())
