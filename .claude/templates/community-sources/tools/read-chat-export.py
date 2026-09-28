#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Converte un export di chat Discord o Telegram in Markdown leggibile e citabile.

Perché esiste
--------------
Le community su Discord sono, per alcune tecniche, la sola documentazione esistente, ma
un canale non è recuperabile né dal crawler del modello né da una richiesta HTTP: la
norma `.claude/skills/fonti-non-recuperabili/RIFERIMENTO.md` lo registra fra le fonti che
richiedono un passaggio manuale. Un export prodotto dall'utente colma quel buco, ma il
JSON che ne esce è verboso e pieno di campi che non servono: un canale di poche migliaia
di messaggi diventa decine di megabyte, cioè inutilizzabile in conversazione.

Questo strumento riduce l'export a Markdown, tenendo solo autore, momento, testo,
allegati e citazioni, e lo filtra per parola chiave o intervallo di date. L'esito va in
`_notes/fonti/` come qualunque altra fonte procurata a mano, e da là si legge o si
condensa. Dove il progetto ospite abbia attivo il pacchetto `voicestudio`, la stessa
cartella accoglie anche le trascrizioni audio, con la stessa convenzione di nome.

Formati accettati
-----------------
Discord: il JSON di DiscordChatExporter, cioè la struttura con le chiavi `guild`,
`channel` e `messages`, dove ogni messaggio ha `author`, `timestamp` e `content`.

Telegram: il `result.json` dell'export ufficiale di Telegram Desktop, dove i messaggi
stanno sotto `messages` e il testo può essere una stringa oppure una lista di frammenti
con formattazione, che questo strumento ricompone.

Il formato viene riconosciuto dalla forma del file, non dall'estensione.

Uso
---
    python tools/read-chat-export.py export.json --out _notes/fonti/2026-08-26-canale.md
    python tools/read-chat-export.py export.json --grep "link cable" --grep checksum
    python tools/read-chat-export.py export.json --since 2024-01-01 --min-length 40

