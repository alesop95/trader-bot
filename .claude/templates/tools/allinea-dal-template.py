#!/usr/bin/env python3
"""Allineamento deterministico di un progetto istanziato al template.

Per ogni file gestito dal template decide, senza modello linguistico, che cosa
fare, usando la storia git del template come arbitro. La domanda che risolve e
quella che a mano costa di più: la copia locale e una versione vecchia e non
toccata del template, oppure e stata estesa sul posto?

Il criterio e l'identità di contenuto. Si calcola l'hash di blob git del file
locale, con le fini riga normalizzate a LF, e lo si cerca fra tutti i blob che
quel percorso ha avuto nella storia del template, rinomine comprese. Se lo si
trova, il file locale e una versione del template mai modificata qui, e
aggiornarlo non perde niente. Se non lo si trova, il file e stato modificato
localmente: si tenta un merge a tre vie con `git merge-file` su una base che va
indovinata, perché l'antenato vero non è osservabile.

Una base indovinata sbaglia in silenzio, e in due direzioni opposte. Se e più
recente dell'antenato vero, la differenza base->testa non contiene la correzione
che il file locale non ha, e quella correzione non arriva a nessuno. Se e più
vecchia, contiene l'aggiunta di un paragrafo che il file locale ha già, e il
merge ne scrive due copie. Nessuno dei due casi produce un conflitto, quindi il
risultato del merge si misura invece di crederlo: quante righe della testa non
consegna e quante ne duplica. Se la base più vicina per contenuto non supera la
verifica si provano le altre versioni candidate; se nessuna la supera si guarda
se il file abbia righe proprie, per decidere fra SUPERATO e CONFLITTO.

Una riga della testa che manca dal merge non è sempre una perdita. Se il progetto
l'ha adattata, cioè al suo posto ha una variante che nessuna versione del template
ha mai avuto e che le somiglia, il merge ha fatto bene a tenere la variante: la si
conta come adattata e non come persa. Se al suo posto c'è una riga storica del
template, e la base troppo recente, e la guardia resta.

Esiti per file:
  UGUALE      contenuto identico alla testa del template
  NUOVO       presente nel template, assente nel progetto: si copia
  VECCHIO     versione storica intatta del template: si aggiorna
  ADATTATO    modificato localmente, contiene già tutte le modifiche del
              template e non ne perde nessuna: e una personalizzazione del
              progetto, non si tocca
  SUPERATO    ogni sua riga compare in qualche versione storica e nessuna base
              produce un merge verificato: e una copia anteriore alla storia
              registrata, senza contenuto proprio, e si aggiorna alla testa. Si
              elenca perché una riga tolta di proposito nel progetto tornerebbe
  MERGE       modificato localmente, merge a tre vie pulito e verificato: si applica
  CONFLITTO   modificato localmente, nessuna base produce un merge verificato e il
              file ha righe proprie da salvare: a mano
  SPOSTATO    il template lo ha rinominato; la copia locale era intatta o si
              fonde pulita nella destinazione: si scrive la destinazione e,
              con --rimuovi, si toglie l'origine
  RIMOSSO     il template lo ha tolto e la copia locale era intatta
  LOCALE      nel percorso gestito, mai esistito nel template: non si tocca
  INNESCO     solo con --innesco: righe di innesco delle skill con RIFERIMENTO.md
              che il CLAUDE.md non nomina ancora; con --applica si aggiungono

Un file risolto a mano si registra con --risolto <percorso> in
.claude/allineamento-risolti.json, versionato nel progetto, insieme al blob della
testa contro cui e stato risolto: resta ADATTATO finché il template non lo cambia.

Perimetro: .claude/PROJECT-SYSTEM.md, .claude/rules/, le skill del sistema
elencate in SKILL_SISTEMA, .claude/templates/ e gli strumenti istanziati sotto
tools/ del progetto il cui nome corrisponde a un unico file */tools/<nome>
del template (solo codice: i file di dati istanziati restano del progetto), e
le guide istanziate sotto docs/<pacchetto>/ da templates/<pacchetto>/.
Non tocca mai memory/, context/, settings: quelli descrivono il progetto, e il
loro allineamento resta un lavoro di lettura. CLAUDE.md lo tocca soltanto con
--innesco, e soltanto per aggiungere righe.

Uso:
  python allinea-dal-template.py --template E:/template-claude-developing --progetto .
  python allinea-dal-template.py ... --applica            # scrive NUOVO, VECCHIO, MERGE, SPOSTATO
  python allinea-dal-template.py ... --applica --rimuovi  # anche le origini di SPOSTATO e i RIMOSSO
  python allinea-dal-template.py ... --json rapporto.json
  python allinea-dal-template.py ... --applica --innesco  # anche le righe di innesco
  python allinea-dal-template.py ... --risolto tools/x.py # registra una risoluzione a mano

Senza --applica non scrive niente. Esce con 0 se non restano conflitti, con 1
se ne restano, con 2 per qualunque errore: chi lo chiama in blocco distingue
così un progetto da guardare da uno strumento che non ha potuto misurare.
La fine riga di un file esistente si conserva quando lo si riscrive.
"""
from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_SISTEMA = [
    "init-project-system", "sync-context", "git-sync", "repo-status",
    "gate-pacchetti", "riprendi", "onboard",
    "prove-che-misurano", "fonti-non-recuperabili", "alberi-di-lavoro",
    "separazione-ambienti",
]
IGNORA = {"__pycache__", ".pytest_cache"}
CODICE = {".py", ".ps1", ".sh", ".js", ".mjs"}


