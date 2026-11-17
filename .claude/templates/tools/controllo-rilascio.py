#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lista di controllo prima del rilascio: per ogni voce dice presente, assente, non applicabile o da dichiarare.

Perché esiste
-------------
Il mandato del proprietario del 2026-11-12 chiedeva che la lista dei controlli da fare prima di
mandare un'applicazione in produzione, una quarantina di voci dalla CI alla posta autenticata ai
limiti di spesa, diventasse una verifica della skill `pipeline-app` che risponde voce per voce,
invece di un elenco da ricordare. La ricognizione del 2026-11-16 sui progetti allineati ha dato
la ragione concreta: dei progetti che dichiarano qualcosa in esercizio, due registrano settimane
di silenzio che nessun controllo ha segnalato.

Come decide
-----------
Una parte delle voci si riconosce dal repository: un file di CI, un file di blocco delle
dipendenze, una cartella di migrazioni. Per quelle lo strumento cerca la prova e, se la trova,
la nomina. Le altre non si vedono da un repository, per esempio un ripristino provato o un limite
di spesa impostato presso un fornitore: per quelle risponde «da dichiarare» finché il progetto
non le dichiara in `tools/rilascio.txt`, una riga per voce:

    ripristino-provato: presente - provato il 2026-11-10 su una copia, vedi docs/ripristino.md
    consenso-cookie: non-applicabile - il sito non usa cookie non tecnici
    limiti-spesa: assente - da impostare prima del primo utente

Una dichiarazione vale più del riconoscimento automatico, in entrambe le direzioni, e porta
sempre un motivo: una riga senza motivo è rifiutata, perché «non applicabile» senza un perché è
il modo in cui una voce sparisce. Lo strumento non si collega a niente e non legge altro che i
nomi dei file e, per tre voci, una parola dentro un file di configurazione.

La lista è stata ricostruita dalla descrizione del mandato e dalla pratica corrente, non copiata
dall'immagine che il proprietario aveva indicato: va letta come un punto di partenza che ogni
progetto corregge, e una voce che manca si aggiunge qui.

Uso
---
    python tools/controllo-rilascio.py                 la lista, voce per voce
    python tools/controllo-rilascio.py --rigoroso      esce con 1 se resta una voce assente o da dichiarare
    python tools/controllo-rilascio.py --radice <dir>  un progetto diverso da quello corrente
    python tools/controllo-rilascio.py --autotest
