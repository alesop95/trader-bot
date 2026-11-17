#!/usr/bin/env python3
"""Riserva dei subagent sul limite del piano, per tutte le radici dei due agenti da terminale.

Perche' esiste. Il proprietario ha chiesto il 2026-11-16 che gli agenti non riempiano mai il
limite settimanale, per tenere quello spazio ad altro, e che cio' che vale per Claude Code valga
anche per Codex. In Claude Code la riserva la attua la mod `instradamento-modelli`, che legge dal
motore la percentuale usata e nega lo spawn. Codex non ha un punto equivalente dentro la sessione:
ha pero' due cose che bastano a un wrapper. Scrive nei propri file di sessione, a ogni risposta,
la percentuale usata delle due finestre del piano; e accetta all'avvio `--disable multi_agent` e `--disable multi_agent_v2`,
che toglie alla sessione gli strumenti con cui apre altri agenti. Questo strumento unisce le due:
`Avvia-Codex.ps1` gli chiede prima di partire se la soglia e' passata, e all'uscita gli fa
registrare l'ultima lettura prima che la pulizia cancelli le sessioni.

La soglia e' una sola per macchina e si scrive con un comando solo, per entrambi i client:
in `<radice Claude>/instradamento-modelli.json`, campo `riservaAgenti`, che la mod legge, e in
`<radice Codex>/riserva-agenti.json`, che legge questo strumento. Stessa forma nei due file.

Limiti, da conoscere. Per Codex la lettura e' quella dell'ultima sessione chiusa con il wrapper,
non di adesso: una finestra il cui azzeramento e' gia' passato non conta, una lettura assente
non nega. La decisione si prende all'avvio e vale per tutta la sessione. Una sessione Codex
avviata senza il wrapper non ha riserva.

Uso:
    python riserva-agenti.py stato                       quadro di tutte le radici, sola lettura
    python riserva-agenti.py imposta --settimanale 80    scrive la soglia in tutte le radici
    python riserva-agenti.py decidi --radice <CODEX_HOME>    JSON per il wrapper, esce sempre con 0
    python riserva-agenti.py registra --radice <CODEX_HOME>  salva l'ultima lettura dalle sessioni
    python riserva-agenti.py --autotest
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

FILE_CODEX = "riserva-agenti.json"
FILE_LETTURA = "riserva-ultima-lettura.json"
FILE_CLAUDE = "instradamento-modelli.json"
SPENTA = {"settimanale": 0, "cinqueOre": 0, "azione": "nega"}
# Le due finestre si riconoscono dalla durata dichiarata, non dalla posizione.
MINUTI = {"settimanale": 10080, "cinqueOre": 300}


def leggi_json(percorso: Path):
    try:
        return json.loads(percorso.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def scrivi_json(percorso: Path, dati) -> None:
    """Scrive conservando fine riga e BOM del file che c'era."""
    nl, bom = "\n", b""
    if percorso.is_file():
        vecchio = percorso.read_bytes()
        nl = "\r\n" if b"\r\n" in vecchio else "\n"
        bom = b"\xef\xbb\xbf" if vecchio.startswith(b"\xef\xbb\xbf") else b""
    testo = (json.dumps(dati, ensure_ascii=False, indent=2) + "\n").replace("\n", nl)
    percorso.write_bytes(bom + testo.encode("utf-8"))


def radici(casa: Path, prefisso: str) -> list:
    return sorted(p for p in casa.glob(prefisso + "*") if p.is_dir() and p.name[len(prefisso):].isdigit())


def cerca_limiti(nodo):
    """Il primo oggetto `rate_limits` dentro una riga di sessione, a qualunque profondita'."""
    if isinstance(nodo, dict):
        if isinstance(nodo.get("rate_limits"), dict):
            return nodo["rate_limits"]
        for v in nodo.values():
            trovato = cerca_limiti(v)
            if trovato is not None:
                return trovato
    elif isinstance(nodo, list):
        for v in nodo:
            trovato = cerca_limiti(v)
            if trovato is not None:
                return trovato
    return None


