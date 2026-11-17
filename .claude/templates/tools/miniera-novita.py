#!/usr/bin/env python3
"""Elenca i repository nominati nei thread di scouting che il registro delle fonti non conosce ancora.

Perche' esiste. Il registro delle fonti a monte segue un thread di Reddit per numero di
commenti: quando qualcuno scrive, il controllo dice «cambiato». Ma il 2026-11-12 il
proprietario ha chiesto un'altra cosa: che alla ripresa si veda se nella miniera, cioe' nel
thread in cui gli utenti segnalano le skill che usano, c'e' qualcosa di nuovo da mettere nei
filoni. «Il thread e' cambiato» non risponde: bisogna leggere i commenti nuovi e tirarne fuori
i candidati. Questo strumento lo fa in modo deterministico: scarica l'albero dei commenti
dall'archivio pubblico che il registro usa gia', ne estrae i repository citati, toglie quelli
che il registro conosce, e scrive l'elenco dei restanti con la frase in cui compaiono.

Non giudica: un repository citato in un commento e' un candidato da guardare, non una fonte
adottata. La lettura alla fonte e le quattro domande di `docs/FILONI.md` restano di chi lavora.
Legge i thread dal registro, cioe' ogni fonte il cui identificativo comincia per `reddit:`.

Uso:
    python tools/miniera-novita.py                 elenco leggibile, e lo scrive nel file del rapporto
    python tools/miniera-novita.py --hook          una riga, esce sempre con zero
    python tools/miniera-novita.py --dal 2026-10-27  solo i commenti da quella data
    python tools/miniera-novita.py --autotest

Per difetto guarda i commenti scritti dalla data in cui il registro ha verificato il thread.
Esce con 0 se non ci sono candidati nuovi, 1 se ce ne sono, 2 se l'archivio non risponde.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import sys
from pathlib import Path

REGISTRO = Path(".claude/templates/fonti-a-monte.json")
RAPPORTO = Path("_notes/fonti-a-monte/miniera-candidati.txt")
# L'host si compone a pezzi: scritto intero in un sorgente, il censimento lo prenderebbe per una fonte.
REPO = re.compile(r"(gist\.)?github" + r"\.com/([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9._-]+)")
RISERVATI = {"topics", "orgs", "features", "marketplace", "sponsors", "settings", "about", "collections", "search", "apps", "user-attachments"}


def repository_citati(testo: str) -> list:
    esito = []
    for m in REPO.finditer(testo or ""):
        proprietario, nome = m.group(2), re.sub(r"\.git$", "", m.group(3).rstrip(".,;:)"))
        if proprietario.lower() in RISERVATI or not nome:
            continue
        # Un gist ha la stessa forma di un repository su un altro host: si distingue dal prefisso.
        esito.append(("gist:" if m.group(1) else "") + proprietario + "/" + nome)
    return esito


def appiattisci(nodi: list) -> list:
    """I commenti dell'albero come elenco di (istante, autore, testo)."""
    esito = []
    for n in nodi or []:
        d = n.get("data", n) if isinstance(n, dict) else {}
        if d.get("body"):
            esito.append((int(d.get("created_utc") or 0), str(d.get("author") or ""), str(d["body"])))
        figli = d.get("replies")
        if isinstance(figli, dict):
            figli = (figli.get("data") or {}).get("children")
        if isinstance(figli, list):
            esito += appiattisci(figli)
    return esito


def candidati(commenti: list, noti: set, dal: int) -> dict:
    """repository -> elenco di (data, frase), per i soli commenti da `dal` e i repository non noti."""
    esito = {}
    for istante, _autore, testo in commenti:
        if istante < dal:
            continue
        for r in repository_citati(testo):
            if r.lower() in noti:
                continue
            frase = re.sub(r"\s+", " ", testo).strip()
            i = frase.lower().find(r.lower())
            ritaglio = frase[max(0, i - 90):i + len(r) + 90]
            esito.setdefault(r, []).append((dt.datetime.fromtimestamp(istante, dt.timezone.utc).date().isoformat(), ritaglio))
    return esito


def noti_dal_registro(registro: dict) -> set:
    return {v["id"].split(":", 1)[1].lower() for v in registro.get("fonti", []) if v["id"].startswith(("github:",))} | \
           {v["id"].lower() for v in registro.get("fonti", []) if v["id"].startswith("gist:")} | \
           {str(v).split(":", 1)[1].lower() for v in registro.get("falsi", {}) if str(v).startswith("github:")}


def thread_del_registro(registro: dict) -> list:
    return [(v["id"].split(":", 1)[1], v.get("data", "")) for v in registro.get("fonti", []) if v["id"].startswith("reddit:")]