"""

import argparse
import glob
import os
import shutil
import sys
import tempfile

DICHIARAZIONI = os.path.join("tools", "rilascio.txt")
STATI = ("presente", "assente", "non-applicabile")

# (identificativo, area, che cosa si chiede, schemi di file che lo provano, (file, parola) che lo prova)
VOCI = [
    ("ci", "Codice e prove", "Una CI esegue i controlli a ogni push", [".github/workflows/*.y*ml", ".gitlab-ci.yml"], None),
    ("prove", "Codice e prove", "Esistono prove automatiche", ["tests", "test", "e2e", "src/**/*.test.*", "**/test_*.py"], None),
    ("lint", "Codice e prove", "Lint e formattazione sono configurati", [".pre-commit-config.yaml", "eslint.config.*", ".eslintrc*", "ruff.toml", "biome.json"], ("pyproject.toml", "ruff")),
    ("stessi-controlli", "Codice e prove", "CI e locale chiamano lo stesso script di controllo", [], None),
    ("blocco-dipendenze", "Dipendenze", "Le dipendenze sono bloccate in un file versionato", ["uv.lock", "poetry.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock*", "Cargo.lock", "go.sum"], None),
    ("vulnerabilita", "Dipendenze", "Le dipendenze sono state controllate per vulnerabilità note", ["_notes/sicurezza/ultimo-controllo.json"], None),
    ("esempio-ambiente", "Segreti e configurazione", "Un file di esempio elenca le variabili d'ambiente senza i valori", [".env.example", ".env.sample", ".env.template"], None),
    ("segreti-ignorati", "Segreti e configurazione", "I file con i segreti sono ignorati da git", [], (".gitignore", ".env")),
    ("segreti-ruotabili", "Segreti e configurazione", "Ogni segreto si può cambiare senza un rilascio, e si sa come", [], None),
    ("ambienti-separati", "Segreti e configurazione", "Prova e produzione hanno credenziali e dati distinti", [], None),
    ("migrazioni", "Dati", "Lo schema dei dati cambia con migrazioni versionate", ["prisma/migrations", "migrations", "alembic", "drizzle", "supabase/migrations"], None),
    ("copia-dati", "Dati", "Una copia dei dati viene fatta da sola, fuori dalla macchina che li ospita", [], None),
    ("ripristino-provato", "Dati", "Il ripristino da quella copia è stato provato almeno una volta", [], None),
    ("dati-di-prova", "Dati", "L'ambiente di prova non contiene dati reali di persone", [], None),
    ("rilascio-descritto", "Rilascio", "Il modo di rilasciare è scritto in un posto solo", [".claude/context/deployment.md", "docs/deploy*.md", "DEPLOY.md"], None),
    ("ritorno-indietro", "Rilascio", "Si sa come tornare alla versione precedente, ed è stato fatto una volta", [], None),
    ("costruzione-ripetibile", "Rilascio", "La costruzione è ripetibile da un comando o da un contenitore", ["Dockerfile", "docker-compose*.y*ml", "compose*.y*ml", "Makefile"], None),
    ("https", "Dominio e posta", "Il sito risponde in HTTPS e il certificato si rinnova da solo", [], None),
    ("scadenze", "Dominio e posta", "Qualcuno riceve l'avviso di scadenza del dominio e del certificato", [], None),
    ("posta-autenticata", "Dominio e posta", "La posta che il sistema manda è autenticata con SPF, DKIM e DMARC", [], None),
    ("disponibilita", "Esercizio", "Un controllo esterno dice se il servizio risponde", [], None),
    ("errori-raccolti", "Esercizio", "Gli errori arrivano in un posto dove qualcuno li guarda", [], None),
    ("avviso-a-una-persona", "Esercizio", "Un guasto produce un avviso a una persona, non solo una riga di registro", [], None),
    ("ultimo-risultato", "Esercizio", "Per ogni lavoro programmato si controlla che l'ultimo risultato utile sia recente", [], None),
    ("registri", "Esercizio", "I registri si conservano per un tempo deciso e non contengono segreti", [], None),
    ("limiti-frequenza", "Abuso e costi", "Le rotte pubbliche e i moduli hanno un limite di frequenza", [], None),
    ("limiti-spesa", "Abuso e costi", "Ogni servizio a consumo ha un tetto di spesa o un avviso", [], None),
    ("accessi-amministrativi", "Abuso e costi", "Gli accessi amministrativi usano il secondo fattore e sono nominali", [], None),
    ("informativa", "Persone e norme", "L'informativa sul trattamento dei dati esiste ed è raggiungibile", [], None),
    ("consenso-cookie", "Persone e norme", "Il consenso ai cookie non tecnici è chiesto prima di usarli", [], None),
    ("cancellazione", "Persone e norme", "Si sa come esportare e cancellare i dati di una persona che lo chiede", [], None),
    ("licenza", "Persone e norme", "Il repository dichiara la propria licenza o la propria riservatezza", ["LICENSE*", "LICENCE*", "COPYING*"], None),
]


def leggi_dichiarazioni(radice):
    """Ritorna (dichiarazioni, errori). Una riga è `voce: stato - motivo`; il cancelletto apre un commento."""
    dichiarazioni, errori = {}, []
    percorso = os.path.join(radice, DICHIARAZIONI)
    if not os.path.exists(percorso):
        return dichiarazioni, errori
    noti = {v[0] for v in VOCI}
    with open(percorso, encoding="utf-8", errors="replace") as f:
        for numero, riga in enumerate(f, 1):
            riga = riga.split("#", 1)[0].strip()
            if not riga:
                continue
            voce, _, resto = riga.partition(":")
            stato, _, motivo = resto.strip().partition(" - ")
            voce, stato, motivo = voce.strip(), stato.strip(), motivo.strip()
            if voce not in noti:
                errori.append("riga %d: voce sconosciuta `%s`" % (numero, voce))
            elif stato not in STATI:
                errori.append("riga %d: stato `%s` non riconosciuto, valgono %s" % (numero, stato, ", ".join(STATI)))
            elif not motivo:
                errori.append("riga %d: `%s` dichiarata senza motivo" % (numero, voce))
            else:
                dichiarazioni[voce] = (stato, motivo)
    return dichiarazioni, errori


def prova_nel_repository(radice, schemi, contiene):
    for schema in schemi:
        trovati = glob.glob(os.path.join(radice, schema), recursive=True)
        trovati = [t for t in trovati if "node_modules" not in t and ".venv" not in t]
        if trovati:
            return os.path.relpath(sorted(trovati)[0], radice).replace("\\", "/")
    if contiene:
        percorso = os.path.join(radice, contiene[0])
        if os.path.exists(percorso):
            with open(percorso, encoding="utf-8", errors="replace") as f:
                if contiene[1] in f.read():
                    return "%s nomina %s" % (contiene[0], contiene[1])
    return None


def valuta(radice):
    """Ritorna (righe, errori): ogni riga è (voce, area, domanda, stato, perché)."""
    dichiarazioni, errori = leggi_dichiarazioni(radice)
    righe = []
    for voce, area, domanda, schemi, contiene in VOCI:
        if voce in dichiarazioni:
            stato, motivo = dichiarazioni[voce]
            righe.append((voce, area, domanda, stato, "dichiarato: " + motivo))
            continue
        prova = prova_nel_repository(radice, schemi, contiene)
        if prova:
            righe.append((voce, area, domanda, "presente", "trovato " + prova))
        elif schemi or contiene:
            righe.append((voce, area, domanda, "assente", "nessuna prova nel repository"))
        else:
            righe.append((voce, area, domanda, "da-dichiarare", "non si vede da un repository: va scritta in " + DICHIARAZIONI.replace("\\", "/")))
    return righe, errori


def stampa(righe, errori):
    area_corrente = None
    for voce, area, domanda, stato, perche in righe:
        if area != area_corrente:
            print("\n" + area)
            area_corrente = area
        print("  %-15s %-22s %s" % (stato, voce, domanda))
        print("  %-15s %-22s   %s" % ("", "", perche))
    conteggi = {}
    for riga in righe:
        conteggi[riga[3]] = conteggi.get(riga[3], 0) + 1
    print("\n%d voci: " % len(righe) + ", ".join("%d %s" % (conteggi[s], s) for s in ("presente", "assente", "non-applicabile", "da-dichiarare") if s in conteggi))
    for e in errori:
        print("ERRORE in %s, %s" % (DICHIARAZIONI.replace("\\", "/"), e))


def autotest():
    esiti = []

    def caso(nome, ok, dettaglio=""):
        esiti.append(bool(ok))
        print(("ok    " if ok else "ROSSO ") + nome + ("" if ok else "  " + str(dettaglio)))

    base = tempfile.mkdtemp(prefix="rilascio-")
    try:
        def stato_di(voce):
            return {r[0]: r for r in valuta(base)[0]}[voce]

        caso("in un repository vuoto una voce riconoscibile e' assente", stato_di("ci")[3] == "assente")
        caso("una voce che non si vede da un repository e' da dichiarare, non assente", stato_di("ripristino-provato")[3] == "da-dichiarare")
        os.makedirs(os.path.join(base, ".github", "workflows"))
        open(os.path.join(base, ".github", "workflows", "ci.yml"), "w").close()
        caso("un file di CI rende la voce presente e viene nominato", stato_di("ci")[3] == "presente" and "ci.yml" in stato_di("ci")[4], stato_di("ci"))
        with open(os.path.join(base, ".gitignore"), "w") as f:
            f.write("node_modules\n.env\n")
        caso("la parola dentro un file prova la voce", stato_di("segreti-ignorati")[3] == "presente")
        os.makedirs(os.path.join(base, "node_modules", "x", "tests"))
        caso("una cartella di prove dentro le dipendenze non conta", stato_di("prove")[3] == "assente", stato_di("prove"))
        os.makedirs(os.path.join(base, "tools"))
        with open(os.path.join(base, DICHIARAZIONI), "w", encoding="utf-8") as f:
            f.write("# dichiarazioni\nripristino-provato: presente - provato su una copia\n"
                    "ci: non-applicabile - nessun rilascio automatico\nconsenso-cookie: non-applicabile\n"
                    "inventata: presente - x\nlimiti-spesa: forse - x\n")
        righe, errori = valuta(base)
        per_voce = {r[0]: r for r in righe}
        caso("una dichiarazione rende presente una voce che non si vede", per_voce["ripristino-provato"][3] == "presente")
        caso("una dichiarazione vale piu' del riconoscimento automatico", per_voce["ci"][3] == "non-applicabile", per_voce["ci"])
        caso("una dichiarazione senza motivo e' rifiutata e la voce resta da dichiarare",
             per_voce["consenso-cookie"][3] == "da-dichiarare" and any("senza motivo" in e for e in errori), errori)
        caso("una voce sconosciuta e uno stato sconosciuto sono errori", any("sconosciuta" in e for e in errori) and any("non riconosciuto" in e for e in errori), errori)
        caso("gli identificativi delle voci sono unici", len({v[0] for v in VOCI}) == len(VOCI))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print("%d prove, %d fallite" % (len(esiti), esiti.count(False)))
    return 1 if False in esiti else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--radice", default=".")
    ap.add_argument("--rigoroso", action="store_true")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()
    if a.autotest:
        return autotest()
    righe, errori = valuta(a.radice)
    stampa(righe, errori)
    aperte = [r for r in righe if r[3] in ("assente", "da-dichiarare")]
    if errori or (a.rigoroso and aperte):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