Nota sul token di Discord
-------------------------
DiscordChatExporter, per esportare un canale di un server di cui si è membri senza
essere un bot, richiede il token utente. Le condizioni d'uso di Discord non lo
consentono e l'uso automatizzato del proprio account espone al rischio di sospensione:
è una decisione dell'utente, va presa sapendolo, e il token non entra né in un file
tracciato né in una conversazione. Questo strumento non tocca il token: lavora solo su
un file già prodotto.
"""

import argparse
import io
import json
import os
import re
import sys

RE_DATA = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


def riconosci(payload):
    """Ritorna 'discord', 'telegram' oppure None, guardando la forma del documento."""
    if isinstance(payload, dict):
        if "messages" in payload and ("channel" in payload or "guild" in payload):
            return "discord"
        if "messages" in payload and ("name" in payload or "type" in payload):
            return "telegram"
    return None


def testo_telegram(valore):
    """Il testo di Telegram è una stringa oppure una lista di frammenti formattati."""
    if isinstance(valore, str):
        return valore
    if isinstance(valore, list):
        pezzi = []
        for f in valore:
            if isinstance(f, str):
                pezzi.append(f)
            elif isinstance(f, dict):
                pezzi.append(f.get("text", ""))
        return "".join(pezzi)
    return ""


def estrai(payload, tipo):
    """Normalizza in una lista di dizionari con le sole chiavi che servono."""
    fuori = []
    if tipo == "discord":
        for m in payload.get("messages", []):
            autore = (m.get("author") or {}).get("nickname") or (m.get("author") or {}).get("name") or "ignoto"
            allegati = [a.get("url", "") for a in (m.get("attachments") or [])]
            citato = None
            rif = m.get("reference") or {}
            if rif.get("messageId"):
                citato = rif["messageId"]
            fuori.append({
                "id": m.get("id"),
                "autore": autore,
                "quando": (m.get("timestamp") or "")[:19].replace("T", " "),
                "testo": (m.get("content") or "").strip(),
                "allegati": [u for u in allegati if u],
                "risposta_a": citato,
            })
    else:
        for m in payload.get("messages", []):
            if m.get("type") not in (None, "message"):
                continue
            fuori.append({
                "id": m.get("id"),
                "autore": m.get("from") or "ignoto",
                "quando": (m.get("date") or "")[:19].replace("T", " "),
                "testo": testo_telegram(m.get("text")).strip(),
                "allegati": [m[k] for k in ("photo", "file") if m.get(k)],
                "risposta_a": m.get("reply_to_message_id"),
            })
    return fuori


def filtra(messaggi, args):
    tenuti = []
    parole = [p.lower() for p in (args.grep or [])]
    for m in messaggi:
        if not m["testo"] and not m["allegati"]:
            continue
        if len(m["testo"]) < args.min_length and not m["allegati"]:
            continue
        if args.since and m["quando"][:10] < args.since:
            continue
        if args.until and m["quando"][:10] > args.until:
            continue
        if parole:
            basso = m["testo"].lower()
            if not any(p in basso for p in parole):
                continue
        tenuti.append(m)
    return tenuti


def rendi(messaggi, meta, args):
    righe = []
    righe.append("# %s" % meta.get("titolo", "Export di chat"))
    righe.append("")
    righe.append("Fonte procurata a mano e convertita da `tools/read-chat-export.py`. %s" % meta.get("nota", ""))
    righe.append("")
    righe.append("Messaggi nel file: %d. Messaggi tenuti dopo il filtro: %d." % (meta["totali"], len(messaggi)))
    if args.grep:
        righe.append("")
        righe.append("Filtro per parola chiave: %s." % ", ".join(args.grep))
    righe.append("")
    ultimo_giorno = None
    for m in messaggi:
        giorno = m["quando"][:10]
        if giorno != ultimo_giorno:
            righe.append("")
            righe.append("## %s" % (giorno or "data ignota"))
            righe.append("")
            ultimo_giorno = giorno
        prefisso = "**%s**, %s" % (m["autore"], m["quando"][11:] or "?")
        if m["risposta_a"]:
            prefisso += " (in risposta a un messaggio precedente)"
        righe.append("%s: %s" % (prefisso, m["testo"].replace("\n", " ")))
        for a in m["allegati"]:
            righe.append("")
            righe.append("    allegato: %s" % a)
        righe.append("")
    return "\n".join(righe)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("export", help="file JSON prodotto dall'export")
    ap.add_argument("--out", help="file Markdown di destinazione")
    ap.add_argument("--grep", action="append",
                    help="tiene solo i messaggi che contengono questa parola; ripetibile")
    ap.add_argument("--since", help="tiene solo i messaggi dal giorno indicato, formato AAAA-MM-GG")
    ap.add_argument("--until", help="tiene solo i messaggi fino al giorno indicato")
    ap.add_argument("--min-length", type=int, default=0,
                    help="scarta i messaggi più corti di tanti caratteri, utili contro il rumore")
    args = ap.parse_args()

    for campo in ("since", "until"):
        v = getattr(args, campo)
        if v and not RE_DATA.match(v):
            print("la data %r non è nel formato AAAA-MM-GG" % v, file=sys.stderr)
            return 2

    with io.open(args.export, encoding="utf-8", errors="replace") as fh:
        payload = json.load(fh)

    tipo = riconosci(payload)
    if tipo is None:
        print("non riconosco la forma di questo export: attesi il JSON di "
              "DiscordChatExporter oppure il result.json di Telegram Desktop", file=sys.stderr)
        return 3

    messaggi = estrai(payload, tipo)
    tenuti = filtra(messaggi, args)

    if tipo == "discord":
        guild = (payload.get("guild") or {}).get("name", "server ignoto")
        canale = (payload.get("channel") or {}).get("name", "canale ignoto")
        titolo = "Discord, %s, canale #%s" % (guild, canale)
        nota = ("Export prodotto con DiscordChatExporter dall'utente, perché un canale "
                "Discord non è recuperabile automaticamente.")
    else:
        titolo = "Telegram, %s" % payload.get("name", "chat ignota")
        nota = "Export prodotto da Telegram Desktop dall'utente."

    testo = rendi(tenuti, {"titolo": titolo, "nota": nota, "totali": len(messaggi)}, args)

    if args.out:
        cartella = os.path.dirname(os.path.abspath(args.out))
        if cartella:
            os.makedirs(cartella, exist_ok=True)
        with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(testo + "\n")
        print("%s: %d messaggi su %d tenuti, %d caratteri scritti in %s"
              % (tipo, len(tenuti), len(messaggi), len(testo), args.out))
    else:
        sys.stdout.write(testo + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
