#!/usr/bin/env python3
"""Allineamento deterministico di un progetto istanziato al template.

Per ogni file gestito dal template decide, senza modello linguistico, che cosa
fare, usando la storia git del template come arbitro. La domanda che risolve e
quella che a mano costa di piu: la copia locale e una versione vecchia e non
toccata del template, oppure e stata estesa sul posto?

Il criterio e l'identita di contenuto. Si calcola l'hash di blob git del file
locale, con le fini riga normalizzate a LF, e lo si cerca fra tutti i blob che
quel percorso ha avuto nella storia del template, rinomine comprese. Se lo si
trova, il file locale e una versione del template mai modificata qui, e
aggiornarlo non perde niente. Se non lo si trova, il file e stato modificato
localmente: si sceglie come base la versione storica piu vicina e si tenta un
merge a tre vie con `git merge-file`. Un merge pulito si puo applicare; uno con
conflitti si lascia alla persona, con il file dei conflitti scritto a parte.

Esiti per file:
  UGUALE      contenuto identico alla testa del template
  NUOVO       presente nel template, assente nel progetto: si copia
  VECCHIO     versione storica intatta del template: si aggiorna
  ADATTATO    modificato localmente e contiene gia tutte le modifiche del
              template: e una personalizzazione del progetto, non si tocca
  SUPERATO    non coincide con nessuna versione storica, ma ogni sua riga compare
              in qualcuna: e una copia anteriore alla storia registrata, senza
              contenuto proprio, e si aggiorna. Si elenca perche una riga tolta
              di proposito nel progetto tornerebbe
  MERGE       modificato localmente, merge a tre vie pulito: si applica
  CONFLITTO   modificato localmente, merge con conflitti: a mano
  SPOSTATO    il template lo ha rinominato; la copia locale era intatta o si
              fonde pulita nella destinazione: si scrive la destinazione e,
              con --rimuovi, si toglie l'origine
  RIMOSSO     il template lo ha tolto e la copia locale era intatta
  LOCALE      nel percorso gestito, mai esistito nel template: non si tocca

Perimetro: .claude/PROJECT-SYSTEM.md, .claude/rules/, le skill del sistema
elencate in SKILL_SISTEMA, .claude/templates/ e gli strumenti istanziati sotto
tools/ del progetto il cui nome corrisponde a un unico file */tools/<nome>
del template (solo codice: i file di dati istanziati restano del progetto), e
le guide istanziate sotto docs/<pacchetto>/ da templates/<pacchetto>/.
Non tocca mai memory/, context/, CLAUDE.md, settings: quelli descrivono il
progetto, e il loro allineamento resta un lavoro di lettura.

Uso:
  python allinea-dal-template.py --template E:/template-claude-developing --progetto .
  python allinea-dal-template.py ... --applica            # scrive NUOVO, VECCHIO, MERGE, SPOSTATO
  python allinea-dal-template.py ... --applica --rimuovi  # anche le origini di SPOSTATO e i RIMOSSO
  python allinea-dal-template.py ... --json rapporto.json

Senza --applica non scrive niente. Esce con 0 se non restano conflitti, con 1
se ne restano, con 2 per qualunque errore: chi lo chiama in blocco distingue
cosi un progetto da guardare da uno strumento che non ha potuto misurare.
La fine riga di un file esistente si conserva quando lo si riscrive.
"""
from __future__ import annotations

import argparse
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
                rinomine.setdefault(src, dst)  # la piu recente vince: log va all'indietro
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
    blob costava 35 ms l'uno, cioe venti secondi a progetto."""
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


def base_piu_vicina(template: Path, candidati: set[str], locale: bytes) -> bytes | None:
    migliore, punteggio = None, -1.0
    righe = locale.decode("utf-8", errors="replace").splitlines()
    for oid in candidati:
        c = lf(leggi_blob(template, oid))
        r = difflib.SequenceMatcher(None, righe, c.decode("utf-8", errors="replace").splitlines(), autojunk=False).quick_ratio()
        if r > punteggio:
            migliore, punteggio = c, r
    return migliore


_righe_cache: dict[frozenset, set[str]] = {}


COMUNI: dict[str, set[str]] = {}


def righe_proprie(template: Path, candidati: set[str], locale: bytes, percorso: str) -> tuple[list[str], bool]:
    """Le righe non vuote del file locale che non compaiono in nessuna versione storica
    del template, e se tolte quelle che --righe-comuni dichiara condivise fra progetti
    non ne resta nessuna. Una riga identica nello stesso file di piu progetti viene da
    una versione del template anteriore alla sua storia git, non dal singolo progetto."""
    chiave = frozenset(candidati)
    if chiave not in _righe_cache:
        u: set[str] = set()
        for oid in candidati:
            u.update(lf(leggi_blob(template, oid)).decode("utf-8", errors="replace").splitlines())
        _righe_cache[chiave] = u
    u = _righe_cache[chiave]
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
    a = ap.parse_args()
    tpl, prj = a.template.resolve(), a.progetto.resolve()
    if a.righe_comuni:
        COMUNI.update({k: set(v) for k, v in json.loads(a.righe_comuni.read_text(encoding="utf-8")).items()})

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
            else:
                base = base_piu_vicina(tpl, storici, loc) if storici else None
                if base is None:
                    voce["esito"] = "CONFLITTO"; voce["nota"] = "nessuna base storica"
                else:
                    unito, n = merge3(loc, base, t)
                    if n == 0 and unito == loc:
                        voce["esito"] = "ADATTATO"
                    elif n == 0:
                        voce["esito"], voce["_dati"] = "MERGE", unito
                    else:
                        # il merge non basta: se il file non ha righe davvero sue, e una copia
                        # anteriore alla storia registrata e si prende la testa del template
                        rp = righe_proprie(tpl, storici, loc, tpl_rel)
                        if rp[1]:
                            voce["esito"], voce["_dati"] = "SUPERATO", t
                            if rp[0]:
                                voce["nota"] = f"{len(rp[0])} righe anteriori alla storia del template, comuni ad altri progetti"
                        else:
                            voce["esito"], voce["_dati_conflitto"], voce["conflitti"] = "CONFLITTO", unito, n
                            voce["righe_proprie"] = rp[0]
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
                unito, n = merge3(loc, base_piu_vicina(tpl, storici, loc), t)
                rp = righe_proprie(tpl, storici, loc, dst) if n else ([], False)
                if n == 0:
                    voce["esito"], voce["_dati"], voce["nota"] = "SPOSTATO", unito, "copia locale estesa, fusa pulita"
                elif rp[1]:
                    voce["esito"], voce["_dati"], voce["nota"] = "SPOSTATO", t, "copia anteriore alla storia del template"
                else:
                    voce["esito"], voce["_dati_conflitto"], voce["conflitti"] = "CONFLITTO", unito, n
                    voce["righe_proprie"] = rp[0]
            # la destinazione e gia valutata al passo 1 come NUOVO: la sostituisce questa voce
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
            # piu origini con lo stesso nome: si sceglie quella che contiene il blob locale
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

    # applicazione
    if a.applica:
        for e in esiti:
            if e["esito"] in ("NUOVO", "VECCHIO", "SUPERATO", "MERGE"):
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
                e["nota"] = f"conflitti in {out.relative_to(prj).as_posix()}"

    # rapporto
    ordine = ["CONFLITTO", "SUPERATO", "MERGE", "SPOSTATO", "RIMOSSO", "VECCHIO", "NUOVO", "ADATTATO", "LOCALE", "UGUALE"]
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