def git(repo: Path, *args: str, binario: bool = False):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if r.returncode != 0:
        print(f"errore: git {' '.join(args)}: {r.stderr.decode(errors='replace')}", file=sys.stderr)
        sys.exit(2)
    return r.stdout if binario else r.stdout.decode("utf-8", errors="replace")


def lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def storia(template: Path):
    """Mappa percorso -> insieme di blob storici, e origine -> destinazione."""
    blob: dict[str, set[str]] = {}
    rinomine: dict[str, str] = {}
    out = git(template, "log", "--format=", "--raw", "--no-abbrev", "-M", "HEAD", "--", ".claude")
    for riga in out.splitlines():
        if not riga.startswith(":"):
            continue
        meta, *percorsi = riga.split("\t")
        _, _, vecchio, nuovo, stato = meta.split()
        if stato.startswith("R") or stato.startswith("C"):
            src, dst = percorsi
            blob.setdefault(src, set()).add(vecchio)
            blob.setdefault(dst, set()).add(nuovo)
            if stato.startswith("R"):
                rinomine.setdefault(src, dst)  # la più recente vince: log va all'indietro
        else:
            p = percorsi[0]
            blob.setdefault(p, set()).update({vecchio, nuovo})
    zero = "0" * 40
    for s in blob.values():
        s.discard(zero)
    return blob, rinomine


_lettore: subprocess.Popen | None = None
_blob_cache: dict[str, bytes] = {}


