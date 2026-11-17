#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera docs/COME-SI-USA.md, la pagina d'ingresso: che cosa si usa, quando e come, in una riga per cosa.

Perché esiste
-------------
Il 2026-11-16 la documentazione del template pesava circa settecentomila caratteri in sei
documenti, e il proprietario ha chiesto di renderla leggibile: come si usa, e come si sfrutta
ogni strumento e ogni skill. Riscrivere quei documenti avrebbe prodotto una settima versione
da tenere allineata a mano. Questa pagina non riscrive niente: è una vista corta, generata dal
disco, che per ogni pacchetto, skill e strumento dà una riga con quando serve e come si usa, e
rimanda al documento lungo per il resto. È il posto da cui si parte; `docs/RIFERIMENTO.md`
resta il posto dove si legge tutto.

Che cosa legge
--------------
Le fasi d'uso da `.claude/templates/guida-grafica.json`; i comandi che digita la persona e le
regole d'uso parsimonioso da `.claude/templates/come-si-usa.json`, che sono autorati perché sono
un giudizio; pacchetti, skill e strumenti con le funzioni di `riferimento.py`, quindi dal
catalogo, dalla cartella delle skill e da quella degli strumenti. Un pacchetto nuovo compare
senza che nessuno tocchi questa pagina. Lo strumento si ferma se un comando autorato nomina uno
strumento che non esiste, perché una pagina d'ingresso con un comando sbagliato è peggio della
sua assenza.

Uso
---
    python .claude/templates/tools/come-si-usa.py --scrivi
    python .claude/templates/tools/come-si-usa.py --check
    python .claude/templates/tools/come-si-usa.py --autotest
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

DATI = ".claude/templates/come-si-usa.json"
FASI = ".claude/templates/guida-grafica.json"
VOCI = ".claude/templates/riferimento-voci.json"
CATALOGO = ".claude/templates/PACKAGES.md"
USCITA = "docs/COME-SI-USA.md"


