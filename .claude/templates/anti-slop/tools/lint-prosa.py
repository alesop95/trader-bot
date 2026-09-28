#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Segnala nella prosa i segni ricorrenti del testo generato da un modello.

Perché esiste
-------------
Un testo generato si riconosce spesso non da un errore ma da una regolarità: paragrafi della
stessa misura, frasi della stessa lunghezza, un'autorità citata senza nome, la stessa figura
retorica ripetuta, tutto a gruppi di tre. Nessuno di questi segni prova da solo che un testo sia
generato, e questo programma non lo pretende: li conta e dice dove stanno, perché chi rilegge
possa decidere. Il catalogo dei segni, con il perché e con le fonti, sta in `GUIDA.md` del
pacchetto `anti-slop`; qui c'è solo il modo di trovarli.

Che cosa cerca
--------------
P1  uniformità: documenti in cui la maggior parte dei paragrafi misurabili ha frasi di
    lunghezza quasi identica, e documenti con quattro o più paragrafi di misura quasi identica.
    La misura è il coefficiente di variazione, deviazione standard divisa per la media, delle
    parole per frase o per paragrafo. Il singolo paragrafo non si segnala: non discrimina.
P2  attribuzione vaga: "gli esperti ritengono", "studi dimostrano", "experts say", senza un
    rimando nella stessa frase, cioè un collegamento, una nota, un anno fra parentesi o una
    sigla di fonte come [F12].
P3  parallelismo negativo: "non si tratta solo di X, si tratta di Y", "non è X. È Y",
    "it's not just X, it's Y", "not about X, it's about Y".
P4  triadi: tre frasi di una o due parole di fila ("Veloce. Semplice. Potente."), e documenti in
    cui gli elenchi di tre elementi sono la grande maggioranza degli elenchi.
P5  gergo forzato: abbreviazioni e intercalari da chat in un testo che non è una chat.
P6  lessico di maniera: parole ed espressioni che la letteratura misura come sovrarappresentate
    nei testi generati, in inglese dalla fonte e in italiano come equivalenti proposti.

Non cerca i trattini lunghi, che sono il compito di `fix-dashes.py` del pacchetto
`fix-typography`, e non guarda dentro i blocchi di codice, il front matter, i commenti HTML, le
tabelle e le citazioni in blocco, dove la regolarità è strutturale o il testo è di altri.

Che cosa non può sapere
-----------------------
Non sa se un testo sia generato. I rilevatori automatici di testo generato sbagliano, e sbagliano
di più sulla prosa di chi scrive in una lingua che non è la propria: per questo l'uscita è un
elenco di punti da rileggere e mai un giudizio, e il codice di uscita è zero salvo `--gate`.

Uso
---
    python tools/lint-prosa.py <file o cartella> [...]
    python tools/lint-prosa.py --gate <file o cartella>     esce 1 se trova qualcosa
    python tools/lint-prosa.py --solo P2,P3 <percorso>       solo alcune famiglie
    python tools/lint-prosa.py --self-test