def autotest() -> int:
    esiti = []

    def caso(nome, ok, dettaglio=""):
        esiti.append(ok)
        print(("ok    " if ok else "ROSSO ") + nome + ("" if ok else "  " + str(dettaglio)))

    h = "https://github" + ".com/"
    albero = [{"data": {"created_utc": 100, "author": "a", "body": "uso " + h + "uno/alfa tutti i giorni",
                        "replies": {"data": {"children": [{"data": {"created_utc": 300, "author": "b", "body": "anche " + h + "due/beta.git, e " + h + "topics/claude"}}]}}}},
              {"created_utc": 400, "author": "c", "body": "vecchio amico: " + h + "Uno/Alfa e nuovo " + h + "tre/gamma)."}]
    c = appiattisci(albero)
    caso("l'albero dei commenti si appiattisce, risposte comprese", len(c) == 3, c)
    caso("i repository si estraggono senza suffissi e senza le pagine del sito",
         repository_citati(c[1][2]) == ["due/beta"] and repository_citati(c[2][2]) == ["Uno/Alfa", "tre/gamma"], [repository_citati(x[2]) for x in c])
    tutti = candidati(c, set(), 0)
    caso("senza registro tutti i repository sono candidati", sorted(tutti) == ["Uno/Alfa", "due/beta", "tre/gamma", "uno/alfa"], sorted(tutti))
    nuovi = candidati(c, {"uno/alfa"}, 0)
    caso("un repository gia' nel registro non e' un candidato, a prescindere dalle maiuscole", sorted(nuovi) == ["due/beta", "tre/gamma"], sorted(nuovi))
    caso("la data limita ai commenti nuovi", sorted(candidati(c, {"uno/alfa"}, 350)) == ["tre/gamma"])
    caso("negativo: nessun commento nuovo, nessun candidato", candidati(c, set(), 1000) == {})
    caso("ogni candidato porta la frase in cui compare", "anche" in nuovi["due/beta"][0][1])
    caso("un gist non si scambia per un repository", repository_citati("vedi https://gist.github" + ".com/tizio/0123abcd qui") == ["gist:tizio/0123abcd"])
    reg = {"fonti": [{"id": "github:Uno/Alfa"}, {"id": "reddit:Sub/abc123", "data": "2026-10-27"}], "falsi": {"github:falso/x": "motivo"}}
    caso("i thread e i repository noti si leggono dal registro", thread_del_registro(reg) == [("Sub/abc123", "2026-10-27")] and noti_dal_registro(reg) == {"uno/alfa", "falso/x"}, noti_dal_registro(reg))
    print("%d prove, %d fallite" % (len(esiti), esiti.count(False)))
    return 1 if False in esiti else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--radice", default=".")
    ap.add_argument("--dal", help="data AAAA-MM-GG; per difetto la data di verifica del thread nel registro")
    ap.add_argument("--hook", action="store_true")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()
    if a.autotest:
        return autotest()
    radice = Path(a.radice).resolve()
    if not (radice / REGISTRO).is_file():
        print("miniera: qui non c'e' il registro delle fonti del template; niente da fare.")
        return 0
    registro = json.loads((radice / REGISTRO).read_text(encoding="utf-8-sig"))
    spec = importlib.util.spec_from_file_location("fonti_a_monte", Path(__file__).with_name("fonti-a-monte.py"))
    fam = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fam)
    noti = noti_dal_registro(registro)
    righe, quanti = [], 0
    try:
        for nome, data in thread_del_registro(registro):
            post = nome.split("/", 1)[1]
            dati = fam.scarica("%s/api/comments/tree?link_id=t3_%s&limit=9999" % (fam.ARCTIC, post))
            commenti = appiattisci(dati.get("data") if isinstance(dati, dict) else [])
            giorno = a.dal or data or "1970-01-01"
            dal = int(dt.datetime.fromisoformat(giorno).replace(tzinfo=dt.timezone.utc).timestamp())
            trovati = candidati(commenti, noti, dal)
            righe.append("thread %s: %d commenti letti, %d repository nuovi citati dal %s" % (nome, len(commenti), len(trovati), giorno))
            for r in sorted(trovati, key=lambda k: (-len(trovati[k]), k.lower())):
                quanti += 1
                righe.append("   %s  (%d citazioni, prima il %s)" % (r, len(trovati[r]), min(x[0] for x in trovati[r])))
                righe.append("      «%s»" % trovati[r][0][1])
    except Exception as err:  # la rete non deve far fallire un'apertura di sessione
        if a.hook:
            return 0
        print("miniera: archivio non raggiunto (%s)" % type(err).__name__, file=sys.stderr)
        return 2
    testo = "miniera, controllo del %s\n%s\n" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "\n".join(righe))
    dest = radice / RAPPORTO
    if dest.parent.is_dir():
        dest.write_text(testo, encoding="utf-8", newline="\n")
    if a.hook:
        if quanti:
            print("miniera: %d repository nuovi citati nei thread di scouting, non ancora nel registro: leggere %s e portare i candidati utili nei filoni." % (quanti, RAPPORTO.as_posix()))
        return 0
    print(testo, end="")
    return 1 if quanti else 0


if __name__ == "__main__":
    sys.exit(main())
