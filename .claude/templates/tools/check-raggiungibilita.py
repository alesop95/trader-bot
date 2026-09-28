#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifica che ogni capacità a scelta del template sia raggiungibile da un gate.

Perché serve
------------
Il template cresce per aggiunte: una regola nuova, una skill nuova, un pacchetto nuovo. Ciascuna
nasce da un caso reale e funziona, ma una capacità che si sceglie esiste per chi avvia o allinea
un progetto soltanto se un punto d'ingresso gliela propone: l'inizializzazione, l'allineamento,
uno dei gate, o l'indice `CLAUDE.md` che il progetto riceve. Una capacità che nessun punto
d'ingresso nomina non viene proposta a nessuno, e questo è indistinguibile dall'averla esclusa
di proposito. Il caso che ha fatto nascere questo controllo: il 2026-09-23 la skill
`studio-didattico`, dichiaratamente opzionale, non era nominata da nessun gate, quindi nessun
progetto l'avrebbe mai adottata se non per caso.

Che cosa controlla
------------------
Per ogni regola sotto `.claude/rules/` e ogni skill sotto `.claude/skills/` cerca il nome in
almeno uno dei PUNTI_DI_INGRESSO. Le capacità sempre attive, che non si scelgono perché valgono
in ogni progetto, non devono essere proposte da nessuno: stanno nell'elenco dichiarato
SEMPRE_ATTIVE, ciascuna con il motivo, così che l'esenzione sia una decisione scritta e non una
dimenticanza. Una capacità nuova che non sta nell'elenco e che nessun punto d'ingresso nomina
fa fallire il controllo. I pacchetti sotto `.claude/templates/` sono coperti da
`check-catalogo.py`, che verifica che ciascuno abbia una voce nel catalogo attraversato dal gate
dei pacchetti.

Che cosa non controlla
----------------------
Controlla che una capacità sia nominata, non che sia spiegata bene. Il principio della sezione
23 di `PROJECT-SYSTEM.md` chiede che il gate spieghi quando conviene una capacità e che cosa
comporta rispetto alle alternative: questo strumento distingue il silenzio dalla presenza, non
una buona spiegazione da una mediocre, e la qualità resta affidata a chi scrive il gate.

Vale per il repository del template, riconosciuto dalla presenza dei due prompt di
istanziazione. In un progetto istanziato non ha oggetto, perché lì le capacità sono già state
scelte, e lo dichiara invece di fallire.

Uso
---
    python .claude/templates/tools/check-raggiungibilita.py
    python .claude/templates/tools/check-raggiungibilita.py --radice <dir>
    python .claude/templates/tools/check-raggiungibilita.py --self-test