"""

import argparse
import io
import os
import re
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ESCLUSE = {".git", "node_modules", ".venv", "__pycache__", "dist", "build", "out", ".next",
           "target"}
ESTENSIONI = (".md", ".markdown", ".txt")

# Soglie. Sono scelte, non misure universali: stanno qui in chiaro perché si possano discutere.
MIN_FRASI_PARAGRAFO = 4       # sotto, la variazione di lunghezza non dice niente
CV_FRASI = 0.25               # sotto questa variazione un paragrafo conta come uniforme
# Il paragrafo singolo non discrimina: misurato il 2026-09-23, il campione generato della fonte
# visiva ha variazione 0.18 e paragrafi umani del template stanno fra 0.11 e 0.22. Discrimina la
# quota di paragrafi uniformi nel documento: al massimo 0.20 nella prosa del template, 1.00 nel
# campione. Si segnala quindi il documento, non il paragrafo.
MIN_PARAGRAFI_MISURABILI = 3
QUOTA_UNIFORMI = 0.6
MIN_PARAGRAFI = 4
CV_PARAGRAFI = 0.12
MIN_ELENCHI = 6               # sotto, la prevalenza delle triadi non è un segnale
QUOTA_TRIADI = 0.7

RIMANDO = re.compile(r"\]\(|https?://|\[\^|\[[FC]\d+\]|\(\d{4}[a-z]?\)|\bdoi:|\bet al\.",
                     re.IGNORECASE)

ATTRIBUZIONE_VAGA = [
    r"\b(gli |molti |numerosi |alcuni )?esperti (dicono|affermano|ritengono|concordano|sostengono|suggeriscono|avvertono)\b",
    r"\bsecondo (gli |molti |alcuni )?(esperti|studi|ricercatori|analisti)\b",
    r"\b(numerosi |diversi |molti |recenti |alcuni )?studi (dimostrano|mostrano|suggeriscono|indicano|confermano|hanno (dimostrato|mostrato|rilevato))\b",
    r"\b(la |le )?ricerch?[ae] (dimostra|mostra|suggerisce|indica|conferma)(no)?\b",
    r"\bi ricercatori hanno (scoperto|trovato|dimostrato|osservato)\b",
    r"\bè (ormai |ampiamente )?(noto|dimostrato|riconosciuto|accertato) che\b",
    r"\b(experts|analysts|scientists) (say|believe|agree|suggest|warn|argue)\b",
    r"\baccording to (experts|studies|research|researchers|analysts)\b",
    r"\b(many |several |recent |some )?studies (show|suggest|indicate|have (shown|found))\b",
    r"\bresearch (shows|suggests|indicates|has shown)\b",
    r"\bresearchers (have )?(found|discovered|shown)\b",
    r"\bit is (widely|generally|commonly) (believed|accepted|known|acknowledged)\b",
]

PARALLELISMO_NEGATIVO = [
    r"\bnon si tratta (solo |soltanto |semplicemente )?di\b[^.;:!?]{0,80}[,;:.]\s*(si tratta|ma) di\b",
    r"\bnon (è|e\u0027) (solo|soltanto|semplicemente)\b[^.;!?]{0,80}[,;:]\s*(ma|è|e\u0027)(?!\w)",
    r"\bnon (è|e\u0027) (una questione di|questione di)\b",
    r"(^|[.!?]\s+)Non è [^.!?]{1,60}\.\s+È\b",
    r"\b[Nn]on è [^.:;,!?]{1,50}[:;,]\s*è\b",
    r"\bit'?s not (just |only |simply )?(about )?[^.;!?]{1,60}[,;.]\s*it'?s (about )?\w",
    r"\bnot (just|only|merely) [^.;!?]{1,60}[,;]\s*(but|it'?s)\b",
    r"\bisn'?t (just|only) [^.;!?]{1,60}[,;]\s*it'?s\b",
]

GERGO_FORZATO = [
    r"\b(tbh|lol|lmao|ngl|imo|fr|smh|idk)\b",
    r"\b(kinda|sorta|gonna|wanna|lowkey|highkey)\b",
    r"\bno cap\b",
    r"\b(raga|cmq|xké|xke|nn|tvb)\b",
    r"\b(figata|una bomba|top di gamma assoluto)\b",
]

# Inglese: le "Words to watch" di Wikipedia:Signs of AI writing (WP:AIVOCAB), corroborate per il
# lessico biomedico da Kobak e altri (FONTI.md). La pagina le data per generazione di modelli e
# avverte che il segnale decade: "delve" è crollata nel 2025. Si dividono in due gruppi. Le
# distintive si segnalano a ogni occorrenza; le comuni, che un testo tecnico usa legittimamente,
# solo quando la loro densità supera DENSITA_COMUNI per mille parole.
LESSICO_EN = [
    r"\bdelv(e|es|ed|ing)\b", r"\btapestry\b", r"\btestament to\b", r"\bpivotal\b",
    r"\bunderscor(e|es|ed|ing)\b", r"\bshowcas(e|es|ed|ing)\b", r"\bintricac(y|ies)\b",
    r"\bintricate\b", r"\bmeticulous(ly)?\b", r"\bboast(s|ed|ing)?\b", r"\bbolster(ed|s|ing)?\b",
    r"\bgarner(s|ed|ing)?\b", r"\binterplay\b", r"\bfoster(s|ed|ing)?\b", r"\benduring\b",
    r"\bvibrant\b", r"\bever-evolving\b",
]
LESSICO_EN_COMUNE = [
    r"\bcrucial\b", r"\bkey\b", r"\blandscape\b", r"\brobust\b", r"\benhanc(e|es|ed|ing)\b",
    r"\bhighlight(s|ed|ing)?\b", r"\bvaluable\b", r"\badditionally\b", r"\balign(s|ed)? with\b",
    r"\bemphasiz(e|es|ed|ing)\b", r"\bdeep dive\b",
]
DENSITA_COMUNI = 8.0
# "Not just X, but also Y" è un sottotipo di WP:AIPARALLEL, ma "non solo... ma anche" è un
# correlativo ordinario dell'italiano: si segnala solo quando si ripete nello stesso file.
CORRELATIVO = re.compile(r"\b(non solo|non soltanto|not only|not just)\b[^.;!?]{1,90}\b(ma|but)( anche| also)?\b",
                         re.IGNORECASE)
MIN_CORRELATIVI = 3
LESSICO_IT = [
    r"\bgioca(no)? un ruolo (cruciale|fondamentale|chiave|centrale)\b",
    r"\bin un mondo (in cui|sempre più|in continua evoluzione)\b",
    r"\bnel panorama (attuale|odierno|digitale)\b",
    r"\bè importante (notare|sottolineare|ricordare) che\b",
    r"\bvale la pena (notare|sottolineare) che\b",
    r"\bimmergiamoci\b", r"\baddentriamoci\b", r"\bsvela(re|ndo)? i segreti\b",
    r"\bun vero e proprio (punto di svolta|game changer)\b", r"\bgame changer\b",
    r"\bin conclusione,\b", r"\bin sintesi,\b",
]

FRASE = re.compile(r"(?<=[.!?])\s+(?=[\"'«(]?[A-ZÀ-ÖØ-Ý])")
PAROLA = re.compile(r"[\wÀ-ÿ'’-]+", re.UNICODE)
ELENCO = re.compile(r"\b([\wÀ-ÿ'’-]+(?: [\wÀ-ÿ'’-]+)?)((?:, [\wÀ-ÿ'’-]+(?: [\wÀ-ÿ'’-]+)?)+),? (e|ed|o|and|or) [\wÀ-ÿ'’-]+")
CORTA = re.compile(r"^[\"'«]?[\wÀ-ÿ'’-]+( [\wÀ-ÿ'’-]+)?[.!]$")


def cammina(radice):
    if os.path.isfile(radice):
        yield radice
        return
    for dirpath, dirnames, filenames in os.walk(radice):
        dirnames[:] = [d for d in dirnames if d not in ESCLUSE]
        if ".md-unwrap-ignore" in filenames:
            dirnames[:] = []
            continue
        for nome in sorted(filenames):
            if nome.lower().endswith(ESTENSIONI):
                yield os.path.join(dirpath, nome)


def paragrafi(testo):
    """I paragrafi di prosa con il numero della loro prima riga, esclusa la struttura."""
    righe = testo.splitlines()
    fuori, dentro_codice, marcatore, in_commento = [], False, "", False
    i = 0
    if righe and righe[0].strip() == "---":
        # Il front matter si salta per intero.
        for j in range(1, len(righe)):
            if righe[j].strip() == "---":
                i = j + 1
                break
    corrente, inizio = [], 0
    while i < len(righe):
        r = righe[i]
        s = r.strip()
        if dentro_codice:
            if s.startswith(marcatore):
                dentro_codice = False
            i += 1
            continue
        if s.startswith("```") or s.startswith("~~~"):
            dentro_codice, marcatore = True, s[:3]
            if corrente:
                fuori.append((inizio, " ".join(corrente)))
                corrente = []
            i += 1
            continue
        if in_commento or s.startswith("<!--"):
            in_commento = "-->" not in s
            i += 1
            continue
        strutturale = (not s or s.startswith(("#", "|", ">", "- ", "* ", "+ ", "<"))
                       or re.match(r"^\d+[.)] ", s) or r.startswith("    "))
        if strutturale:
            if corrente:
                fuori.append((inizio, " ".join(corrente)))
                corrente = []
        else:
            if not corrente:
                inizio = i + 1
            corrente.append(s)
        i += 1
    if corrente:
        fuori.append((inizio, " ".join(corrente)))
    return fuori


def pulisci(p):
    p = re.sub(r"`[^`]*`", "X", p)                 # il codice in linea conta come una parola
    # Il testo fra virgolette è una menzione, non un uso: una guida che cita "gli esperti
    # ritengono" per spiegarlo non sta attribuendo niente a nessuno. Conta come una parola.
    p = re.sub(r"\"[^\"]{1,300}\"|«[^»]{1,300}»|“[^”]{1,300}”", "X", p)
    p = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", p)  # un collegamento conta per il suo testo
    return p


def frasi(p):
    return [f.strip() for f in FRASE.split(pulisci(p)) if f.strip()]


def n_parole(s):
    return len(PAROLA.findall(s))


def cv(valori):
    if len(valori) < 2:
        return None
    media = statistics.mean(valori)
    return statistics.pstdev(valori) / media if media else None


def cerca(testo, attive=None):
    """Ritorna una lista di (riga, famiglia, descrizione, estratto)."""
    attive = attive or {"P1", "P2", "P3", "P4", "P5", "P6"}
    esiti = []
    blocchi = paragrafi(testo)
    misurabili, uniformi = 0, 0
    for riga, p in blocchi:
        fs = frasi(p)
        if "P1" in attive and len(fs) >= MIN_FRASI_PARAGRAFO:
            v = cv([n_parole(f) for f in fs])
            if v is not None:
                misurabili += 1
                uniformi += v < CV_FRASI
        for f in fs:
            if "P2" in attive and not RIMANDO.search(f):
                for pat in ATTRIBUZIONE_VAGA:
                    m = re.search(pat, f, re.IGNORECASE)
                    if m:
                        esiti.append((riga, "P2", "attribuzione senza fonte nominata", m.group(0)))
                        break
            if "P5" in attive:
                for pat in GERGO_FORZATO:
                    m = re.search(pat, f, re.IGNORECASE)
                    if m:
                        esiti.append((riga, "P5", "gergo da chat", m.group(0)))
                        break
            if "P6" in attive:
                for pat, lingua in [(x, "en") for x in LESSICO_EN] + [(x, "it") for x in LESSICO_IT]:
                    m = re.search(pat, f, re.IGNORECASE)
                    if m:
                        esiti.append((riga, "P6", "lessico di maniera" + (" (indizio debole)" if lingua == "it" else ""), m.group(0)))
        if "P3" in attive:
            for pat in PARALLELISMO_NEGATIVO:
                for m in re.finditer(pat, pulisci(p), re.IGNORECASE if "Non è" not in pat else 0):
                    esiti.append((riga, "P3", "parallelismo negativo", m.group(0).strip()[:70]))
        if "P4" in attive:
            corte = [CORTA.match(f) is not None for f in fs]
            for k in range(len(corte) - 2):
                if corte[k] and corte[k + 1] and corte[k + 2]:
                    esiti.append((riga, "P4", "tre frasi di una o due parole di fila",
                                  " ".join(fs[k:k + 3])[:70]))
                    break
    if "P1" in attive and misurabili >= MIN_PARAGRAFI_MISURABILI \
            and uniformi / misurabili >= QUOTA_UNIFORMI:
        esiti.append((blocchi[0][0], "P1", "frasi di lunghezza quasi uguale in %d paragrafi su %d"
                      % (uniformi, misurabili), ""))
    if "P1" in attive:
        misure = [n_parole(pulisci(p)) for _, p in blocchi if n_parole(pulisci(p)) >= 20]
        if len(misure) >= MIN_PARAGRAFI:
            v = cv(misure)
            if v is not None and v < CV_PARAGRAFI:
                esiti.append((blocchi[0][0], "P1", "paragrafi di misura quasi uguale (variazione "
                              "%.2f su %d paragrafi)" % (v, len(misure)), ""))
    if "P3" in attive:
        correlativi = sum(len(CORRELATIVO.findall(pulisci(p))) for _, p in blocchi)
        if correlativi >= MIN_CORRELATIVI:
            esiti.append((1, "P3", "'non solo... ma anche' ripetuto %d volte nel file" % correlativi, ""))
    if "P6" in attive:
        parole = sum(n_parole(pulisci(p)) for _, p in blocchi)
        comuni = sum(len(re.findall(pat, pulisci(p), re.IGNORECASE))
                     for _, p in blocchi for pat in LESSICO_EN_COMUNE)
        if parole >= 300 and comuni * 1000.0 / parole >= DENSITA_COMUNI:
            esiti.append((1, "P6", "parole comuni di maniera troppo dense (%.1f per mille parole)"
                          % (comuni * 1000.0 / parole), ""))
    if "P4" in attive:
        conta = {2: 0, 3: 0, 4: 0}
        for _, p in blocchi:
            for m in ELENCO.finditer(pulisci(p)):
                n = m.group(2).count(",") + 2
                conta[min(n, 4)] += 1
        totale = sum(conta.values())
        if totale >= MIN_ELENCHI and conta[3] / totale >= QUOTA_TRIADI:
            esiti.append((1, "P4", "gli elenchi sono quasi tutti di tre elementi (%d su %d)"
                          % (conta[3], totale), ""))
    return esiti


APOSTROFO = chr(39)   # costruito, perché la grafia scorretta che si prova non stia nel sorgente


def self_test():
    esiti = []

    def prova(nome, condizione, dettaglio=""):
        esiti.append((nome, bool(condizione), dettaglio))

    def famiglie(testo):
        return {f for _, f, _, _ in cerca(testo)}

    # Il paragrafo d'esempio della fonte visiva: frasi quasi tutte della stessa misura.
    uniforme = ("AI slop refers to the generation of low-quality outputs by artificial systems. "
                "This can happen when the model is trained on poor or insufficient data. "
                "As a result, the system may produce responses that are simply inaccurate. "
                "Such outputs can undermine user trust and reduce the overall effectiveness.\n")
    prova("negativo P1: un solo paragrafo uniforme non basta a segnalare il documento",
          "P1" not in famiglie(uniforme))
    prova("P1: un documento con i paragrafi quasi tutti uniformi si segnala",
          "P1" in famiglie(uniforme + "\n" + uniforme.replace("AI slop", "Model drift") + "\n"
                           + uniforme.replace("system", "service")))
    prova("P3: 'non è X: è Y' con i due punti si segnala",
          "P3" in famiglie("Non è burocrazia: è ciò che permette di accorgersene.\n"))
    vario = ("Funziona. Ma solo finché la cartella corrente è quella giusta, e nessuno se ne "
             "accorge fino al primo commit sbagliato, che arriva sempre di venerdì sera quando "
             "chi l'ha scritto è già uscito. Poi si corregge. Il costo, in quel caso, è stato "
             "di un'ora di lavoro e di tre messaggi di scuse.\n")
    prova("negativo P1: frasi di lunghezza diversa non si segnalano", "P1" not in famiglie(vario))

    prova("P2: «gli esperti ritengono» senza fonte si segnala",
          "P2" in famiglie("Gli esperti ritengono che cambierà il settore.\n"))
    prova("negativo P2: la stessa frase con un rimando non si segnala",
          "P2" not in famiglie("Gli esperti ritengono che cambierà il settore [F13].\n"))
    prova("P2: 'studies suggest' in inglese si segnala",
          "P2" in famiglie("Studies suggest that 67% of people agree.\n"))

    prova("P3: 'non si tratta di X, si tratta di Y' si segnala",
          "P3" in famiglie("Non si tratta di risparmiare tempo, si tratta di cambiare metodo.\n"))
    prova("P3: 'it's not about X. It's about Y' si segnala",
          "P3" in famiglie("It's not about saving time. It's about transforming how you work.\n"))
    prova("P3: la grafia con l'apostrofo al posto dell'accento si riconosce",
          "P3" in famiglie("Il punto non e" + APOSTROFO + " solo questo, e" + APOSTROFO + " anche altro.\n"))
    prova("negativo P3: 'non solo X ma anche Y' come correlativo ordinario non si segnala",
          "P3" not in famiglie("Serve non solo alla prova ma anche al rilascio.\n"))

    prova("P4: tre frasi di una parola di fila si segnalano",
          "P4" in famiglie("Il prodotto è pronto. Veloce. Semplice. Potente.\n"))
    prova("negativo P4: due frasi corte non bastano",
          "P4" not in famiglie("Il prodotto è pronto. Veloce. Semplice, e anche economico.\n"))

    prova("P5: il gergo da chat si segnala", "P5" in famiglie("Kinda wild when you think about it lol.\n"))
    prova("P3: 'non solo... ma anche' ripetuto tre volte si segnala per densità",
          "P3" in famiglie("Serve non solo a X ma anche a Y. Vale non solo qui ma anche là. "
                           "Aiuta non solo te ma anche noi.\n"))
    prova("P6: il lessico di maniera inglese si segnala",
          "P6" in famiglie("This is a testament to the team, and we delve into it.\n"))

    blocco = "Testo.\n\n```\nGli esperti ritengono che. Veloce. Semplice. Potente.\n```\n"
    prova("negativo: dentro un blocco di codice non si cerca niente", famiglie(blocco) == set(),
          str(famiglie(blocco)))
    prova("negativo: un segno citato fra virgolette è una menzione e non si segnala",
          famiglie("La formula «gli esperti ritengono» è un'attribuzione vaga.\n") == set())
    tabella = "| Gli esperti ritengono che il test sia utile |\n|---|\n"
    prova("negativo: dentro una tabella non si cerca niente", famiglie(tabella) == set())

    larghezza = max(len(n) for n, _, _ in esiti)
    falliti = 0
    for nome, ok, dettaglio in esiti:
        if not ok:
            falliti += 1
        print("  %s  %s%s" % (nome.ljust(larghezza), "ok" if ok else "FALLITO",
                              ("  " + dettaglio[:120]) if (dettaglio and not ok) else ""))
    print("")
    print("%d prove, %d fallite." % (len(esiti), falliti))
    return 1 if falliti else 0


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("percorsi", nargs="*", default=["."])
    p.add_argument("--gate", action="store_true", help="esce 1 se trova qualcosa")
    p.add_argument("--solo", help="famiglie da cercare, separate da virgola, per esempio P2,P3")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        return self_test()
    attive = set(a.solo.upper().split(",")) if a.solo else None
    totale, per_famiglia, file_con = 0, {}, 0
    for radice in a.percorsi:
        for percorso in cammina(radice):
            try:
                testo = io.open(percorso, encoding="utf-8").read()
            except (OSError, UnicodeDecodeError):
                continue
            trovati = cerca(testo, attive)
            if trovati:
                file_con += 1
            for riga, fam, desc, estratto in trovati:
                totale += 1
                per_famiglia[fam] = per_famiglia.get(fam, 0) + 1
                print("%s:%d  %s  %s%s" % (percorso, riga, fam, desc,
                                           ("  «" + estratto + "»") if estratto else ""))
    print("")
    print("%d segnalazioni in %d file: %s" % (
        totale, file_con, ", ".join("%s %d" % (k, per_famiglia[k]) for k in sorted(per_famiglia)) or "nessuna"))
    print("Sono punti da rileggere, non un giudizio: nessuno di questi segni prova da solo che un "
          "testo sia generato. Il perché di ciascuno sta in GUIDA.md del pacchetto anti-slop.")
    return 1 if (a.gate and totale) else 0


if __name__ == "__main__":
    sys.exit(main())
