#!/usr/bin/env python3
"""Le lezioni che un progetto istanziato deve al template, visibili da entrambe le parti.

Perché esiste. Il 2026-10-19 il proprietario ha chiesto che un progetto istanziato
capisca da solo, mentre avanza, che cosa deve far risalire al template, e che il
template, riaperto, raccolga quel debito prima di aggiungere funzionalità nuove.
Fino a quel giorno il canale era una prescrizione (PROJECT-SYSTEM.md, sezione 16) e
un file di note mandato a mano da un repository all'altro: in una sola giornata un
progetto ne ha mandati quattro, e il proprietario ha dovuto fare da corriere.

Il meccanismo ha due registri e nessuna scrittura fra repository.

Nel progetto, `.claude/memory/lezioni-template.md`, versionato e del progetto: una
voce per lezione, `## L-001 - <data> - <titolo>`, con il testo sotto. La voce si
crea con `nuova` nel giro di lavoro in cui la lezione nasce, e la voce del work-log
di quel giro porta il campo `**Template:** L-001` oppure `**Template:** nessuna`.

Nel template, `.claude/templates/lezioni-recepite.json`, versionato: quali lezioni
di quale progetto sono entrate e con quale commit. Arriva in ogni progetto con
l'allineamento, perché sta sotto `.claude/templates/`, e da lì il progetto sa da sé
quali sue lezioni sono chiuse, senza che il template scriva nel progetto.

    python .claude/templates/tools/lezioni-template.py nuova "titolo" --testo "che cosa, misurato come"
    python .claude/templates/tools/lezioni-template.py controlla          # nel progetto, avvisa e non blocca
    python .claude/templates/tools/lezioni-template.py raccogli           # nel template, a inizio sessione
    python .claude/templates/tools/lezioni-template.py recepisci <progetto> L-001 --dove "file"
    python .claude/templates/tools/lezioni-template.py --autotest

`controlla` esce sempre con 0, salvo `--rigoroso`: una lezione non ancora risalita
non rende sbagliato il commit, e il suo compito è non far dimenticare una decisione
già presa, non prenderla al posto di chi scrive. `raccogli` legge l'elenco dei
progetti dal registro di allinea-tutti.ps1, compresi quelli nelle macchine
raggiungibili via SSH, ed esce con 0 anche quando trova lezioni aperte.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REGISTRO = Path(".claude") / "memory" / "lezioni-template.md"
RECEPITE = Path(".claude") / "templates" / "lezioni-recepite.json"
WORKLOG = Path(".claude") / "memory" / "progress.md"
VOCE = re.compile(r"^## (L-\d{3,}) - (\d{4}-\d{2}-\d{2}) - (.+?)\s*$", re.M)
ADOTTATO = re.compile(r"^Adottato il: (\d{4}-\d{2}-\d{2})", re.M)
VOCE_LOG = re.compile(r"^## (\d{4}-\d{2}-\d{2})\b(.*)$", re.M)
CAMPO = re.compile(r"^\*\*Template:\*\*\s*(.+)$", re.M)

TESTA = """# Lezioni per il template

> Le lezioni nate in questo progetto che valgono oltre il progetto, cioè che passano le due domande della sezione 16 di `.claude/PROJECT-SYSTEM.md`: restano vere tolti i nomi propri, e non sono già nella testa di chi lavora bene. Una voce per lezione, creata con `python .claude/templates/tools/lezioni-template.py nuova` nel giro di lavoro in cui la lezione nasce. Lo stato non si scrive qui: una lezione è recepita quando il template la elenca in `.claude/templates/lezioni-recepite.json`, che arriva con l'allineamento.

