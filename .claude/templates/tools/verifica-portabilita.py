#!/usr/bin/env python3
"""Dice che cosa, nel template, funziona su un solo sistema operativo.

Perche' esiste. Il template dichiara in piu' punti che le capacita' vanno fornite in
doppia forma, PowerShell e shell POSIX, ma la dichiarazione non era presidiata da
nulla: il 2026-10-23 un censimento ha trovato quarantacinque capacita' di cui venti
in doppia forma e venticinque in forma singola, e soprattutto ha trovato che tutti
gli hook di git erano senza bit di esecuzione. Quest'ultimo e' il difetto peggiore
della famiglia, perche' su Linux git salta un hook non eseguibile **senza dire
niente**: il presidio sparisce e il commit passa.

Un rapporto che segnala sempre le stesse cose smette di essere letto, quindi le
forme singole legittime si dichiarano in `portabilita-eccezioni.json` accanto a
questo file, ciascuna con la propria ragione. Una forma singola non dichiarata e'
un rilievo; una dichiarata non lo e'. Questo strumento non corregge niente.

Uso, dalla radice del template:
    python .claude/templates/tools/verifica-portabilita.py
    python .claude/templates/tools/verifica-portabilita.py --hook   # compatto, non blocca
    python .claude/templates/tools/verifica-portabilita.py --autotest

Esce con 0 se non trova rilievi, con 1 se ne trova, con 0 sempre in modo hook.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ECCEZIONI = Path(".claude/templates/tools/portabilita-eccezioni.json")


def tracciati(radice: Path) -> list[str]:
    r = subprocess.run(["git", "ls-files", "-s"], capture_output=True, text=True,
                       cwd=radice, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return []
    return r.stdout.splitlines()


def leggi_eccezioni(radice: Path) -> dict:
    f = radice / ECCEZIONI
    if not f.is_file():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def esamina(radice: Path) -> dict:
    righe = tracciati(radice)
    if not righe:
        return {"errore": "git non risponde o non e' un repository"}
    modi, percorsi = {}, []
    for riga in righe:
        try:
            meta, percorso = riga.split("\t", 1)
            modo = meta.split()[0]
        except ValueError:
            continue
        modi[percorso] = modo
        percorsi.append(percorso)
    ecc = leggi_eccezioni(radice)
    scusate = set(ecc.get("forme-singole", {}).keys())
    # Il debito noto non e' una dimenticanza e non e' un'eccezione: e' una capacita'
    # che dovrebbe esistere su entrambi i sistemi, che oggi non esiste, e che qualcuno
    # ha gia' guardato. Tenerlo nello stesso mucchio delle dimenticanze produce quindici
    # avvisi identici a ogni giro, che e' il modo piu' rapido di far spegnere il controllo.
    debito = set(ecc.get("debito-noto", {}).keys())

    # 1. capacita' in forma singola: stessa cartella, stesso nome, estensione diversa
    forme: dict[tuple[str, str], set[str]] = {}
    for p in percorsi:
        q = Path(p)
        if q.suffix.lower() in (".ps1", ".sh", ".py"):
            forme.setdefault((q.parent.as_posix(), q.stem.lower()), set()).add(q.suffix.lower())
    singole, note = [], []
    for (cartella, nome), est in sorted(forme.items()):
        if len(est) > 1 or ".py" in est:
            continue          # il Python vale come terza via, portabile per natura
        # Per un file nella radice `parent` vale ".", e un prefisso "./" nel rapporto
        # sporca il confronto con le eccezioni oltre che la lettura.
        chiave = ("%s%s" % (nome, next(iter(est))) if cartella == "."
                  else "%s/%s%s" % (cartella, nome, next(iter(est))))
        if any(chiave.startswith(s) or s in chiave for s in scusate):
            continue
        if any(chiave.startswith(s) or s in chiave for s in debito):
            note.append((chiave, next(iter(est))))
            continue
        singole.append((chiave, next(iter(est))))

    # 2. hook di git senza bit di esecuzione: il difetto che rompe in silenzio
    hook_non_eseguibili = [p for p, m in modi.items()
                           if p.startswith(".githooks/") and m == "100644"]

    # 3. script di shell senza bit di esecuzione
    sh_non_eseguibili = [p for p, m in modi.items()
                         if p.endswith(".sh") and m == "100644"]

    # 4. .gitattributes che protegga almeno gli script di shell
    ga = radice / ".gitattributes"
    ga_ok = ga.is_file() and re.search(r"^\s*\*\.sh\s+.*eol=lf", ga.read_text(encoding="utf-8"),
                                       re.M) is not None

    # 5. comandi negli hook: percorsi con barra rovesciata, o interprete non risolto
    comandi = []
    for p in percorsi:
        if not p.endswith(".json") or "settings" not in Path(p).name:
            continue
        try:
            dati = json.loads((radice / p).read_text(encoding="utf-8"))
        except Exception:
            continue
        for evento, gruppi in (dati.get("hooks") or {}).items():
            for g in gruppi if isinstance(gruppi, list) else []:
                for h in g.get("hooks", []):
                    c = str(h.get("command", ""))
                    if not c:
                        continue
                    if "\\" in c and "windows" not in p.lower():
                        comandi.append((p, evento, "percorso con barra rovesciata", c[:90]))
                    if re.search(r"(?<![\w.-])python(?![3\w])", c) and "PY=" not in c:
                        comandi.append((p, evento, "chiama python nudo, assente su molte distribuzioni", c[:90]))

    return {"singole": singole, "debito": note, "hook_non_eseguibili": hook_non_eseguibili,
            "sh_non_eseguibili": sh_non_eseguibili, "gitattributes_sh": ga_ok,
            "comandi": comandi, "capacita": len(forme), "eccezioni": len(scusate)}


def stampa(e: dict, compatto: bool) -> int:
    if "errore" in e:
        print("portabilita: " + e["errore"])
        return 0
    rilievi = (len(e["singole"]) + len(e["hook_non_eseguibili"])
               + len(e["sh_non_eseguibili"]) + len(e["comandi"])
               + (0 if e["gitattributes_sh"] else 1))
    if compatto:
        print("portabilita: %d rilievi (%d capacita' censite, %d eccezioni dichiarate)"
              % (rilievi, e["capacita"], e["eccezioni"]))
        if e["hook_non_eseguibili"]:
            print("   GRAVE: %d hook di git senza bit di esecuzione: su Linux git li salta in silenzio"
                  % len(e["hook_non_eseguibili"]))
        return 0
    if e["hook_non_eseguibili"]:
        print("GRAVE, hook di git senza bit di esecuzione (su Linux git li salta senza dirlo):")
        for p in sorted(e["hook_non_eseguibili"]):
            print("   " + p)
    if not e["gitattributes_sh"]:
        print("\nManca un .gitattributes che fissi `*.sh text eol=lf`: un clone su Windows con")
        print("conversione automatica rompe gli script di shell, e l'errore si vede solo su Linux.")
    if e["sh_non_eseguibili"]:
        print("\n%d script di shell senza bit di esecuzione:" % len(e["sh_non_eseguibili"]))
        for p in sorted(e["sh_non_eseguibili"])[:10]:
            print("   " + p)
    if e["comandi"]:
        print("\nComandi di hook non portabili:")
        for p, ev, perche, c in e["comandi"]:
            print("   %s [%s] %s\n      %s" % (p, ev, perche, c))
    if e["singole"]:
        print("\n%d capacita' in forma singola e non dichiarate, su %d censite:"
              % (len(e["singole"]), e["capacita"]))
        for chiave, est in e["singole"]:
            print("   %-70s solo %s" % (chiave, est))
        print("Se una di queste e' legittima, si dichiara in %s con la sua ragione;" % ECCEZIONI.as_posix())
        print("se invece dovrebbe esistere e non esiste ancora, va sotto `debito-noto`:")
        print("un rilievo che ricompare a ogni giro senza essere ne' risolto ne' dichiarato")
        print("insegna a ignorare il controllo, ed e' il modo in cui un presidio muore.")
    if e.get("debito"):
        print("\n%d capacita' in forma singola gia' note, dichiarate come debito da portare:"
              % len(e["debito"]))
        for chiave, est in e["debito"]:
            print("   %-70s solo %s" % (chiave, est))
    if rilievi == 0:
        print("portabilita: nessun rilievo nuovo su %d capacita' censite." % e["capacita"])
    return 1 if rilievi else 0


def autotest() -> int:
    import tempfile
    ok = True

    def caso(nome: str, cond: bool) -> None:
        nonlocal ok
        print(("ok   " if cond else "NO   ") + nome)
        ok = ok and cond

    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        subprocess.run(["git", "init", "-q"], cwd=r, capture_output=True)
        (r / ".githooks").mkdir()
        (r / ".githooks/pre-commit").write_text("#!/bin/sh\n", encoding="utf-8")
        (r / "a.ps1").write_text("", encoding="utf-8")
        (r / "b.sh").write_text("", encoding="utf-8")
        (r / "b.ps1").write_text("", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=r, capture_output=True)
        e = esamina(r)
        caso("l'hook senza bit di esecuzione e' rilevato", ".githooks/pre-commit" in e["hook_non_eseguibili"])
        caso("la capacita' in doppia forma non e' un rilievo",
             not any(k.endswith("/b.ps1") or k == "b.ps1" for k, _ in e["singole"]))
        caso("la capacita' in forma singola e' un rilievo",
             any(k == "a.ps1" for k, _ in e["singole"]))
        caso("l'assenza di .gitattributes e' rilevata", e["gitattributes_sh"] is False)
        (r / ".gitattributes").write_text("*.sh text eol=lf\n", encoding="utf-8")
        caso("un .gitattributes che copre gli script chiude il rilievo",
             esamina(r)["gitattributes_sh"] is True)
        (r / ".claude/templates/tools").mkdir(parents=True)
        (r / ECCEZIONI).write_text(json.dumps({"forme-singole": {"a.ps1": "di prova"}}),
                                   encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=r, capture_output=True)
        caso("una forma singola dichiarata non e' piu' un rilievo",
             not any(k == "a.ps1" for k, _ in esamina(r)["singole"]))
    print("\nautotest " + ("superato" if ok else "FALLITO"))
    return 0 if ok else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Che cosa funziona su un solo sistema operativo.")
    p.add_argument("--radice", default=".")
    p.add_argument("--hook", action="store_true", help="forma compatta, non blocca mai")
    p.add_argument("--autotest", action="store_true")
    a = p.parse_args(argv)
    if a.autotest:
        return autotest()
    esito = stampa(esamina(Path(a.radice)), a.hook)
    return 0 if a.hook else esito


if __name__ == "__main__":
    sys.exit(main())