def modulo_riferimento():
    spec = importlib.util.spec_from_file_location("riferimento", Path(__file__).with_name("riferimento.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def prima_frase(testo: str, tetto: int = 170) -> str:
    """La prima frase di un testo, senza spezzare un nome di file o un numero con il punto."""
    testo = re.sub(r"\s+", " ", testo or "").strip()
    m = re.search(r"[.;](?= [A-ZÈÀ`]|$)", testo)
    frase = testo[:m.start()] if m and m.start() > 25 else testo
    if len(frase) > tetto:
        frase = frase[:tetto].rsplit(" ", 1)[0].rstrip(",:") + " [...]"
    return frase.replace("|", "\\|")


def strumenti_nominati(comando: str) -> list:
    return re.findall(r"[A-Za-z0-9_-]+\.(?:py|ps1|sh)", comando)


def problemi(dati: dict, nomi_strumenti: set, nomi_skill: set) -> list:
    guasti = []
    for c in dati.get("comandi", []):
        for campo in ("situazione", "comando", "nota"):
            if not c.get(campo):
                guasti.append("un comando non ha il campo `%s`: %s" % (campo, c))
        for s in strumenti_nominati(c.get("comando", "")):
            if s not in nomi_strumenti:
                guasti.append("il comando `%s` nomina lo strumento `%s`, che non esiste" % (c.get("comando"), s))
        m = re.match(r"/([a-z0-9-]+)", c.get("comando", ""))
        if m and m.group(1) not in nomi_skill:
            guasti.append("il comando `%s` nomina la skill `%s`, che non esiste" % (c.get("comando"), m.group(1)))
    for r in dati.get("risparmio", []):
        if not r.get("regola") or not r.get("perche"):
            guasti.append("una regola di risparmio è incompleta: %s" % r)
    return guasti


def genera(dati: dict, fasi: list, voci: list, skill: list, strumenti: list, testi: dict) -> str:
    r = []
    r.append("# Come si usa il template")
    r.append("")
    r.append("> Pagina d'ingresso, generata da `.claude/templates/tools/come-si-usa.py` e fermata da `chiudi` quando resta indietro: non si modifica a mano. Dà una riga per ogni cosa che il template offre, con quando serve e come si usa. Il perché di ogni scelta, le fonti e i casi stanno nei documenti lunghi elencati in fondo, e questa pagina vi rimanda invece di ripeterli.")
    r.append("")
    r.append("## Il ciclo, in sei fasi")
    r.append("")
    r.append("| Fase | Quando | Con che cosa | Che cosa ne esce |")
    r.append("|---|---|---|---|")
    for f in fasi:
        r.append("| %s | %s | %s | %s |" % (f["titolo"], f["quando"], ", ".join("`%s`" % s for s in f["strumenti"]), f["esito"]))
    r.append("")
    r.append("La stessa cosa come grafico, con l'intreccio fra gli strumenti, sta in `docs/guida-grafica.html`.")
    r.append("")
    r.append("## Che cosa digiti tu")
    r.append("")
    r.append("Quasi tutto parte da solo o lo fa l'agente. Questi sono i comandi che restano a te, per situazione. Gli strumenti stanno in `tools/` nel progetto e in `.claude/templates/tools/` nel template; `chiudi` è il nome con cui il profilo del terminale chiama `chiudi-sessione`.")
    r.append("")
    r.append("| Situazione | Comando | Che cosa fa |")
    r.append("|---|---|---|")
    for c in dati["comandi"]:
        r.append("| %s | `%s` | %s |" % (c["situazione"], c["comando"], c["nota"]))
    r.append("")
    r.append("## Usarlo spendendo poco")
    r.append("")
    r.append("Le regole con cui il template tiene basso il consumo di token, ciascuna con la ragione. Il testo normativo è `.claude/rules/token-economy.md`; lo strumento che le attua per i subagent è il pacchetto `instradamento-modelli`.")
    r.append("")
    r.append("| Regola | Perché |")
    r.append("|---|---|")
    for x in dati["risparmio"]:
        r.append("| %s | %s |" % (x["regola"], x["perche"]))
    r.append("")
    r.append("## Le skill di sistema")
    r.append("")
    r.append("Si caricano quando la loro situazione si presenta, oppure si invocano per nome. In Claude Code con `/nome`, in Codex con `$nome`.")
    r.append("")
    r.append("| Skill | Che cosa fa | Come si usa |")
    r.append("|---|---|---|")
    for s in skill:
        come = (testi.get("skill:" + s["nome"]) or {}).get("come", "")
        r.append("| `%s` | %s | %s |" % (s["nome"], prima_frase(s["descrizione"]), prima_frase(come)))
    r.append("")
    r.append("## I pacchetti, per settore")
    r.append("")
    r.append("Un pacchetto non è attivo finché il gate non lo propone e tu non rispondi. La colonna «Quando» è il segnale con cui il gate lo riconosce; «Quando no» è la ragione per rifiutarlo. La riga completa di ciascuno, con le fonti, sta in `docs/RIFERIMENTO.md`.")
    settore = None
    for v in voci:
        if v["settore"] != settore:
            settore = v["settore"]
            r.append("")
            r.append("### %s" % settore)
            r.append("")
            r.append("| Pacchetto | Quando | Come si usa | Quando no |")
            r.append("|---|---|---|---|")
        t = testi.get("pacchetto:" + v["nome"]) or {}
        r.append("| `%s` | %s | %s | %s |" % (v["nome"], prima_frase(v["quando"]), prima_frase(t.get("come", "")), prima_frase(t.get("quando_no", ""))))
    r.append("")
    r.append("## Gli strumenti")
    r.append("")
    r.append("Quelli che `chiudi` e gli hook lanciano da sé non vanno ricordati: sono qui per sapere che esistono. La descrizione completa di ciascuno sta in `.claude/templates/tools/README.md`.")
    r.append("")
    r.append("| Strumento | Che cosa fa |")
    r.append("|---|---|")
    for s in strumenti:
        r.append("| `%s` | %s |" % (s["nome"], prima_frase(s["descrizione"]) or "Vedi il README degli strumenti"))
    r.append("")
    r.append("## Dove si legge il resto")
    r.append("")
    r.append("| Per sapere | Si apre |")
    r.append("|---|---|")
    r.append("| Con quale cadenza si fa che cosa, e quale leva tirare davanti a un sintomo | `GUIDA-USO.md` |")
    r.append("| Tutto di ogni skill, pacchetto, strumento e fonte: come, perché, quando no | `docs/RIFERIMENTO.md` |")
    r.append("| Il flusso come grafico, per fasi e per settore | `docs/guida-grafica.html` |")
    r.append("| Che cosa è deciso e non ancora pronto | `docs/FILONI.md` |")
    r.append("| Lo standard del sistema, sezione per sezione | `.claude/PROJECT-SYSTEM.md` |")
    r.append("| Da dove viene ogni cosa e se è cambiata a monte | `.claude/templates/fonti-a-monte.md` |")
    r.append("")
    return "\n".join(r)


def carica(radice: Path):
    rif = modulo_riferimento()
    dati = json.loads((radice / DATI).read_text(encoding="utf-8"))
    fasi = json.loads((radice / FASI).read_text(encoding="utf-8"))["fasi"]
    testi = json.loads((radice / VOCI).read_text(encoding="utf-8"))
    voci = rif.catalogo((radice / CATALOGO).read_text(encoding="utf-8-sig"))
    return dati, fasi, voci, rif.skill_di_sistema(radice), rif.strumenti(radice), testi


def autotest() -> int:
    esiti = []

    def caso(nome, ok, dettaglio=""):
        esiti.append(bool(ok))
        print(("ok    " if ok else "ROSSO ") + nome + ("" if ok else "  " + str(dettaglio)))

    caso("la prima frase si ferma al punto seguito da una maiuscola", prima_frase("Fa una cosa precisa e la fa bene. Poi ne fa un'altra.") == "Fa una cosa precisa e la fa bene")
    caso("un nome di file con il punto non spezza la frase", "tools/chiudi.ps1 e si ferma" in prima_frase("Lancia sempre tools/chiudi.ps1 e si ferma. Fine."))
    lunga = prima_frase("parola " * 80)
    caso("una frase lunga viene troncata a una parola intera e lo dichiara", lunga.endswith("[...]") and len(lunga) < 190, lunga)
    caso("la barra verticale viene protetta, perche' romperebbe la tabella", "\\|" in prima_frase("Sceglie fra a | b quando serve davvero"))
    buoni = {"comandi": [{"situazione": "x", "comando": "python tools/a.py --ora", "nota": "y"}, {"situazione": "x", "comando": "/riprendi", "nota": "y"}],
             "risparmio": [{"regola": "r", "perche": "p"}]}
    caso("dati completi non danno problemi", problemi(buoni, {"a.py"}, {"riprendi"}) == [])
    caso("un comando che nomina uno strumento inesistente e' un problema", any("non esiste" in g for g in problemi(buoni, set(), {"riprendi"})))
    caso("un comando che nomina una skill inesistente e' un problema", any("skill" in g for g in problemi(buoni, {"a.py"}, set())))
    caso("un comando senza nota e' un problema", problemi({"comandi": [{"situazione": "x", "comando": "chiudi"}]}, set(), set()) != [])
    pagina = genera(buoni, [{"titolo": "Aprire", "quando": "sempre", "strumenti": ["riprendi"], "esito": "si sa"}],
                    [{"nome": "p1", "settore": "S", "quando": "Serve quando il progetto ha un sito pubblico. Poi no.", "cosa_fa": "c"}],
                    [{"nome": "riprendi", "descrizione": "Riapre."}], [{"nome": "a.py", "descrizione": "Fa a."}],
                    {"pacchetto:p1": {"come": "Si lancia una volta dalla radice del progetto. Fine.", "quando_no": "Mai dove il sito non ha visitatori. Fine."}})
    caso("la pagina porta il pacchetto sotto il suo settore con le tre colonne",
         "### S" in pagina and "| `p1` | Serve quando il progetto ha un sito pubblico | Si lancia una volta dalla radice del progetto | Mai dove il sito non ha visitatori |" in pagina, pagina[-900:])
    caso("la pagina dichiara di essere generata", "non si modifica a mano" in pagina)
    print("%d prove, %d fallite" % (len(esiti), esiti.count(False)))
    return 1 if False in esiti else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--radice", default=".")
    ap.add_argument("--scrivi", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()
    if a.autotest:
        return autotest()
    radice = Path(a.radice).resolve()
    if not (radice / DATI).is_file():
        print("come-si-usa: qui non ci sono i dati del template; niente da fare.")
        return 0
    dati, fasi, voci, skill, strumenti, testi = carica(radice)
    guasti = problemi(dati, {s["nome"] for s in strumenti}, {s["nome"] for s in skill})
    for g in guasti:
        print("come-si-usa: " + g)
    if guasti:
        return 1
    pagina = genera(dati, fasi, voci, skill, strumenti, testi)
    dest = radice / USCITA
    if a.scrivi:
        dest.write_bytes(pagina.encode("utf-8"))
        print("scritto %s: %d caratteri, %d comandi, %d skill, %d pacchetti, %d strumenti" % (USCITA, len(pagina), len(dati["comandi"]), len(skill), len(voci), len(strumenti)))
        return 0
    attuale = dest.read_bytes().decode("utf-8").replace("\r\n", "\n") if dest.is_file() else ""
    if attuale != pagina:
        print("come-si-usa: %s non e' allineata ai dati; rigenerare con --scrivi" % USCITA)
        return 1 if a.check else 0
    print("come-si-usa: allineata")
    return 0


if __name__ == "__main__":
    sys.exit(main())
