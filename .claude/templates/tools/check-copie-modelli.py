#!/usr/bin/env python3
"""Confronta ogni strumento istanziato con il suo modello sotto .claude/templates/.

Perche' serve. Un progetto che adotta questo standard copia gli strumenti condivisi dal
bundle dentro la propria anatomia: un modello che sta in
`.claude/templates/<pacchetto>/tools/<file>` diventa `tools/<file>`, e uno che sta in
`.claude/templates/<pacchetto>/rules/<file>` diventa `.claude/rules/<file>`. Dal momento
della copia le due esistono in parallelo, e niente le tiene insieme: si correggono nella
copia perche' e' quella che gira, e il modello resta indietro senza che nessuno lo veda.

Il modo in cui questo difetto si manifesta e' il peggiore possibile, perche' non si
manifesta affatto nel repository dove e' nato. Il 2026-09-16, in questo bundle, i tre
strumenti tipografici avevano ricevuto una guardia che impedisce di riscrivere le copie dei
modelli; la guardia era entrata nelle copie sotto `tools/`, dove era stata provata, e non
nei modelli sotto `.claude/templates/fix-typography/tools/`. Tutte le prove passavano,
perche' le prove girano sulle copie. Il difetto sarebbe comparso soltanto nei progetti
allineati dopo, sotto forma di strumenti privi di una protezione che la documentazione
dichiarava presente: un difetto che viaggia in avanti e non si vede indietro.

Che cosa confronta, e che cosa no. Confronta i soli file che la convenzione vuole identici
byte per byte fra modello e copia, cioe' il codice eseguibile e i file normativi; il
criterio e' il nome della cartella dentro il pacchetto, non un elenco scritto a mano. Non
confronta i README dei pacchetti, che descrivono il pacchetto e non hanno una copia, ne' i
file di configurazione che si istanziano proprio per essere adattati: l'elenco delle
esclusioni di `fix-dashes`, per esempio, nella copia porta le righe del progetto ospite e
divergere e' il suo mestiere. Quei casi stanno in ECCEZIONI, con il motivo accanto.

Un modello senza copia non e' un difetto: significa che quel pacchetto non e' stato
adottato, che e' la condizione normale, e si conta senza elencarlo salvo richiesta.

Uso:
    python tools/check-copie-modelli.py                 confronta, radice = cartella corrente
    python tools/check-copie-modelli.py --radice <dir>  confronta un'altra radice
    python tools/check-copie-modelli.py --tutti         elenca anche i modelli non istanziati
    python tools/check-copie-modelli.py --allinea       riporta le copie sui modelli
    python tools/check-copie-modelli.py --self-test

Esce con codice 1 se almeno una copia diverge dal suo modello, 0 altrimenti.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile

MODELLI = os.path.join(".claude", "templates")

# Le cartelle di un pacchetto che corrispondono a una cartella dell'anatomia ospite. La
# chiave e' il nome della cartella dentro il pacchetto, il valore e' dove quella cartella
# atterra nel progetto che adotta il pacchetto. Il criterio e' strutturale e non un elenco di
# file: un pacchetto nuovo che porti strumenti entra in questo controllo senza toccarlo.
ANATOMIA = {
    "tools": "tools",
    "hooks": os.path.join(".claude", "hooks"),
    "rules": os.path.join(".claude", "rules"),
    "skills": os.path.join(".claude", "skills"),
    "agents": os.path.join(".claude", "agents"),
    "commands": os.path.join(".claude", "commands"),
}

# Le copie che divergono per mestiere, con la ragione. Non e' una lista di cose da
# sistemare: e' la dichiarazione che per questi file la divergenza e' il comportamento
# voluto, e senza dichiararla il controllo produrrebbe una segnalazione perpetua, che e' il
# modo piu' rapido di insegnare a ignorarlo.
ECCEZIONI = {
    "dashes-exclude.txt": "elenco di esclusioni del progetto ospite: si istanzia per essere "
                          "esteso con i file di quel progetto",
    "accents-exclude.txt": "elenco di esclusioni degli accenti del progetto ospite: si istanzia "
                           "per essere esteso con i file di quel progetto",
}


def leggi(percorso):
    with open(percorso, "rb") as f:
        return f.read()


def destinazione(relativo):
    """Dove atterra un modello nel progetto ospite, oppure None se non si istanzia.

    Si cerca, dopo il nome del pacchetto, il primo segmento che sia una cartella
    dell'anatomia: tutto cio' che segue si conserva, cosi' che una skill annidata in una
    cartella propria mantenga la sua struttura. Un modello che non attraversi nessuna di
    quelle cartelle, tipicamente un README o uno scheletro sotto `templates/`, non ha copia.
    """
    parti = relativo.replace("\\", "/").split("/")
    for i, segmento in enumerate(parti):
        if segmento in ANATOMIA and i + 1 < len(parti):
            return os.path.join(ANATOMIA[segmento], *parti[i + 1:])
    return None


def confronta(radice, tutti=False):
    base = os.path.join(radice, MODELLI)
    identici, divergenti, assenti, dichiarati, conflitti = [], [], [], [], []
    visti = {}
    if not os.path.isdir(base):
        return identici, divergenti, assenti, dichiarati, conflitti

    for cartella, sottocartelle, nomi in os.walk(base):
        sottocartelle[:] = [c for c in sottocartelle
                            if c not in (".git", "__pycache__", "node_modules", ".venv")]
        for nome in sorted(nomi):
            modello = os.path.join(cartella, nome)
            relativo = os.path.relpath(modello, base)
            dest = destinazione(relativo)
            if dest is None:
                continue
            # Due pacchetti che portino lo stesso file nella stessa posizione sono un
            # conflitto anche quando nessuno dei due e' stato istanziato: chi li adottasse
            # entrambi si troverebbe il secondo a sovrascrivere il primo in silenzio.
            precedente = visti.get(dest)
            if precedente and leggi(precedente) != leggi(modello):
                conflitti.append((dest, os.path.relpath(precedente, base), relativo))
            visti.setdefault(dest, modello)

            copia = os.path.join(radice, dest)
            if not os.path.exists(copia):
                assenti.append((relativo, dest))
                continue
            if leggi(copia) == leggi(modello):
                identici.append((relativo, dest))
            elif nome in ECCEZIONI:
                dichiarati.append((relativo, dest, ECCEZIONI[nome]))
            else:
                divergenti.append((relativo, dest))

    del tutti
    return identici, divergenti, assenti, dichiarati, conflitti


def stampa(radice, tutti):
    identici, divergenti, assenti, dichiarati, conflitti = confronta(radice)

    if divergenti:
        print("copie che divergono dal loro modello, da riconciliare:")
        for relativo, dest in divergenti:
            print("  %s" % dest)
            print("      modello: %s" % os.path.join(MODELLI, relativo))
        print("")
        print("Si guarda il diff prima di scegliere il verso: la correzione puo' stare da una")
        print("parte come dall'altra, e `--allinea` presume che la copia sia quella giusta.")
        print("")

    if conflitti:
        print("due modelli diversi per la stessa destinazione:")
        for dest, primo, secondo in conflitti:
            print("  %s <- %s e %s" % (dest, primo, secondo))
        print("")

    if dichiarati:
        print("divergenze dichiarate, che non sono difetti:")
        for relativo, dest, motivo in dichiarati:
            print("  %s: %s" % (dest, motivo))
        print("")

    if tutti and assenti:
        print("modelli non istanziati in questo progetto:")
        for relativo, dest in assenti:
            print("  %s -> %s" % (os.path.join(MODELLI, relativo), dest))
        print("")

    print("%d copie allineate, %d divergenti, %d dichiarate, %d modelli non istanziati"
          % (len(identici), len(divergenti), len(dichiarati), len(assenti)))
    return 1 if (divergenti or conflitti) else 0


def allinea(radice):
    """Riporta ogni copia sul suo modello, che e' il verso giusto solo a volte.

    La direzione non e' ovvia e lo strumento non prova a indovinarla: qui si presume che la
    copia sia quella corretta, perche' e' quella che gira e su cui si lavora, e che il
    modello sia rimasto indietro. E' il caso osservato, ma non e' l'unico possibile, quindi
    l'opzione si usa dopo aver letto i diff e non al posto di leggerli.
    """
    _, divergenti, _, _, _ = confronta(radice)
    for relativo, dest in divergenti:
        modello = os.path.join(radice, MODELLI, relativo)
        shutil.copyfile(os.path.join(radice, dest), modello)
        print("allineato %s <- %s" % (os.path.join(MODELLI, relativo), dest))
    if not divergenti:
        print("niente da allineare")
    return 0


def self_test():
    """Costruisce una radice finta con una copia allineata, una divergente e una assente."""
    falliti = 0
    base = tempfile.mkdtemp(prefix="check-copie-")
    try:
        def scrivi(percorso, testo):
            completo = os.path.join(base, percorso)
            os.makedirs(os.path.dirname(completo), exist_ok=True)
            with open(completo, "wb") as f:
                f.write(testo.encode("utf-8"))

        scrivi(os.path.join(MODELLI, "pacchetto", "tools", "uguale.py"), "a\n")
        scrivi(os.path.join("tools", "uguale.py"), "a\n")
        scrivi(os.path.join(MODELLI, "pacchetto", "tools", "diverso.py"), "a\n")
        scrivi(os.path.join("tools", "diverso.py"), "b\n")
        scrivi(os.path.join(MODELLI, "pacchetto", "tools", "assente.py"), "a\n")
        scrivi(os.path.join(MODELLI, "pacchetto", "README.md"), "non si istanzia\n")
        scrivi(os.path.join(MODELLI, "pacchetto", "rules", "regola.md"), "x\n")
        scrivi(os.path.join(".claude", "rules", "regola.md"), "y\n")
        scrivi(os.path.join(MODELLI, "pacchetto", "tools", "dashes-exclude.txt"), "a\n")
        scrivi(os.path.join("tools", "dashes-exclude.txt"), "a\nb\n")

        identici, divergenti, assenti, dichiarati, conflitti = confronta(base)
        atteso = {
            "identici": {os.path.join("tools", "uguale.py")},
            "divergenti": {os.path.join("tools", "diverso.py"),
                           os.path.join(".claude", "rules", "regola.md")},
            "assenti": {os.path.join("tools", "assente.py")},
            "dichiarati": {os.path.join("tools", "dashes-exclude.txt")},
        }
        ottenuto = {
            "identici": {d for _, d in identici},
            "divergenti": {d for _, d in divergenti},
            "assenti": {d for _, d in assenti},
            "dichiarati": {d for _, d, _ in dichiarati},
        }
        for chiave in atteso:
            if atteso[chiave] != ottenuto[chiave]:
                print("  FALLITA  %s: atteso %s, ottenuto %s"
                      % (chiave, sorted(atteso[chiave]), sorted(ottenuto[chiave])))
                falliti += 1
        if conflitti:
            print("  FALLITA  conflitti: nessuno atteso, trovati %s" % conflitti)
            falliti += 1

        # Il README del pacchetto non deve comparire da nessuna parte: e' la meta' della
        # prova che impedisce a un controllo troppo largo di passare.
        tutti = ottenuto["identici"] | ottenuto["divergenti"] | ottenuto["assenti"]
        if any("README" in d for d in tutti):
            print("  FALLITA  un README di pacchetto e' stato trattato come copia")
            falliti += 1
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print("check-copie-modelli: %d controlli falliti" % falliti)
    return 1 if falliti else 0


def main():
    ap = argparse.ArgumentParser(
        description="Confronta gli strumenti istanziati con i loro modelli.")
    ap.add_argument("--radice", default=".",
                    help="radice del progetto; per difetto la cartella corrente")
    ap.add_argument("--tutti", action="store_true",
                    help="elenca anche i modelli che questo progetto non ha istanziato")
    ap.add_argument("--allinea", action="store_true",
                    help="riporta le copie sui modelli, presumendo che la copia sia giusta")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    radice = os.path.abspath(args.radice)
    if args.allinea:
        return allinea(radice)
    return stampa(radice, args.tutti)


if __name__ == "__main__":
    sys.exit(main())
