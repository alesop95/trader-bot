#!/usr/bin/env python3
"""Verifica che il catalogo dei pacchetti descriva il disco, e non quello che descriveva ieri.

Perche' serve. Il catalogo in `.claude/templates/PACKAGES.md` e' la lista che il gate
attraversa per proporre i pacchetti, ed e' scritto a mano mentre le cartelle dei pacchetti
nascono e cambiano nome per conto proprio. Le due cose divergono in tre modi, tutti muti:
una riga nomina una cartella che non c'e' piu' e il gate propone un pacchetto inesistente;
una cartella non ha riga e il pacchetto non viene proposto a nessuno, il che e'
indistinguibile dall'averlo escluso di proposito; e i totali dichiarati in prosa restano al
numero che era giusto quando qualcuno li ha scritti.

Il terzo caso e' il piu' istruttivo perche' e' quello che si nota di meno. Il 2026-09-16 il
catalogo diceva settantatre' voci e ne aveva settantaquattro, mentre `docs/feature-map.html`
ne dichiarava sessantuno: tre numeri per lo stesso fatto, nessuno dei quali sbagliato nel
momento in cui era stato scritto. Un totale non ha un modo di accorgersi di essere vecchio,
e chi lo legge non ha modo di sapere che lo sia.

Perche' i totali in prosa non si cercano con una espressione regolare. Il testo dice anche
che un progetto appartiene a due o tre settori, e quel tre non e' un totale: e' una
osservazione. Una regola che cercasse un numero seguito da "settori" segnalerebbe entrambi,
e un controllo che segnala cio' che e' corretto insegna a ignorarlo. Le affermazioni che
questo strumento verifica stanno quindi in un elenco dichiarato, AFFERMAZIONI, una riga per
frase, con accanto che cosa quella frase conta. Registrarne una nuova costa una riga;
`--censimento` elenca i numeri che compaiono accanto alle parole del dominio, cosi' che
trovarle non richieda di ricordarsele.

Uso:
    python tools/check-catalogo.py                 verifica, radice = cartella corrente
    python tools/check-catalogo.py --radice <dir>  verifica un'altra radice
    python tools/check-catalogo.py --censimento    elenca i numeri da registrare
    python tools/check-catalogo.py --self-test

Esce con codice 1 se almeno una verifica fallisce, 0 altrimenti.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

CATALOGO = os.path.join(".claude", "templates", "PACKAGES.md")
MODELLI = os.path.join(".claude", "templates")

# Le cartelle sotto .claude/templates/ che non sono pacchetti: sono parti dell'anatomia di un
# progetto ospite o materiale condiviso, e non hanno una riga di catalogo perche' non si
# scelgono al gate.
NON_PACCHETTI = {"_notes", "agents", "context", "memory", "rules", "skills", "tools"}

# Le affermazioni numeriche sul catalogo, dichiarate una per una con cio' che contano. Il
# gruppo di cattura e' il numero, in cifre o in lettere italiane.
AFFERMAZIONI = [
    (CATALOGO, r"non è di comodità: con (\w+) voci", "voci"),
    (CATALOGO, r"trasforma un elenco di (\w+) voci", "voci"),
    (os.path.join("docs", "feature-map.html"),
     r"<strong>(\d+)</strong> pacchetti opt-in totali", "voci"),
    (os.path.join("docs", "feature-map.html"), r"I (\w+) settori, e da che cosa", "settori"),
]

UNITA = {"zero": 0, "uno": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6,
         "sette": 7, "otto": 8, "nove": 9, "dieci": 10, "undici": 11, "dodici": 12,
         "tredici": 13, "quattordici": 14, "quindici": 15, "sedici": 16, "diciassette": 17,
         "diciotto": 18, "diciannove": 19}
DECINE = {"venti": 20, "trenta": 30, "quaranta": 40, "cinquanta": 50, "sessanta": 60,
          "settanta": 70, "ottanta": 80, "novanta": 90}


def numero(parola):
    """Il valore di un numero scritto in cifre o in lettere, oppure None se non lo e'.

    Copre da zero a novantanove, che e' l'intervallo in cui vivono i conteggi di un catalogo,
    e gestisce le due contrazioni dell'italiano: la vocale finale della decina cade davanti a
    uno e otto, e il tre finale prende l'accento. Fuori dall'intervallo restituisce None
    invece di indovinare, perche' un numero non riconosciuto va dichiarato e non convertito
    a caso.
    """
    parola = parola.strip().lower()
    if parola.isdigit():
        return int(parola)
    parola = parola.replace("é", "e").replace("è", "e")
    if parola in UNITA:
        return UNITA[parola]
    for decina, valore in DECINE.items():
        if parola == decina:
            return valore
        if parola.startswith(decina[:-1]) and len(parola) > len(decina) - 1:
            resto = parola[len(decina) - 1:]
            if resto in ("uno", "otto"):
                return valore + UNITA[resto]
        if parola.startswith(decina):
            resto = parola[len(decina):]
            if resto in UNITA and 1 <= UNITA[resto] <= 9:
                return valore + UNITA[resto]
    return None


def leggi(percorso):
    with open(percorso, "rb") as f:
        return f.read().decode("utf-8")


def analizza_catalogo(testo):
    """Estrae dal catalogo i settori con le loro voci, e per ogni voce i modelli citati."""
    settore = None
    voci = []
    for riga in testo.split("\n"):
        if riga.startswith("### "):
            settore = riga[4:].strip()
            continue
        # Il nome puo' essere seguito da una annotazione nella stessa cella, per esempio
        # (MCP): venti righe su settantaquattro ce l'hanno, e un pattern che pretendesse la
        # cella chiusa subito dopo l'apice inverso le perderebbe tutte senza dire nulla,
        # riportando un totale piu' basso di quello vero. E' il difetto che questo strumento
        # esiste per trovare, comparso dentro lo strumento stesso alla prima corsa.
        m = re.match(r"\| *`([^`]+)`[^|]*\|", riga)
        if not m or settore is None:
            continue
        nome = m.group(1)
        citati = set(re.findall(r"`templates/([A-Za-z0-9_.-]+)/", riga))
        voci.append((nome, settore, citati))
    return voci


def pacchetti_su_disco(radice):
    base = os.path.join(radice, MODELLI)
    if not os.path.isdir(base):
        return set()
    return {n for n in os.listdir(base)
            if os.path.isdir(os.path.join(base, n)) and n not in NON_PACCHETTI}


def verifica(radice):
    problemi = []
    percorso = os.path.join(radice, CATALOGO)
    if not os.path.isfile(percorso):
        return ["manca %s: senza catalogo non c'e' niente da verificare" % CATALOGO], {}

    testo = leggi(percorso)
    voci = analizza_catalogo(testo)
    disco = pacchetti_su_disco(radice)

    # Un nome in due settori non e' una ridondanza innocua: il gate attraversa i settori
    # riconosciuti, quindi lo stesso pacchetto verrebbe proposto due volte a chi appartiene a
    # entrambi, e una risposta data la prima volta non varrebbe per la seconda.
    visti = {}
    for nome, settore, _ in voci:
        if nome in visti and visti[nome] != settore:
            problemi.append("`%s` compare in due settori: %s e %s"
                            % (nome, visti[nome], settore))
        visti[nome] = settore

    citati = set()
    for nome, _, modelli in voci:
        citati |= modelli
        for modello in sorted(modelli):
            # Si guarda il disco e non l'insieme dei pacchetti: una voce puo' legittimamente
            # citare una cartella condivisa come `templates/tools/`, che pacchetto non e'.
            if not os.path.isdir(os.path.join(radice, MODELLI, modello)):
                problemi.append("la voce `%s` cita `templates/%s/`, che non esiste"
                                % (nome, modello))

    # Un pacchetto sul disco senza riga di catalogo non viene proposto da nessun gate: e'
    # presente e invisibile, che e' lo stato peggiore dei due possibili, perche' occupa spazio
    # e non rende servizio.
    for cartella in sorted(disco - citati - set(visti)):
        problemi.append("`templates/%s/` sta sul disco e nessuna voce del catalogo lo cita"
                        % cartella)

    conteggi = {"voci": len(voci), "settori": len(set(s for _, s, _ in voci))}

    for relativo, pattern, cosa in AFFERMAZIONI:
        completo = os.path.join(radice, relativo)
        if not os.path.isfile(completo):
            continue
        for m in re.finditer(pattern, leggi(completo), re.IGNORECASE | re.DOTALL):
            dichiarato = numero(m.group(1))
            if dichiarato is None:
                problemi.append("%s: non so leggere il numero %r; va scritto in cifre o in "
                                "lettere fino a novantanove" % (relativo, m.group(1)))
            elif dichiarato != conteggi[cosa]:
                problemi.append("%s dichiara %d %s, ma il catalogo ne ha %d"
                                % (relativo, dichiarato, cosa, conteggi[cosa]))

    return problemi, conteggi


def censimento(radice):
    """Elenca i numeri che stanno accanto alle parole del dominio, da registrare o ignorare."""
    parole = r"(voci|pacchetti|settori)"
    for relativo in (CATALOGO, os.path.join("docs", "feature-map.html")):
        completo = os.path.join(radice, relativo)
        if not os.path.isfile(completo):
            continue
        print(relativo)
        for riga in leggi(completo).split("\n"):
            for m in re.finditer(r"([A-Za-z0-9à-ÿ]+) +" + parole, riga):
                if numero(m.group(1)) is None:
                    continue
                print("  %-6s %-9s  %s" % (m.group(1), m.group(2), riga.strip()[:90]))
    print("")
    print("Si registra in AFFERMAZIONI solo cio' che e' un totale del catalogo: un numero")
    print("accanto a una di queste parole puo' essere un'osservazione e non un conteggio.")
    return 0


def self_test():
    import tempfile
    import shutil
    falliti = 0
    base = tempfile.mkdtemp(prefix="check-catalogo-")
    try:
        def scrivi(percorso, testo):
            completo = os.path.join(base, percorso)
            os.makedirs(os.path.dirname(completo), exist_ok=True)
            with open(completo, "wb") as f:
                f.write(testo.encode("utf-8"))

        os.makedirs(os.path.join(base, MODELLI, "alfa"))
        os.makedirs(os.path.join(base, MODELLI, "orfano"))
        scrivi(CATALOGO, "\n".join((
            "## Catalogo",
            "",
            "Il criterio non è di comodità: con due voci si attraversa a mano.",
            "",
            "### Primo settore",
            "",
            "| `alfa` | fa | quando | `templates/alfa/tools/x.py` in `tools/` | note |",
            "| `beta` | fa | quando | `templates/beta/` in `tools/` | note |",
            "",
            "### Secondo settore",
            "",
            "| `alfa` | fa | quando | niente | note |",
        )))
        problemi, conteggi = verifica(base)
        attesi = [
            ("due settori", False),
            ("compare in due settori", True),
            ("templates/beta/`, che non esiste", True),
            ("`templates/orfano/` sta sul disco", True),
            ("dichiara 2 voci, ma il catalogo ne ha 3", True),
        ]
        for frammento, deve in attesi[1:]:
            trovato = any(frammento in p for p in problemi)
            if trovato != deve:
                print("  FALLITA  atteso %r fra i problemi, problemi=%s" % (frammento, problemi))
                falliti += 1
        if conteggi != {"voci": 3, "settori": 2}:
            print("  FALLITA  conteggi %s" % conteggi)
            falliti += 1

        for parola, valore in (("settantatre", 73), ("settantatré", 73), ("ventuno", 21),
                               ("ventotto", 28), ("dieci", 10), ("61", 61), ("novantanove", 99),
                               ("centouno", None)):
            if numero(parola) != valore:
                print("  FALLITA  numero(%r) = %r, atteso %r" % (parola, numero(parola), valore))
                falliti += 1
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print("check-catalogo: %d controlli falliti" % falliti)
    return 1 if falliti else 0


def main():
    ap = argparse.ArgumentParser(
        description="Verifica il catalogo dei pacchetti contro il disco.")
    ap.add_argument("--radice", default=".",
                    help="radice del progetto; per difetto la cartella corrente")
    ap.add_argument("--censimento", action="store_true",
                    help="elenca i numeri accanto alle parole del dominio")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    radice = os.path.abspath(args.radice)
    if args.censimento:
        return censimento(radice)

    problemi, conteggi = verifica(radice)
    for p in problemi:
        print("  %s" % p)
    if conteggi:
        print("")
        print("%d voci in %d settori" % (conteggi["voci"], conteggi["settori"]))
    print("check-catalogo: %d problemi" % len(problemi))
    return 1 if problemi else 0


if __name__ == "__main__":
    sys.exit(main())