def finestre(limiti: dict) -> dict:
    """Da `rate_limits` di Codex a {settimanale: {usato, azzera}, cinqueOre: {...}}."""
    esito = {}
    for chiave in ("primary", "secondary"):
        f = (limiti or {}).get(chiave)
        if not isinstance(f, dict) or f.get("used_percent") is None:
            continue
        for nome, minuti in MINUTI.items():
            if f.get("window_minutes") == minuti:
                esito[nome] = {"usato": float(f["used_percent"]), "azzera": f.get("resets_at")}
    return esito


def ultima_lettura_dalle_sessioni(radice: Path):
    """L'ultima lettura dei limiti nella sessione piu' recente che ne porta una."""
    sessioni = radice / "sessions"
    if not sessioni.is_dir():
        return None
    for percorso in sorted(sessioni.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
        ultima = None
        try:
            with percorso.open(encoding="utf-8", errors="replace") as f:
                for riga in f:
                    if '"rate_limits"' not in riga:
                        continue
                    try:
                        limiti = cerca_limiti(json.loads(riga))
                    except ValueError:
                        continue
                    trovate = finestre(limiti) if limiti else {}
                    if trovate:
                        ultima = trovate
        except OSError:
            continue
        if ultima:
            return {"letto": int(percorso.stat().st_mtime), "finestre": ultima}
    return None


def registra(radice: Path) -> bool:
    lettura = ultima_lettura_dalle_sessioni(radice)
    if not lettura:
        return False
    scrivi_json(radice / FILE_LETTURA, lettura)
    return True


# Le due funzioni di delega di Codex 0.169: la prima e' dichiarata deprecata, la seconda stabile e
# spenta per difetto. Si spengono entrambe, perche' una riserva che ne chiude una sola smette di
# valere il giorno in cui il client accende l'altra.
SPEGNI_DELEGA = ("--disable", "multi_agent", "--disable", "multi_agent_v2")
# Il nome con cui l'hook PreToolUse di Codex vede l'avvio di un subagent. La documentazione letta
# il 2026-11-16 diceva spawn_agent; la prova dal vero del 2026-11-17 con Codex 0.169 ha registrato
# collaborationspawn_agent, cioe' il nome dello strumento con davanti quello del suo gruppo, senza
# separatore. Si riconosce quindi la desinenza, che copre il nome nudo, quello con il prefisso e
# un eventuale prefisso di altra forma; Agent resta per la forma di Claude Code.
STRUMENTI_DI_DELEGA = {"spawn_agent", "agent"}


def e_delega(nome) -> bool:
    n = str(nome or "").lower()
    return n == "agent" or n.endswith("spawn_agent")


def risposta_hook(motivo: str) -> dict:
    """Il diniego nella forma JSON che Codex legge dallo standard output, con uscita 0.

    La prova dal vero del 2026-11-17 su Windows ha mostrato che l'uscita 2 non arriva a Codex:
    lo strumento usciva con 2 e Codex riportava «hook exited with code 1», trattava l'hook come
    guasto e lasciava partire il subagent. Il codice si perde nella shell con cui Codex lancia il
    comando. La forma JSON, che la documentazione di Codex indica come preferita, non dipende dal
    codice di uscita."""
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": motivo}}


def hook(entrata, radice: Path, adesso: int):
    """Per un hook PreToolUse di Codex: (2, motivo) se l'avvio di un subagent va negato, altrimenti (0, "")."""
    if not e_delega((entrata or {}).get("tool_name")):
        return 0, ""
    d = decidi(leggi_json(radice / FILE_CODEX), ultima_lettura_dalle_sessioni(radice) or leggi_json(radice / FILE_LETTURA), adesso)
    if d["nega"]:
        return 2, "Subagent non avviato: " + d["motivo"] + ". Fai il lavoro in prima persona, oppure rimandalo."
    return 0, ""


def decidi(riserva, lettura, adesso: int) -> dict:
    """La decisione del wrapper. Senza soglia, senza lettura o a finestra azzerata non si nega."""
    riserva = dict(SPENTA, **(riserva or {}))
    for nome in MINUTI:
        try:
            soglia = float(riserva.get(nome) or 0)
        except (TypeError, ValueError):
            soglia = 0
        f = ((lettura or {}).get("finestre") or {}).get(nome)
        if soglia <= 0 or not f:
            continue
        if f.get("azzera") and int(f["azzera"]) <= adesso:
            continue
        if f["usato"] >= soglia:
            quale = "settimanale" if nome == "settimanale" else "delle cinque ore"
            quando = ""
            if f.get("azzera"):
                quando = ", la finestra si azzera il " + dt.datetime.fromtimestamp(int(f["azzera"])).strftime("%Y-%m-%d alle %H:%M")
            motivo = "il limite %s del piano era al %g%% all'ultima lettura, la riserva parte dal %g%%%s" % (quale, f["usato"], soglia, quando)
            nega = riserva.get("azione") != "avvisa"
            return {"oltre": True, "nega": nega, "motivo": motivo, "argomenti": list(SPEGNI_DELEGA) if nega else []}
    return {"oltre": False, "nega": False, "motivo": "", "argomenti": []}


def imposta(casa: Path, riserva: dict) -> list:
    """Scrive la stessa soglia in tutte le radici dei due client. Idempotente."""
    righe = []
    for radice in radici(casa, ".claude-account"):
        p = radice / FILE_CLAUDE
        dati = leggi_json(p)
        if dati is None:
            righe.append("%s: %s assente o illeggibile, non toccato (si crea con l'installatore di instradamento-modelli)" % (radice.name, FILE_CLAUDE))
            continue
        if dati.get("riservaAgenti") == riserva:
            righe.append("%s: invariata" % radice.name)
            continue
        dati["riservaAgenti"] = riserva
        scrivi_json(p, dati)
        righe.append("%s: scritta" % radice.name)
    for radice in radici(casa, ".codex-account"):
        p = radice / FILE_CODEX
        if leggi_json(p) == riserva:
            righe.append("%s: invariata" % radice.name)
            continue
        scrivi_json(p, riserva)
        righe.append("%s: scritta" % radice.name)
    return righe


def stato(casa: Path, adesso: int) -> list:
    righe = []
    for radice in radici(casa, ".claude-account"):
        dati = leggi_json(radice / FILE_CLAUDE) or {}
        r = dict(SPENTA, **(dati.get("riservaAgenti") or {}))
        righe.append("%-18s settimanale %g%%, cinque ore %g%%, azione %s; la lettura dei limiti e' della mod, dentro la sessione: /instradamento"
                     % (radice.name, r["settimanale"], r["cinqueOre"], r["azione"]))
    for radice in radici(casa, ".codex-account"):
        r = dict(SPENTA, **(leggi_json(radice / FILE_CODEX) or {}))
        lettura = leggi_json(radice / FILE_LETTURA)
        d = decidi(r, lettura, adesso)
        f = (lettura or {}).get("finestre") or {}
        letto = "nessuna lettura registrata"
        if f:
            letto = ", ".join("%s %g%%" % (k, v["usato"]) for k, v in sorted(f.items())) + " al " + \
                dt.datetime.fromtimestamp(int(lettura.get("letto") or 0)).strftime("%Y-%m-%d %H:%M")
        righe.append("%-18s settimanale %g%%, cinque ore %g%%, azione %s; %s; %s"
                     % (radice.name, r["settimanale"], r["cinqueOre"], r["azione"], letto,
                        "SUBAGENT SPENTI al prossimo avvio" if d["nega"] else ("oltre soglia, solo avviso" if d["oltre"] else "sotto soglia")))
    return righe or ["nessuna radice di account trovata in %s" % casa]


def autotest() -> int:
    esiti = []

    def caso(nome, ok, dettaglio=""):
        esiti.append(bool(ok))
        print(("ok    " if ok else "ROSSO ") + nome + ("" if ok else "  " + str(dettaglio)))

    limiti = {"primary": {"used_percent": 31.0, "window_minutes": 300, "resets_at": 2000},
              "secondary": {"used_percent": 85.0, "window_minutes": 10080, "resets_at": 5000}, "credits": {}}
    f = finestre(limiti)
    caso("le finestre si riconoscono dalla durata", f == {"cinqueOre": {"usato": 31.0, "azzera": 2000}, "settimanale": {"usato": 85.0, "azzera": 5000}}, f)
    caso("una finestra assente non produce una lettura", finestre({"primary": None, "secondary": None}) == {})
    lettura = {"letto": 900, "finestre": f}
    d = decidi({"settimanale": 80}, lettura, 1000)
    caso("oltre la soglia settimanale i subagent si spengono, con il motivo", d["nega"] and d["argomenti"] == ["--disable", "multi_agent", "--disable", "multi_agent_v2"] and "85%" in d["motivo"] and "80%" in d["motivo"], d)
    caso("sotto la soglia non si nega", not decidi({"settimanale": 90}, lettura, 1000)["oltre"])
    caso("in solo avviso si dichiara e non si spegne", decidi({"settimanale": 80, "azione": "avvisa"}, lettura, 1000) == dict(d, nega=False, argomenti=[]))
    caso("una finestra gia' azzerata non conta", not decidi({"settimanale": 80}, lettura, 6000)["oltre"])
    caso("senza lettura non si nega", not decidi({"settimanale": 80}, None, 1000)["oltre"])
    caso("senza soglia non si nega", not decidi(None, lettura, 1000)["oltre"] and not decidi({"settimanale": 0}, lettura, 1000)["oltre"])
    caso("la soglia delle cinque ore e' indipendente", decidi({"cinqueOre": 30}, lettura, 1000)["nega"] and "cinque ore" in decidi({"cinqueOre": 30}, lettura, 1000)["motivo"])

    base = Path(tempfile.mkdtemp(prefix="riserva-"))
    try:
        codex, claude, altro = base / ".codex-account1", base / ".claude-account1", base / ".claude-account2"
        (codex / "sessions" / "2026" / "11").mkdir(parents=True)
        claude.mkdir()
        altro.mkdir()
        (base / ".codex").mkdir()
        riga = {"type": "event_msg", "payload": {"type": "token_count", "rate_limits": limiti}}
        vecchia = dict(limiti, secondary={"used_percent": 10.0, "window_minutes": 10080, "resets_at": 5000})
        (codex / "sessions" / "2026" / "11" / "rollout-a.jsonl").write_text(
            json.dumps({"payload": {"rate_limits": vecchia}}) + "\nnon json\n" + json.dumps(riga) + "\n", encoding="utf-8")
        caso("la lettura registrata e' l'ultima della sessione", registra(codex) and leggi_json(codex / FILE_LETTURA)["finestre"]["settimanale"]["usato"] == 85.0)
        caso("una radice senza sessioni non registra niente e non fallisce", registra(claude) is False)
        (claude / FILE_CLAUDE).write_bytes(b'{\r\n  "modo": "instrada",\r\n  "agenti": {"Explore": "haiku"}\r\n}\r\n')
        r = {"settimanale": 80, "cinqueOre": 0, "azione": "nega"}
        prima = imposta(base, r)
        dopo = leggi_json(claude / FILE_CLAUDE)
        caso("imposta scrive in Claude senza perdere il resto e conservando il fine riga",
             dopo["riservaAgenti"] == r and dopo["modo"] == "instrada" and dopo["agenti"] == {"Explore": "haiku"} and b"\r\n" in (claude / FILE_CLAUDE).read_bytes(), dopo)
        caso("imposta scrive in Codex il file proprio", leggi_json(codex / FILE_CODEX) == r)
        caso("una radice Claude senza configurazione non viene creata a meta'", not (altro / FILE_CLAUDE).exists() and any("non toccato" in x for x in prima), prima)
        caso("la radice Codex di default, senza numero, non e' una radice di account", not (base / ".codex" / FILE_CODEX).exists())
        seconda = imposta(base, r)
        caso("imposta e' idempotente", sum("invariata" in x for x in seconda) == 2, seconda)
        codice, motivo = hook({"tool_name": "spawn_agent", "tool_input": {}}, codex, 1000)
        caso("l'hook nega l'avvio di un subagent oltre soglia, con il motivo", codice == 2 and "85%" in motivo, (codice, motivo))
        codice, _ = hook({"tool_name": "collaborationspawn_agent", "tool_input": {"agent_type": "elenca-file"}}, codex, 1000)
        caso("l'hook nega anche con il nome registrato dal vero da Codex 0.169, collaborationspawn_agent", codice == 2, codice)
        caso("il diniego si consegna come JSON di PreToolUse con decisione deny e il motivo",
             risposta_hook("x")["hookSpecificOutput"] == {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "x"})
        caso("l'hook lascia passare uno strumento che non e' di delega", hook({"tool_name": "Bash"}, codex, 1000) == (0, ""))
        caso("l'hook lascia passare l'attesa e i messaggi fra agenti, che non avviano niente",
             hook({"tool_name": "collaborationwait_agent"}, codex, 1000) == (0, "") and hook({"tool_name": "collaborationsend_message"}, codex, 1000) == (0, ""))
        caso("l'hook lascia passare tutto a finestra azzerata", hook({"tool_name": "Agent"}, codex, 9000) == (0, ""))
        caso("l'hook non nega in una radice senza soglia", hook({"tool_name": "spawn_agent"}, altro, 1000) == (0, ""))
        caso("lo stato dichiara i subagent spenti quando la lettura e' oltre soglia", any("SUBAGENT SPENTI" in x for x in stato(base, 1000)), stato(base, 1000))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print("%d prove, %d fallite" % (len(esiti), esiti.count(False)))
    return 1 if False in esiti else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("comando", nargs="?", choices=["stato", "imposta", "decidi", "registra", "hook"])
    ap.add_argument("--radice", help="radice di un account Codex, cioe' il suo CODEX_HOME")
    ap.add_argument("--casa", default=os.path.expanduser("~"), help="cartella che contiene le radici; per difetto il profilo utente")
    ap.add_argument("--settimanale", type=float)
    ap.add_argument("--cinque-ore", type=float, default=0)
    ap.add_argument("--azione", choices=["nega", "avvisa"], default="nega")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()
    if a.autotest:
        return autotest()
    adesso = int(dt.datetime.now().timestamp())
    if a.comando == "decidi":
        # Il wrapper non deve mai fermarsi per colpa di questo strumento: qualunque errore vale «non negare».
        try:
            radice = Path(a.radice)
            print(json.dumps(decidi(leggi_json(radice / FILE_CODEX), leggi_json(radice / FILE_LETTURA), adesso), ensure_ascii=False))
        except Exception:
            print(json.dumps({"oltre": False, "nega": False, "motivo": "", "argomenti": []}))
        return 0
    if a.comando == "hook":
        # Un hook che si rompe non deve fermare il client: qualunque errore vale «lascia passare».
        try:
            radice = Path(a.radice or os.environ.get("CODEX_HOME") or "")
            codice, motivo = hook(json.loads(sys.stdin.read() or "{}"), radice, adesso)
        except Exception:
            return 0
        if codice:
            print(json.dumps(risposta_hook(motivo), ensure_ascii=False))
            sys.stderr.write(motivo + "\n")
        return 0
    if a.comando == "registra":
        try:
            registra(Path(a.radice))
        except Exception:
            pass
        return 0
    if a.comando == "imposta":
        if a.settimanale is None:
            ap.error("imposta richiede --settimanale; zero spegne la soglia")
        def valore(x):
            return int(x) if float(x).is_integer() else x

        for riga in imposta(Path(a.casa), {"settimanale": valore(a.settimanale), "cinqueOre": valore(a.cinque_ore), "azione": a.azione}):
            print(riga)
        return 0
    for riga in stato(Path(a.casa), adesso):
        print(riga)
    return 0


if __name__ == "__main__":
    sys.exit(main())