Adottato il: {data}
"""


def oggi() -> str:
    return dt.date.today().isoformat()


def nome_progetto(radice: Path) -> str:
    return radice.resolve().name


def leggi_voci(testo: str) -> list[dict]:
    voci = []
    trovate = list(VOCE.finditer(testo))
    for i, m in enumerate(trovate):
        fine = trovate[i + 1].start() if i + 1 < len(trovate) else len(testo)
        voci.append({"id": m.group(1), "data": m.group(2), "titolo": m.group(3),
                     "testo": testo[m.end():fine].strip()})
    return voci


def leggi_recepite(radice: Path) -> list[dict]:
    f = radice / RECEPITE
    if not f.is_file():
        return []
    return json.loads(f.read_text(encoding="utf-8"))


def chiuse_per(recepite: list[dict], progetto: str) -> dict[str, dict]:
    return {r["id"]: r for r in recepite if r.get("progetto") == progetto}


# --------------------------------------------------------------------------- nel progetto

def cmd_nuova(radice: Path, titolo: str, testo: str) -> str:
    f = radice / REGISTRO
    if not f.is_file():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(TESTA.format(data=oggi()), encoding="utf-8", newline="\n")
    attuale = f.read_text(encoding="utf-8")
    numeri = [int(v["id"][2:]) for v in leggi_voci(attuale)]
    nuovo = "L-%03d" % (max(numeri, default=0) + 1)
    titolo = " ".join(titolo.split())
    # Il corpo si conserva com'è, paragrafi, tabelle e blocchi di codice compresi: la prima
    # versione lo univa in una riga sola e un progetto istanziato ha visto un blocco recintato
    # diventare testo in linea, il 2026-10-20. Si normalizzano soltanto le fini riga.
    corpo = testo.replace("\r\n", "\n").replace("\r", "\n").strip("\n").rstrip()
    voce = "\n## %s - %s - %s\n\n%s\n" % (nuovo, oggi(), titolo, corpo or "Da descrivere: che cosa, misurato come, e perché vale oltre il progetto.")
    with f.open("a", encoding="utf-8", newline="\n") as h:
        h.write(voce)
    return nuovo


def esamina_progetto(radice: Path) -> dict:
    """Che cosa il progetto deve al template e dove il work-log non lo dice. Funzione pura sui file."""
    progetto = nome_progetto(radice)
    f = radice / REGISTRO
    testo = f.read_text(encoding="utf-8") if f.is_file() else ""
    voci = leggi_voci(testo)
    chiuse = chiuse_per(leggi_recepite(radice), progetto)
    aperte = [v for v in voci if v["id"] not in chiuse]
    m = ADOTTATO.search(testo)
    adottato = m.group(1) if m else None
    senza_campo, citazioni_rotte = [], []
    log = radice / WORKLOG
    ids = {v["id"] for v in voci}
    if adottato and log.is_file():
        lt = log.read_text(encoding="utf-8")
        intestazioni = list(VOCE_LOG.finditer(lt))
        for i, h in enumerate(intestazioni):
            if h.group(1) < adottato:
                continue
            fine = intestazioni[i + 1].start() if i + 1 < len(intestazioni) else len(lt)
            corpo = lt[h.end():fine]
            c = CAMPO.search(corpo)
            if not c:
                senza_campo.append(h.group(1) + h.group(2).rstrip())
                continue
            for rif in re.findall(r"L-\d{3,}", c.group(1)):
                if rif not in ids:
                    citazioni_rotte.append(rif)
    return {"progetto": progetto, "registro": f.is_file(), "adottato": adottato, "voci": voci,
            "aperte": aperte, "chiuse": chiuse, "senza_campo": senza_campo, "citazioni_rotte": citazioni_rotte}


def cmd_controlla(radice: Path, rigoroso: bool) -> int:
    e = esamina_progetto(radice)
    if not e["registro"]:
        print("lezioni-template: registro assente; la prima lezione lo crea con `lezioni-template.py nuova`")
        return 0
    avvisi = 0
    for v in e["aperte"]:
        print("lezione aperta %s del %s: %s" % (v["id"], v["data"], v["titolo"]))
    for x in e["senza_campo"]:
        avvisi += 1
        print("AVVISO: voce del work-log senza **Template:** -> %s" % x)
    for rif in e["citazioni_rotte"]:
        avvisi += 1
        print("AVVISO: il work-log cita %s, che il registro non ha" % rif)
    print("lezioni-template: %d aperte, %d recepite, %d avvisi" % (len(e["aperte"]), len(e["chiuse"]), avvisi))
    return 1 if (rigoroso and avvisi) else 0


# --------------------------------------------------------------------------- nel template

def leggi_remoto(prj: str, rel: str) -> str | None:
    m = re.match(r"^ssh://([^/]+)(/.*)$", prj)
    if not m:
        return None
    # Un tempo massimo per macchina: il 2026-10-20 `chiudi` è rimasto fermo su questa lettura.
    try:
        # -n e stdin chiuso: lanciato da un terminale interattivo, ssh ereditava la console e
        # restava in attesa sullo standard input, e con lui tutta la chiusura.
        r = subprocess.run(["ssh", "-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", m.group(1),
                            "cat '" + m.group(2).rstrip("/") + "/" + rel + "' 2>/dev/null"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           stdin=subprocess.DEVNULL, timeout=25)
    except subprocess.TimeoutExpired:
        return None
    return r.stdout if r.returncode == 0 else ""


def cmd_raccogli(template: Path, solo_locali: bool = False) -> int:
    reg = template / "_notes" / "allineamento" / "registro.json"
    if not reg.is_file():
        print("lezioni-template: registro di allinea-tutti assente, nessun elenco di progetti")
        return 0
    progetti = sorted(json.loads(reg.read_text(encoding="utf-8")).keys())
    if solo_locali:
        progetti = [p for p in progetti if not p.startswith("ssh://")]
    recepite = leggi_recepite(template)
    totale, con_debito, irraggiungibili = 0, 0, []
    for prj in progetti:
        if prj.startswith("ssh://"):
            testo = leggi_remoto(prj, REGISTRO.as_posix())
            nome = prj.rstrip("/").rsplit("/", 1)[-1]
        else:
            f = Path(prj) / REGISTRO
            testo = f.read_text(encoding="utf-8") if f.is_file() else ""
            nome = Path(prj).name
        if testo is None:
            irraggiungibili.append(prj)
            continue
        chiuse = chiuse_per(recepite, nome)
        aperte = [v for v in leggi_voci(testo) if v["id"] not in chiuse]
        if aperte:
            con_debito += 1
            print("%s  (%s)" % (nome, prj))
            for v in aperte:
                print("  %s del %s: %s" % (v["id"], v["data"], v["titolo"]))
            totale += len(aperte)
    print("\nlezioni aperte verso il template: %d in %d progetti su %d" % (totale, con_debito, len(progetti)))
    if totale:
        print("Prima di una funzionalità nuova si recepiscono: si legge la voce nel registro del progetto,")
        print("la si porta nel template se passa le due domande della sezione 16, e la si chiude con `recepisci`.")
    return 0


def cmd_recepisci(template: Path, progetto: str, ident: str, commit: str, dove: str) -> None:
    f = template / RECEPITE
    dati = leggi_recepite(template)
    dati = [r for r in dati if not (r["progetto"] == progetto and r["id"] == ident)]
    dati.append({"progetto": progetto, "id": ident, "commit": commit, "data": oggi(), "dove": dove})
    dati.sort(key=lambda r: (r["progetto"], r["id"]))
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(dati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------- prove

def autotest() -> int:
    casi = rossi = 0

    def caso(nome: str, ok: bool) -> None:
        nonlocal casi, rossi
        casi += 1
        rossi += 0 if ok else 1
        print(("ok   " if ok else "ROSSO ") + nome)

    with tempfile.TemporaryDirectory() as d:
        prj = Path(d) / "progetto-prova"
        (prj / ".claude" / "memory").mkdir(parents=True)
        caso("senza registro il controllo non blocca", cmd_controlla(prj, False) == 0)
        a = cmd_nuova(prj, "una  lezione", "misurata così")
        b = cmd_nuova(prj, "un'altra", "")
        caso("le lezioni si numerano in ordine", (a, b) == ("L-001", "L-002"))
        caso("il registro nasce con la data di adozione", ADOTTATO.search((prj / REGISTRO).read_text(encoding="utf-8")) is not None)
        strutturato = "Primo paragrafo.\n\nSecondo paragrafo.\n\n```markdown\n| A | B |\n|---|---|\n```"
        altro = Path(d) / "struttura"
        (altro / ".claude" / "memory").mkdir(parents=True)
        c3 = cmd_nuova(altro, "con struttura", strutturato)
        voce3 = [v for v in leggi_voci((altro / REGISTRO).read_text(encoding="utf-8")) if v["id"] == c3][0]
        caso("paragrafi e blocchi di codice del corpo restano com'erano", voce3["testo"] == strutturato)
        ad = ADOTTATO.search((prj / REGISTRO).read_text(encoding="utf-8")).group(1)
        (prj / WORKLOG).write_text(
            "# Work-log\n\n## %s - passo con lezione\n\nTesto.\n\n**Template:** L-001, l'allineamento non sincronizza Codex\n\n"
            "## %s - passo senza campo\n\nTesto.\n\n## %s - passo che cita una lezione inesistente\n\n**Template:** L-009\n\n"
            "## 2000-01-01 - voce anteriore all'adozione\n\nNiente campo, e va bene.\n" % (ad, ad, ad), encoding="utf-8")
        e = esamina_progetto(prj)
        caso("due lezioni aperte finché il template non le recepisce", len(e["aperte"]) == 2)
        caso("una voce del work-log senza campo si segnala", len(e["senza_campo"]) == 1 and "senza campo" in e["senza_campo"][0])
        caso("una voce anteriore all'adozione non si segnala", not any("anteriore" in x for x in e["senza_campo"]))
        caso("una citazione a una lezione inesistente si segnala", e["citazioni_rotte"] == ["L-009"])
        caso("il controllo avvisa ma non blocca", cmd_controlla(prj, False) == 0)
        caso("con --rigoroso gli avvisi bloccano", cmd_controlla(prj, True) == 1)
        cmd_recepisci(prj, "progetto-prova", "L-001", "abc1234", "allinea-tutti.ps1")
        e = esamina_progetto(prj)
        caso("la lezione recepita dal template si chiude da sé nel progetto", [v["id"] for v in e["aperte"]] == ["L-002"])
        caso("un altro progetto con lo stesso numero non si chiude", not chiuse_per(leggi_recepite(prj), "altro-progetto"))
        tpl = Path(d) / "template"
        (tpl / "_notes" / "allineamento").mkdir(parents=True)
        (tpl / "_notes" / "allineamento" / "registro.json").write_text(json.dumps({str(prj): {}}), encoding="utf-8")
        (tpl / RECEPITE).parent.mkdir(parents=True)
        (tpl / RECEPITE).write_text(json.dumps([{"progetto": "progetto-prova", "id": "L-001", "commit": "x", "data": "x", "dove": "x"}]), encoding="utf-8")
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_raccogli(tpl)
        out = buf.getvalue()
        caso("il template raccoglie le sole lezioni non recepite", "L-002" in out and "L-001" not in out and "1 in 1 progetti" in out)
    print("\n%d casi superati su %d" % (casi - rossi, casi))
    return 1 if rossi else 0


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Le lezioni che un progetto deve al template.")
    p.add_argument("--autotest", action="store_true")
    p.add_argument("--radice", default=".", help="radice del progetto o del template")
    sub = p.add_subparsers(dest="comando")
    pn = sub.add_parser("nuova", help="registra una lezione nel progetto")
    pn.add_argument("titolo")
    pn.add_argument("--testo", default="")
    pn.add_argument("--testo-file", dest="testo_file", help="file Markdown con il corpo, per i corpi lunghi o strutturati")
    pc = sub.add_parser("controlla", help="nel progetto: lezioni aperte e work-log senza campo")
    pc.add_argument("--rigoroso", action="store_true")
    prc = sub.add_parser("raccogli", help="nel template: le lezioni aperte di tutti i progetti")
    prc.add_argument("--solo-locali", action="store_true", dest="solo_locali",
                     help="senza le macchine via SSH, per i controlli che devono restare veloci")
    pr = sub.add_parser("recepisci", help="nel template: chiude una lezione recepita")
    pr.add_argument("progetto")
    pr.add_argument("id")
    # Facoltativo di proposito: nel template si recepisce prima di committare, nello stesso
    # commit della correzione, quindi lo SHA non esiste ancora; quel commit si ritrova con
    # `git log -1 -- .claude/templates/lezioni-recepite.json`.
    pr.add_argument("--commit", default="")
    pr.add_argument("--dove", default="")
    a = p.parse_args(argv)
    if a.autotest:
        return autotest()
    radice = Path(a.radice)
    if a.comando == "nuova":
        testo = Path(a.testo_file).read_text(encoding="utf-8") if a.testo_file else a.testo
        print("registrata " + cmd_nuova(radice, a.titolo, testo) + " in " + str(REGISTRO))
        return 0
    if a.comando == "controlla":
        return cmd_controlla(radice, a.rigoroso)
    if a.comando == "raccogli":
        return cmd_raccogli(radice, a.solo_locali)
    if a.comando == "recepisci":
        cmd_recepisci(radice, a.progetto, a.id, a.commit, a.dove)
        print("recepita %s %s" % (a.progetto, a.id))
        return 0
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