Esce con codice 1 se almeno una capacità a scelta non è raggiungibile, 0 altrimenti.
"""

import argparse
import io
import os
import re
import shutil
import sys
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PUNTI_DI_INGRESSO = [
    os.path.join(".claude", "skills", "init-project-system", "SKILL.md"),
    os.path.join(".claude", "PROMPT-nuovo-progetto.md"),
    os.path.join(".claude", "PROMPT-allinea-progetto-esistente.md"),
    os.path.join(".claude", "skills", "gate-pacchetti", "SKILL.md"),
    os.path.join(".claude", "skills", "separazione-ambienti", "SKILL.md"),
    os.path.join(".claude", "templates", "PACKAGES.md"),
    os.path.join(".claude", "templates", "CLAUDE.md"),
]

MARCATORE_BUNDLE = os.path.join(".claude", "PROMPT-nuovo-progetto.md")

# Le capacità che non si scelgono, con il motivo. Aggiungerne una è una decisione: significa
# dichiarare che vale in ogni progetto e che nessun gate deve proporla.
SEMPRE_ATTIVE = {
    "regola:chat-non-e-memoria": "persistenza di ciò che nasce in sessione, vale in ogni progetto",
    "regola:git-commands-format": "forma dei comandi consegnati all'utente, vale in ogni progetto",
    "regola:git-identity-and-repo": "identità git locale, vale in ogni progetto",
    "regola:interaction-style": "stile di documentazione e interazione, vale in ogni progetto",
    "regola:manual-screenshots": "riscontro visivo dei passi manuali, vale in ogni progetto",
    "regola:security-permissions": "modalità di permesso e sandbox, vale in ogni sessione",
    "regola:token-economy": "economia del contesto, vale in ogni sessione",
}


def capacita(radice):
    """Le regole e le skill presenti sul disco, come chiavi 'regola:nome' e 'skill:nome'."""
    trovate = []
    regole = os.path.join(radice, ".claude", "rules")
    if os.path.isdir(regole):
        for f in sorted(os.listdir(regole)):
            if f.endswith(".md"):
                trovate.append("regola:" + f[:-3])
    skill = os.path.join(radice, ".claude", "skills")
    if os.path.isdir(skill):
        for d in sorted(os.listdir(skill)):
            if os.path.isfile(os.path.join(skill, d, "SKILL.md")):
                trovate.append("skill:" + d)
    return trovate


def testo_ingressi(radice):
    parti = []
    for relativo in PUNTI_DI_INGRESSO:
        p = os.path.join(radice, relativo)
        if os.path.isfile(p):
            parti.append(io.open(p, encoding="utf-8", errors="replace").read())
    return "\n".join(parti)


def nominata(nome, testo):
    # Il nome come parola intera: `riprendi` non deve contare dentro `riprendila`, e un nome
    # con trattini non deve contare dentro un nome più lungo che lo contiene.
    return re.search(r"(?<![\w-])" + re.escape(nome) + r"(?![\w-])", testo) is not None


def verifica(radice):
    """Ritorna (irraggiungibili, esenzioni_orfane)."""
    testo = testo_ingressi(radice)
    presenti = capacita(radice)
    irraggiungibili = [c for c in presenti
                       if c not in SEMPRE_ATTIVE and not nominata(c.split(":", 1)[1], testo)]
    orfane = [c for c in SEMPRE_ATTIVE if c not in presenti]
    return irraggiungibili, orfane


def self_test():
    esiti = []

    def prova(nome, condizione, dettaglio=""):
        esiti.append((nome, bool(condizione), dettaglio))

    tmp = tempfile.mkdtemp(prefix="check-raggiungibilita-")
    try:
        os.makedirs(os.path.join(tmp, ".claude", "rules"))
        os.makedirs(os.path.join(tmp, ".claude", "skills", "init-project-system"))
        os.makedirs(os.path.join(tmp, ".claude", "skills", "nascosta"))
        io.open(os.path.join(tmp, MARCATORE_BUNDLE), "w", encoding="utf-8").write(
            "Esegui la regola `a-scelta` quando serve, e la skill `corta-lunga`.\n")
        io.open(os.path.join(tmp, ".claude", "skills", "init-project-system", "SKILL.md"), "w",
                encoding="utf-8").write("Procedura.\n")
        io.open(os.path.join(tmp, ".claude", "skills", "nascosta", "SKILL.md"), "w",
                encoding="utf-8").write("Nessuno mi nomina.\n")
        io.open(os.path.join(tmp, ".claude", "rules", "a-scelta.md"), "w",
                encoding="utf-8").write("# Regola\n")
        io.open(os.path.join(tmp, ".claude", "rules", "corta.md"), "w",
                encoding="utf-8").write("# Regola\n")
        io.open(os.path.join(tmp, ".claude", "rules", "chat-non-e-memoria.md"), "w",
                encoding="utf-8").write("# Regola\n")

        irr, orf = verifica(tmp)
        prova("una skill che nessun ingresso nomina si segnala", "skill:nascosta" in irr, str(irr))
        prova("negativo: una regola nominata da un ingresso non si segnala",
              "regola:a-scelta" not in irr, str(irr))
        # Il difetto che questa prova pianta: un confronto per sottostringa conterebbe la regola
        # `corta` come nominata perché il testo nomina `corta-lunga`.
        prova("un nome corto non conta come nominato dentro la menzione di un nome più lungo",
              "regola:corta" in irr, str(irr))
        prova("negativo: una capacità sempre attiva non si segnala anche se nessuno la nomina",
              "regola:chat-non-e-memoria" not in irr, str(irr))
        prova("un'esenzione per una capacità che non esiste più si segnala",
              "regola:interaction-style" in orf, str(orf))
        prova("una skill non è raggiungibile solo perché è essa stessa un punto d'ingresso",
              "skill:init-project-system" in irr, str(irr))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    larghezza = max(len(n) for n, _, _ in esiti)
    falliti = 0
    for nome, ok, dettaglio in esiti:
        if not ok:
            falliti += 1
        print("  %s  %s%s" % (nome.ljust(larghezza), "ok" if ok else "FALLITO",
                              ("  " + dettaglio[:160]) if (dettaglio and not ok) else ""))
    print("")
    print("%d prove, %d fallite." % (len(esiti), falliti))
    return 1 if falliti else 0


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--radice", default=".", help="radice del repository del template")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        return self_test()
    if not os.path.isfile(os.path.join(a.radice, MARCATORE_BUNDLE)):
        print("check-raggiungibilita: non è il repository del template (manca %s); in un "
              "progetto istanziato le capacità sono già state scelte e non c'è niente da "
              "verificare." % MARCATORE_BUNDLE)
        return 0
    irr, orf = verifica(a.radice)
    for c in irr:
        print("  %s non è nominata da nessun punto d'ingresso: nessun gate la propone, e per chi "
              "avvia o allinea un progetto non esiste. Va proposta da un gate, oppure dichiarata "
              "in SEMPRE_ATTIVE con il motivo." % c)
    for c in orf:
        print("  %s è dichiarata in SEMPRE_ATTIVE ma non esiste più sul disco: l'esenzione va "
              "tolta." % c)
    n = len(capacita(a.radice))
    print("%d capacità esaminate, %d sempre attive dichiarate" % (n, len(SEMPRE_ATTIVE)))
    print("check-raggiungibilita: %d problemi" % (len(irr) + len(orf)))
    return 1 if (irr or orf) else 0


if __name__ == "__main__":
    sys.exit(main())