def leggi_blob(template: Path, oid: str) -> bytes:
    """Un solo processo git cat-file --batch per tutta la corsa: un processo per
    blob costava 35 ms l'uno, cioè venti secondi a progetto."""
    global _lettore
    if oid in _blob_cache:
        return _blob_cache[oid]
    if _lettore is None:
        _lettore = subprocess.Popen(["git", "-C", str(template), "cat-file", "--batch"],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    _lettore.stdin.write(oid.encode() + b"\n")
    _lettore.stdin.flush()
    testa = _lettore.stdout.readline().split()
    if len(testa) != 3 or testa[1] != b"blob":
        print(f"errore: blob {oid} non leggibile dal template", file=sys.stderr)
        sys.exit(2)
    dati = _lettore.stdout.read(int(testa[2]))
    _lettore.stdout.read(1)  # a capo che chiude il record
    _blob_cache[oid] = dati
    return dati


def file_testa(template: Path) -> dict[str, str]:
    out = git(template, "ls-tree", "-r", "HEAD", "--", ".claude")
    m = {}
    for riga in out.splitlines():
        meta, p = riga.split("\t", 1)
        m[p] = meta.split()[2]
    return m


def gestito(p: str) -> bool:
    parti = p.split("/")
    if any(x in IGNORA for x in parti):
        return False
    if p == ".claude/PROJECT-SYSTEM.md":
        return True
    if p.startswith(".claude/rules/") or p.startswith(".claude/templates/"):
        return True
    return len(parti) > 2 and parti[1] == "skills" and parti[2] in SKILL_SISTEMA


def basi_ordinate(template: Path, candidati: set[str], locale: bytes) -> list[str]:
    """Le versioni storiche dalla più vicina per contenuto alla più lontana."""
    righe = locale.decode("utf-8", errors="replace").splitlines()
    def somiglianza(oid: str) -> float:
        c = lf(leggi_blob(template, oid)).decode("utf-8", errors="replace").splitlines()
        return difflib.SequenceMatcher(None, righe, c, autojunk=False).quick_ratio()
    return sorted(candidati, key=somiglianza, reverse=True)


MARCATORI = ("<<<<<<< ", "||||||| ", "=======", ">>>>>>> ")


def conta_righe(dati: bytes) -> collections.Counter:
    """Le righe non vuote, senza i marcatori che git merge-file inserisce."""
    return collections.Counter(r for r in dati.decode("utf-8", errors="replace").splitlines()
                               if r.strip() and not r.startswith(MARCATORI))


def verifica_merge(locale: bytes, testa_dati: bytes, unito: bytes,
                   sostituite: collections.Counter | None = None) -> tuple[int, int]:
    """Quante righe della testa il risultato non consegna, e quante ne duplica.

    Sono le due firme di una base sbagliata, e nessuna delle due produce un
    conflitto: una base più recente dell'antenato vero lascia fuori dalla
    differenza base->testa una correzione che il file locale non ha, una base
    più vecchia ci mette dentro l'aggiunta di un paragrafo che il file locale
    ha già. Misurate come differenze di multinsiemi di righe, quindi cieche a
    uno spostamento e sensibili a una perdita o a un raddoppio, che è quello
    che serve qui.

    `sostituite` sono le righe della testa che il progetto ha rimpiazzato di
    proposito con righe sue (vedi `sostituite_localmente`): la loro assenza dal
    risultato e la personalizzazione che il merge deve conservare, non una perdita."""
    L, T, R = conta_righe(locale), conta_righe(testa_dati), conta_righe(unito)
    S = sostituite or collections.Counter()
    perse = sum(max(0, v - R.get(k, 0) - S.get(k, 0)) for k, v in T.items())
    duplicate = sum(R[k] - max(L.get(k, 0), T.get(k, 0)) for k in R
                    if R[k] > max(L.get(k, 0), T.get(k, 0)))
    return perse, duplicate


def sostituite_localmente(base: bytes, locale: bytes, storiche: set[str]) -> collections.Counter:
    """Le righe della base che il file locale ha rimpiazzato con righe soltanto sue.

    Il caso e quello di un progetto che adatta una riga del template, un percorso
    o un nome proprio: la riga della testa manca dal merge perché il merge ha
    tenuto, correttamente, la variante locale. Senza questa distinzione la
    verifica la conta come persa e il file resta CONFLITTO a ogni corsa, anche
    quando non c'è niente da decidere; su retrogame-mod-pok-dev, il 2026-09-29,
    lo erano undici file su undici.

    La distinzione va tenuta stretta, perché e proprio la forma che assume la
    base troppo recente da cui la verifica protegge: anche li una riga della
    testa manca e il file locale ha altro al suo posto. La differenza sta in
    che cosa c'è al suo posto. Se il file locale e anteriore a una correzione,
    al posto della riga corretta ha la riga vecchia, che è testo storico del
    template; se l'ha adattata, ha una riga che nessuna versione del template
    ha mai avuto. Si perdona quindi solo un blocco sostituito in cui ogni riga
    locale non vuota e propria, e mai una cancellazione, che nei due casi ha la
    stessa faccia.

    Non basta ancora, e lo ha mostrato la prova del paragrafo duplicato: un file
    che non ha mai ricevuto un blocco del template e ha una riga propria nello
    stesso punto produce anch'esso una sostituzione, e perdonarla farebbe
    perdere il blocco. Un adattamento e una variante della stessa riga, quindi
    ogni riga propria perdona al più una riga della base, e soltanto se le
    somiglia per almeno il sessanta per cento dei caratteri."""
    b = [r for r in base.decode("utf-8", errors="replace").splitlines()]
    l = [r for r in locale.decode("utf-8", errors="replace").splitlines()]
    perdonate: collections.Counter = collections.Counter()
    sm = difflib.SequenceMatcher(None, b, l, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "replace":
            continue
        nuove = [r for r in l[j1:j2] if r.strip()]
        if not nuove or any(r in storiche for r in nuove):
            continue
        vecchie = [r for r in b[i1:i2] if r.strip() and not r.startswith(MARCATORI)]
        for r in nuove:
            migliore, punteggio = None, 0.6
            for i, v in enumerate(vecchie):
                q = difflib.SequenceMatcher(None, v, r, autojunk=False).ratio()
                if q >= punteggio:
                    migliore, punteggio = i, q
            if migliore is not None:
                perdonate[vecchie.pop(migliore)] += 1
    return perdonate


def nota_verifica(perse: int, duplicate: int, anteriori: int) -> str:
    """Dice perché il merge non è stato creduto, in modo che l'uscita resti leggibile."""
    parti = []
    if perse:
        parti.append(f"{perse} righe della testa che il merge non consegna")
    if duplicate:
        parti.append(f"{duplicate} righe che il merge duplicherebbe")
    if anteriori:
        parti.append(f"{anteriori} righe anteriori alla storia del template, comuni ad altri progetti")
    return "; ".join(parti)


def fondi(template: Path, candidati: set[str], locale: bytes, testa_dati: bytes):
    """Il primo merge verificato fra le basi candidate, altrimenti il meno peggio.

    Restituisce (unito, conflitti, perse, duplicate, verificato, sostituite). La
    base più vicina per contenuto e solo la prima ipotesi: quando passa la
    verifica, e il caso normale, si e pagato un solo `git merge-file`. Quando non
    passa si scorrono le altre, perché una base che perde una correzione o ne
    duplica un'altra non è una base, per quanto somigli. `sostituite` conta le
    righe della testa rimaste fuori perché il progetto le ha adattate."""
    storiche = righe_storiche(template, candidati)
    migliore = None
    for oid in basi_ordinate(template, candidati, locale):
        base = lf(leggi_blob(template, oid))
        unito, n = merge3(locale, base, testa_dati)
        s = sostituite_localmente(base, locale, storiche)
        perse, duplicate = verifica_merge(locale, testa_dati, unito, s)
        if n == 0 and not perse and not duplicate:
            T, R = conta_righe(testa_dati), conta_righe(unito)
            fuori = sum(max(0, v - R.get(k, 0)) for k, v in T.items())
            return unito, n, perse, duplicate, True, fuori
        punteggio = (n > 0, perse + duplicate, n)
        if migliore is None or punteggio < migliore[0]:
            migliore = (punteggio, (unito, n, perse, duplicate, False, 0))
    return migliore[1]


_righe_cache: dict[frozenset, set[str]] = {}


def righe_storiche(template: Path, candidati: set[str]) -> set[str]:
    """Ogni riga che il percorso ha avuto in una qualunque versione del template."""
    chiave = frozenset(candidati)
    if chiave not in _righe_cache:
        u: set[str] = set()
        for oid in candidati:
            u.update(lf(leggi_blob(template, oid)).decode("utf-8", errors="replace").splitlines())
        _righe_cache[chiave] = u
    return _righe_cache[chiave]


COMUNI: dict[str, set[str]] = {}

# I file che il progetto ha risolto a mano, con il blob della testa del template contro
# cui la risoluzione e stata fatta. Vive nel progetto ed è versionato, perché descrive
# una decisione del progetto e non uno stato della macchina.
FILE_RISOLTI = ".claude/allineamento-risolti.json"
RISOLTI: dict[str, dict] = {}


def innesco(template: Path, prj: Path, skill: list[str]) -> tuple[bytes | None, list[str], str]:
    """Il CLAUDE.md del progetto con le righe di innesco mancanti, e quali sono.

    Una norma spostata in una skill non è caricata da nessuno se il CLAUDE.md non
    nomina la situazione in cui serve: la skill resta scopribile per descrizione,
    ma la ragione per cui la norma e uscita da rules/ era proprio non affidarsi a
    quello. Le righe si prendono dal modello `templates/CLAUDE.md` del template,
    che ne e la sola fonte, e si aggiungono soltanto quelle delle skill che il
    CLAUDE.md non nomina ancora: una riga già scritta, anche riformulata dal
    progetto, non si tocca.

    Il punto di inserimento, in ordine: dopo l'ultima riga dell'indice di innesco
    se il progetto ne ha già uno, altrimenti prima della sezione degli
    apprendimenti recenti o dei vincoli di team, che il modello mette subito
    dopo l'indice, altrimenti in coda."""
    # Claude Code legge il CLAUDE.md di progetto sia in radice sia sotto .claude/, e
    # blog-alessio lo tiene nel secondo posto: cercarlo solo in radice lo dava per assente
    f = next((c for c in (prj / "CLAUDE.md", prj / ".claude" / "CLAUDE.md") if c.is_file()), None)
    if f is None:
        return None, [], "CLAUDE.md assente"
    modello = (template / ".claude/templates/CLAUDE.md").read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    intro = next((r for r in modello if r.startswith("Norme caricate su richiesta")), None)
    righe_skill = {}
    for r in modello:
        for s in skill:
            if r.startswith("- ") and r.rstrip().endswith(f"skill `{s}`."):
                righe_skill[s] = r
    grezzo = f.read_bytes()
    bom = grezzo.startswith(b"\xef\xbb\xbf")
    testo = grezzo[3:] if bom else grezzo
    crlf = b"\r\n" in testo
    s = testo.decode("utf-8").replace("\r\n", "\n")
    # presente vuol dire nominata come skill, fra apici inversi: il nome nudo compare
    # anche dentro quello della vecchia regola, `alberi-di-lavoro.md`, che non innesca niente
    mancanti = [k for k in skill if k in righe_skill and f"`{k}`" not in s]
    if not mancanti or intro is None:
        return None, [], ""
    L = s.split("\n")
    nuove = [righe_skill[k] for k in mancanti]
    i_intro = next((i for i, r in enumerate(L) if r.startswith("Norme caricate su richiesta")), None)
    if i_intro is not None:
        j = i_intro + 1
        while j < len(L) and not L[j].startswith("- "):
            j += 1
        while j < len(L) and L[j].startswith("- "):
            j += 1
        L[j:j] = nuove
        dove = "in coda all'indice di innesco esistente"
    else:
        # l'avvertenza del modello sulle righe da togliere non serve nel progetto:
        # qui si scrivono solo le righe delle skill che il progetto ha
        testa_intro = intro.split(" Si tolgono")[0]
        blocco = [testa_intro, ""] + nuove + [""]
        k = next((i for i, r in enumerate(L) if r.startswith("## Apprendimenti recenti")), None)
        if k is None:
            k = next((i for i, r in enumerate(L) if r.startswith("## Vincoli di team")), None)
        if k is None:
            while L and L[-1] == "":
                L.pop()
            L[len(L):] = [""] + blocco[:-1] + [""]
            dove = "in coda al file"
        else:
            L[k:k] = blocco
            dove = "prima di " + L[k + len(blocco)].lstrip("# ")
    out = "\n".join(L)
    if crlf:
        out = out.replace("\n", "\r\n")
    dati = (b"\xef\xbb\xbf" if bom else b"") + out.encode("utf-8")
    return dati, mancanti, dove


def righe_proprie(template: Path, candidati: set[str], locale: bytes, percorso: str) -> tuple[list[str], bool]:
    """Le righe non vuote del file locale che non compaiono in nessuna versione storica
    del template, e se tolte quelle che --righe-comuni dichiara condivise fra progetti
    non ne resta nessuna. Una riga identica nello stesso file di più progetti viene da
    una versione del template anteriore alla sua storia git, non dal singolo progetto."""
    u = righe_storiche(template, candidati)
    proprie = [r for r in locale.decode("utf-8", errors="replace").splitlines() if r.strip() and r not in u]
    comuni = COMUNI.get(percorso, set())
    return proprie, bool(candidati) and all(r in comuni for r in proprie)



def merge3(locale: bytes, base: bytes, testa: bytes) -> tuple[bytes, int]:
    with tempfile.TemporaryDirectory() as d:
        a, b, c = (Path(d) / n for n in ("locale", "base", "template"))
        a.write_bytes(locale); b.write_bytes(base); c.write_bytes(testa)
        r = subprocess.run(["git", "merge-file", "-p", "-L", "locale", "-L", "base", "-L", "template",
                            str(a), str(b), str(c)], capture_output=True)
        if r.returncode < 0:
            print("errore: git merge-file fallito", file=sys.stderr)
            sys.exit(2)
        return r.stdout, r.returncode


def scrivi(dest: Path, dati: bytes):
    """Scrive conservando la fine riga del file esistente."""
    if dest.exists() and b"\r\n" in dest.read_bytes():
        dati = lf(dati).replace(b"\n", b"\r\n")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(dati)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--template", required=True, type=Path, help="radice del repository del template")
    ap.add_argument("--progetto", default=Path("."), type=Path)
    ap.add_argument("--applica", action="store_true")
    ap.add_argument("--rimuovi", action="store_true", help="con --applica, rimuove origini spostate e file rimossi")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--righe-comuni", type=Path, help="JSON {percorso nel template: [righe]} di righe "
                    "anteriori alla storia del template, ricavate dal consenso fra progetti (allinea-tutti.ps1)")
    ap.add_argument("--risolto", action="append", default=[], metavar="PERCORSO",
                    help="registra in .claude/allineamento-risolti.json che il file, percorso nel "
                         "progetto, e stato risolto a mano contro la testa attuale del template; "
                         "ripetibile. Da quel momento resta ADATTATO finche il template non lo cambia")
    ap.add_argument("--innesco", action="store_true",
                    help="valuta anche le righe di innesco delle skill con RIFERIMENTO.md nel "
                         "CLAUDE.md del progetto; con --applica scrive quelle mancanti")
    a = ap.parse_args()
    tpl, prj = a.template.resolve(), a.progetto.resolve()
    if a.righe_comuni:
        COMUNI.update({k: set(v) for k, v in json.loads(a.righe_comuni.read_text(encoding="utf-8")).items()})
    f_risolti = prj / FILE_RISOLTI
    if f_risolti.is_file():
        RISOLTI.update(json.loads(f_risolti.read_text(encoding="utf-8")))

    blob, rinomine = storia(tpl)
    testa = file_testa(tpl)
    esiti: list[dict] = []

    def valuta(dest_rel: str, tpl_rel: str | None, storici: set[str]):
        """dest_rel: percorso nel progetto; tpl_rel: percorso in testa al template (o None)."""
        dest = prj / dest_rel
        voce = {"file": dest_rel, "template": tpl_rel}
        if tpl_rel is None:
            if not dest.exists():
                return
            loc = lf(dest.read_bytes())
            voce["esito"] = "RIMOSSO" if blob_id(loc) in storici else "LOCALE"
            esiti.append(voce); return
        t = lf(leggi_blob(tpl, testa[tpl_rel]))
        if not dest.exists():
            voce["esito"], voce["_dati"] = "NUOVO", t
        else:
            loc = lf(dest.read_bytes())
            if loc == t:
                voce["esito"] = "UGUALE"
            elif blob_id(loc) in storici:
                voce["esito"], voce["_dati"] = "VECCHIO", t
            elif RISOLTI.get(dest_rel, {}).get("testa") == testa[tpl_rel]:
                # risolto a mano contro questa stessa testa: finché il template non
                # cambia di nuovo il file non c'è niente di nuovo da decidere
                voce["esito"] = "ADATTATO"
                voce["nota"] = f"risolto a mano il {RISOLTI[dest_rel].get('il', '?')}, testa invariata"
            elif not storici:
                voce["esito"] = "CONFLITTO"; voce["nota"] = "nessuna base storica"
            else:
                unito, n, perse, duplicate, ok, fuori = fondi(tpl, storici, loc, t)
                if ok:
                    voce["esito"] = "ADATTATO" if unito == loc else "MERGE"
                    if voce["esito"] == "MERGE":
                        voce["_dati"] = unito
                    if fuori:
                        voce["nota"] = f"{fuori} righe della testa adattate dal progetto, conservate nella variante locale"
                else:
                    # nessuna base produce un merge verificato: se il file non ha righe
                    # davvero sue, e una copia anteriore alla storia registrata e si
                    # prende la testa del template
                    rp = righe_proprie(tpl, storici, loc, tpl_rel)
                    if rp[1]:
                        voce["esito"], voce["_dati"] = "SUPERATO", t
                        voce["nota"] = nota_verifica(perse, duplicate, len(rp[0]))
                    else:
                        voce["esito"], voce["_dati_conflitto"] = "CONFLITTO", unito
                        voce["righe_proprie"] = rp[0]
                        if n:
                            voce["conflitti"] = n
                        voce["nota"] = nota_verifica(perse, duplicate, 0)
        esiti.append(voce)

    # 1. file della testa del template nel perimetro
    for p in sorted(testa):
        if gestito(p):
            valuta(p, p, blob.get(p, set()))

    # 2. file locali nel perimetro assenti dalla testa: rinominati, rimossi o locali
    for f in sorted((prj / ".claude").rglob("*")):
        if not f.is_file():
            continue
        p = f.relative_to(prj).as_posix()
        if p in testa or not gestito(p):
            continue
        dst = p
        while dst in rinomine and dst not in testa:
            dst = rinomine[dst]
        if dst != p and dst in testa:
            loc = lf(f.read_bytes())
            t = lf(leggi_blob(tpl, testa[dst]))
            storici = blob.get(p, set()) | blob.get(dst, set())
            voce = {"file": p, "template": dst}
            if blob_id(loc) in storici:
                voce["esito"], voce["_dati"] = "SPOSTATO", t
            else:
                unito, n, perse, duplicate, ok, _ = fondi(tpl, storici, loc, t)
                rp = righe_proprie(tpl, storici, loc, dst) if not ok else ([], False)
                if ok:
                    voce["esito"], voce["_dati"], voce["nota"] = "SPOSTATO", unito, "copia locale estesa, fusa pulita"
                elif rp[1]:
                    voce["esito"], voce["_dati"] = "SPOSTATO", t
                    voce["nota"] = "copia anteriore alla storia del template; " + nota_verifica(perse, duplicate, len(rp[0]))
                else:
                    voce["esito"], voce["_dati_conflitto"] = "CONFLITTO", unito
                    voce["righe_proprie"] = rp[0]
                    if n:
                        voce["conflitti"] = n
                    voce["nota"] = nota_verifica(perse, duplicate, 0)
            # la destinazione e già valutata al passo 1 come NUOVO: la sostituisce questa voce
            esiti[:] = [e for e in esiti if not (e["file"] == dst and e["esito"] == "NUOVO")]
            esiti.append(voce)
        else:
            valuta(p, None, blob.get(p, set()))

    # 3. strumenti istanziati sotto tools/ del progetto
    per_nome: dict[str, list[str]] = {}
    for p in testa:
        parti = p.split("/")
        if len(parti) >= 2 and parti[-2] == "tools" and p.startswith(".claude/templates/") and not set(parti) & IGNORA:
            per_nome.setdefault(parti[-1], []).append(p)
    for f in sorted((prj / "tools").glob("*")) if (prj / "tools").is_dir() else []:
        # solo codice: i file di dati istanziati (elenchi di esclusioni, voci di roadmap)
        # sono del progetto per costruzione, e fonderli con quelli del template li guasterebbe
        cand = per_nome.get(f.name, []) if f.suffix in CODICE else []
        if f.is_file() and len(cand) == 1:
            valuta(f"tools/{f.name}", cand[0], blob.get(cand[0], set()))
        elif f.is_file() and len(cand) > 1:
            # più origini con lo stesso nome: si sceglie quella che contiene il blob locale
            loc = blob_id(lf(f.read_bytes()))
            giusti = [c for c in cand if loc in blob.get(c, set()) or loc == testa[c]]
            if len(giusti) == 1:
                valuta(f"tools/{f.name}", giusti[0], blob.get(giusti[0], set()))
            else:
                esiti.append({"file": f"tools/{f.name}", "template": None, "esito": "CONFLITTO",
                              "nota": "origine ambigua: " + ", ".join(cand)})

    # 4. guide dei pacchetti istanziate sotto docs/<pacchetto>/
    docs = prj / "docs"
    for f in sorted(docs.rglob("*")) if docs.is_dir() else []:
        if not f.is_file():
            continue
        rel = f.relative_to(docs).as_posix()
        if "/" not in rel:
            continue  # docs/README.md e simili sono del progetto: solo docs/<pacchetto>/ viene dal template
        src = f".claude/templates/{rel}"
        if src in testa:
            valuta(f"docs/{rel}", src, blob.get(src, set()))

    # 5. file risolti a mano, su richiesta esplicita
    if a.risolto:
        oggi = __import__("datetime").date.today().isoformat()
        for p in a.risolto:
            p = p.replace("\\", "/").lstrip("./") if not p.startswith(".claude") else p.replace("\\", "/")
            voce = next((e for e in esiti if e["file"] == p and e.get("template") in testa), None)
            f = prj / p
            if voce is None or not f.is_file():
                print(f"errore: --risolto {p}: non e un file del perimetro con un corrispondente nel template", file=sys.stderr)
                sys.exit(2)
            if any(r.startswith(MARCATORI[0]) or r.startswith(MARCATORI[3]) for r in f.read_text(encoding="utf-8", errors="replace").splitlines()):
                print(f"errore: --risolto {p}: il file contiene ancora marcatori di conflitto", file=sys.stderr)
                sys.exit(2)
            RISOLTI[p] = {"testa": testa[voce["template"]], "il": oggi}
            if voce["esito"] == "CONFLITTO":
                voce["esito"], voce["nota"] = "ADATTATO", f"risolto a mano il {oggi}, registrato ora"
                voce.pop("_dati_conflitto", None)
        f_risolti.parent.mkdir(parents=True, exist_ok=True)
        f_risolti.write_text(json.dumps(dict(sorted(RISOLTI.items())), ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8", newline="\n")

    # 6. righe di innesco nel CLAUDE.md, fuori dal perimetro dei file e quindi solo su richiesta
    if a.innesco:
        skill = sorted({p.split("/")[2] for p in testa
                        if p.startswith(".claude/skills/") and p.endswith("/RIFERIMENTO.md")
                        and p.split("/")[2] in SKILL_SISTEMA})
        dati, mancanti, dove = innesco(tpl, prj, skill)
        if dati is not None:
            nome = "CLAUDE.md" if (prj / "CLAUDE.md").is_file() else ".claude/CLAUDE.md"
            esiti.append({"file": nome, "template": ".claude/templates/CLAUDE.md", "esito": "INNESCO",
                          "skill": mancanti, "nota": f"righe per {', '.join(mancanti)}, {dove}", "_dati": dati})

    # applicazione
    if a.applica:
        for e in esiti:
            if e["esito"] == "INNESCO":
                (prj / e["file"]).write_bytes(e["_dati"])
            elif e["esito"] in ("NUOVO", "VECCHIO", "SUPERATO", "MERGE"):
                scrivi(prj / e["file"], e["_dati"])
            elif e["esito"] == "SPOSTATO":
                scrivi(prj / e["template"], e["_dati"])
                if a.rimuovi:
                    (prj / e["file"]).unlink()
            elif e["esito"] == "RIMOSSO" and a.rimuovi:
                (prj / e["file"]).unlink()
    for e in esiti:
        if e["esito"] == "CONFLITTO" and "_dati_conflitto" in e:
            out = prj / (e["file"] + ".conflitto")
            if a.applica:
                out.write_bytes(e["_dati_conflitto"])
                dove = f"esito del merge in {out.relative_to(prj).as_posix()}"
                e["nota"] = f"{e['nota']}; {dove}" if e.get("nota") else dove

    # rapporto
    ordine = ["CONFLITTO", "SUPERATO", "MERGE", "SPOSTATO", "RIMOSSO", "VECCHIO", "NUOVO", "INNESCO", "ADATTATO", "LOCALE", "UGUALE"]
    conta = {k: sum(1 for e in esiti if e["esito"] == k) for k in ordine}
    for k in ordine:
        if k in ("UGUALE", "ADATTATO", "LOCALE"):
            continue
        for e in (x for x in esiti if x["esito"] == k):
            extra = f" -> {e['template']}" if k == "SPOSTATO" else ""
            nota = f"  ({e['nota']})" if e.get("nota") else ""
            n = f" [{e['conflitti']} conflitti]" if e.get("conflitti") else ""
            print(f"{k:9} {e['file']}{extra}{n}{nota}")
    print("\n" + "  ".join(f"{k}={v}" for k, v in conta.items()))
    print("applicato" if a.applica else "prova a vuoto: niente scritto (usa --applica)")
    if a.json:
        a.json.write_text(json.dumps([{k: v for k, v in e.items() if not k.startswith("_")} for e in esiti],
                                     ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(1 if conta["CONFLITTO"] else 0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # un errore imprevisto non deve somigliare a un conflitto
        print(f"errore: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
