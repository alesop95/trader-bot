#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trova nella documentazione i riferimenti a file che non esistono.

Perché esiste
-------------
Su un progetto reale è emerso per caso che il documento di contesto primario descriveva un file
di sorgente come parte dell'interfaccia. Quel file non esisteva, nessun altro file lo citava, e la
cosa descritta non c'era. L'errore stava nel punto peggiore in cui possa stare: non produce un
difetto nel codice, produce un difetto nel ragionamento di chi lo legge, e aveva quasi fatto
scrivere una descrizione falsa in un manuale d'uso.

È stato trovato perché qualcuno stava verificando una frase prima di copiarla. Cioè per fortuna.
Questo strumento rende meccanica quella fortuna: un documento che nomina un file inesistente è una
fotografia invecchiata, e la si può scoprire in un secondo invece che per caso.

Non verifica se una descrizione sia vera, che è un giudizio. Verifica solo se l'oggetto di cui
parla esista. È il sottoinsieme controllabile del problema, ed è quello che ha prodotto il difetto.

Le tre categorie, e perché non sono un elenco unico
----------------------------------------------------
Da correggere: un documento vivo che nomina un file assente. Va sistemato.

Storico: il work-log e le schede didattiche raccontano fatti con una data, e una voce di luglio che
nomina un file poi cancellato era vera quel giorno. Riscriverla falsificherebbe il registro. Si
segnala per conoscenza, non per correzione.

Modello: sotto `.claude/templates/` i percorsi sono convenzioni da istanziare in un progetto nuovo,
non file di questo progetto. Non sono errori per definizione.

Metterle in un elenco unico renderebbe lo strumento inservibile: cento segnalazioni di cui novanta
legittime insegnano a ignorare le altre dieci. È la stessa ragione per cui esistono i marcatori di
soppressione più sotto, e vale come criterio generale di ogni controllo automatico.

La quarta categoria, che esiste per un repository solo
-------------------------------------------------------
Bundle: il repository che contiene lo standard, invece di averlo adottato, nomina in continuazione
percorsi che un progetto ospite avrà e che qui non esistono per costruzione, come lo snapshot della
memoria o gli strumenti dei pacchetti visti dalla loro destinazione. Su quel repository le prime tre
categorie producono decine di segnalazioni tutte legittime, e la conclusione corretta non è
correggerle ma dichiarare che quel repository è il bundle, con l'opzione `--bundle`.

La distinzione non si indovina e non va indovinata, perché in un progetto ospite quelle stesse
segnalazioni sono vere e vanno lette: un documento che nomina `tools/md-unwrap.py` in un progetto
che non ha istanziato quel pacchetto sta descrivendo uno strumento che là non c'è. L'opzione è
quindi esplicita, e in modalità bundle una citazione finisce nella quarta categoria solo per due
ragioni verificabili: il bundle porta quel file sotto `templates/`, cioè lo nomina dalla sua
destinazione futura; oppure il percorso appartiene all'anatomia che il bundle crea in un progetto e
che nel bundle non esiste.

Che cosa non richiede configurazione, e perché
------------------------------------------------
Le radici che identificano un percorso del progetto non si scrivono a mano: si leggono da git, cioè
dalle cartelle e dai file di primo livello che il repository traccia. Una lista scritta a mano
sarebbe un secondo posto dove vive lo stesso fatto, quindi divergerebbe: una cartella nuova non
verrebbe controllata e nessuno se ne accorgerebbe, perché il difetto si manifesta come assenza di
segnalazioni. Dove git non risponda, si ripiega sul contenuto della cartella, dichiarandolo.

Il limite di quella scelta va detto invece di essere scoperto: un riferimento a un percorso che
comincia con una cartella che il repository non ha non viene controllato affatto, e non produce
nessuna segnalazione. È voluto, perché è così che si distingue un percorso da una frase, ma
significa che questo strumento non trova un riferimento a un albero che non esiste: trova i
riferimenti rotti dentro l'albero che c'è. Chi verifica una documentazione copiata da un altro
progetto tenga presente che i suoi percorsi, qui, sono invisibili.

Uso
---
    python tools/lint-doc-references.py              elenca le categorie
    python tools/lint-doc-references.py --solo-vivi  solo la categoria da correggere
    python tools/lint-doc-references.py --bundle     su questo repository, che e' il bundle
    python tools/lint-doc-references.py --self-test

Esce con codice diverso da zero se esiste almeno un riferimento della prima categoria, così si può
mettere in una verifica automatica prima di un commit.
"""

import argparse
import glob
import io
import os
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# I documenti vivi che raccontano fatti datati, dove un file poi cancellato era vero quel giorno.
# Sono prefissi di percorso, non nomi esatti, perché le schede didattiche sono numerate.
STORICI = ("memory/progress.md", "memory/decisions.md", "context/refactor-", "context/studio-",
           "context/archive-", "OPERATIONS.md", "CASE-STUDIES.md")

# Dove vivono le convenzioni da istanziare, che nominano percorsi di un progetto che non è questo.
MODELLO = ("templates/",)

# L'anatomia che il bundle crea in un progetto ospite e che nel bundle non esiste. Serve alla sola
# modalità bundle, e non va confusa con un elenco di eccezioni: sono i percorsi che il bundle
# nomina per prescriverli, non per descrivere sé stesso.
ANATOMIA_OSPITE = (".claude/memory/", ".claude/context/", ".claude/commands/",
                   ".claude/agents/", "_notes/")

# Marcatori di soppressione. Servono per la specie di falso positivo più numerosa e più insidiosa:
# un documento che nomina un percorso proprio per dire che non esiste più. La tabella "dov'era e
# dov'è ora" di un indice, la nota che corregge una sezione rimossa, il racconto di un file
# aggiunto al gitignore: in tutti questi casi l'assenza del file è il contenuto, e segnalarla come
# difetto renderebbe lo strumento inutile.
#
# Sono espliciti e cercabili di proposito. Un elenco di eccezioni dentro lo strumento sarebbe
# invisibile a chi scrive il documento; un marcatore nel documento sta accanto alla riga che lo
# richiede, e chi cancella quella riga si porta via anche l'eccezione.
MARCATORE_RIGA = "<!-- ref-assente -->"
MARCATORE_INIZIO = "<!-- ref-assente: inizio -->"
MARCATORE_FINE = "<!-- ref-assente: fine -->"

# Estensioni dopo le quali un due punti introduce un simbolo o una riga, non fa parte del percorso.
ESTENSIONI = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".json", ".md", ".rules", ".yml", ".yaml",
              ".html", ".css", ".ps1", ".sh", ".py", ".toml", ".cfg", ".txt", ".tex", ".sql")


def radici(radice=None):
    """Le cartelle e i file di primo livello che il repository traccia.

    Si leggono da git invece di essere elencati, perché un elenco scritto a mano sarebbe un secondo
    posto dove vive lo stesso fatto e divergerebbe in silenzio: una cartella nuova smetterebbe di
    essere controllata senza che nessuno veda nulla, perché il sintomo è l'assenza di segnalazioni.
    """
    cartelle, file = set(), set()
    fonte = "git"
    try:
        p = subprocess.run(["git", "ls-files"], cwd=radice, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        voci = p.stdout.splitlines() if p.returncode == 0 else []
    except FileNotFoundError:
        voci = []
    if not voci:
        fonte = "cartella"
        base = radice or "."
        voci = []
        for nome in os.listdir(base):
            if nome == ".git":
                continue
            voci.append(nome + "/" if os.path.isdir(os.path.join(base, nome)) else nome)
    for voce in voci:
        voce = voce.replace("\\", "/")
        if "/" in voce:
            cartelle.add(voce.split("/", 1)[0] + "/")
        else:
            file.add(voce.rstrip("/"))
    return tuple(sorted(cartelle)), frozenset(file), fonte


def normalizza(token):
    """Riduce un token alla sola parte che puo' essere un percorso.

    Due riduzioni, per due forme che senza di esse produrrebbero falsi positivi. La prima toglie il
    riferimento a un simbolo o a una riga che segue il nome del file. La seconda tiene il solo primo
    campo separato da spazi, perche' un comando scritto con i suoi argomenti fra apici inversi non
    e' un percorso: un percorso che contenga davvero uno spazio verrebbe troncato, ma l'esito e' una
    mancata segnalazione invece di una falsa, che e' il verso giusto in cui sbagliare per uno
    strumento la cui utilita' dipende dal fatto che chi lo legge si fidi delle sue righe.
    """
    token = token.split()[0] if token.split() else token
    for est in ESTENSIONI:
        i = token.find(est + ":")
        if i != -1:
            return token[:i + len(est)]
    return token


def e_percorso(token, cartelle, file_radice):
    """Un token è un percorso da controllare solo se non contiene segnaposto o caratteri jolly."""
    if any(c in token for c in "<>*{}$|"):
        return False
    if token.endswith("/") or not token:
        return False
    return token.startswith(cartelle) or token in file_radice


def prescritti_dal_bundle(radice=None):
    """I percorsi che il bundle nomina sotto `templates/`, cioe' quelli che prescrive.

    Si calcolano una volta per corsa e si passano a chi classifica, invece di essere memoizzati per
    percorso: una cache per percorso restituirebbe un insieme vecchio a chi analizzasse due volte
    la stessa cartella dopo averne cambiato il contenuto, che in esercizio non accade mai e in una
    prova accade subito.

    Il criterio e' volutamente largo, e vale solo in modalita' bundle: se il bundle nomina un
    percorso nei propri modelli, quel percorso appartiene al progetto ospite e non a questo
    repository. Fuori da quella modalita' l'insieme non si usa, perche' in un progetto ospite la
    stessa citazione descrive un file che deve esserci davvero.
    """
    fuori = set()
    base = os.path.join(radice or ".", ".claude", "templates")
    if not os.path.isdir(base):
        return fuori
    for cartella, _c, file in os.walk(base):
        for f in file:
            if not f.endswith(".md"):
                continue
            testo = io.open(os.path.join(cartella, f), encoding="utf-8", errors="replace").read()
            for pezzo in re.findall(r"[A-Za-z0-9_./<>-]{3,}", testo):
                pezzo = pezzo.replace("<radice>/", "").strip("/")
                if "/" in pezzo and "." in os.path.basename(pezzo):
                    fuori.add(pezzo)
    return fuori


def portato_dal_bundle(token, radice=None, prescritti=None):
    """Vero se il bundle porta o prescrive quel file, per nome o come percorso nominato."""
    base = os.path.join(radice or ".", ".claude", "templates")
    if not os.path.isdir(base):
        return False
    if token.replace("\\", "/") in (prescritti or set()):
        return True
    nome = os.path.basename(token)
    for cartella, _c, file in os.walk(base):
        if nome in file:
            return True
    return False


def categoria(documento, token=None, bundle=False, radice=None, prescritti=None):
    d = documento.replace("\\", "/")
    if any(m in d for m in MODELLO):
        return "modello"
    if any(s in d for s in STORICI):
        return "storico"
    if bundle and token is not None:
        if token.replace("\\", "/").startswith(ANATOMIA_OSPITE):
            return "bundle"
        if portato_dal_bundle(token, radice, prescritti):
            return "bundle"
    return "vivo"


def documenti_da_leggere(radice=None):
    base = radice or "."
    fuori = []
    for schema in (".claude/**/*.md", "docs/**/*.md", "_notes/*.md", "*.md"):
        fuori += sorted(glob.glob(os.path.join(base, schema), recursive=True))
    visti, unici = set(), []
    for f in fuori:
        rel = os.path.relpath(f, base).replace("\\", "/")
        if rel not in visti:
            visti.add(rel)
            unici.append(rel)
    return unici


def analizza(radice=None, bundle=False):
    """Ritorna il dizionario delle tre categorie e la fonte delle radici."""
    cartelle, file_radice, fonte = radici(radice)
    base = radice or "."
    trovati = {"vivo": [], "storico": [], "modello": [], "bundle": []}
    prescritti = prescritti_dal_bundle(radice) if bundle else set()
    for documento in documenti_da_leggere(radice):
        percorso = os.path.join(base, documento)
        if not os.path.isfile(percorso):
            continue
        testo = io.open(percorso, encoding="utf-8", errors="replace", newline="").read()
        soppresso = False
        for numero, riga in enumerate(testo.split("\n"), 1):
            if MARCATORE_INIZIO in riga:
                soppresso = True
                continue
            if MARCATORE_FINE in riga:
                soppresso = False
                continue
            if soppresso or MARCATORE_RIGA in riga:
                continue
            # Solo i riferimenti fra apici inversi: un percorso scritto in prosa nuda e' spesso una
            # frase, per esempio "i file in src", e produrrebbe rumore che nessuno legge.
            for token in re.findall(r"`([^`\n]+)`", riga):
                token = normalizza(token.strip().rstrip(".,;:)"))
                if not e_percorso(token, cartelle, file_radice):
                    continue
                if os.path.exists(os.path.join(base, token)):
                    continue
                trovati[categoria(documento, token, bundle, radice, prescritti)].append(
                    (documento, numero, token))
    return trovati, fonte, cartelle


# ------------------------------------------------------------------------------------------
# Le prove, su un albero sintetico. Non toccano il repository dove vivono.
# ------------------------------------------------------------------------------------------

def self_test():
    import shutil
    import tempfile
    esiti = []

    def prova(nome, condizione, dettaglio=""):
        esiti.append((nome, bool(condizione), dettaglio))

    tmp = tempfile.mkdtemp(prefix="lint-doc-ref-")
    try:
        def scrivi(rel, testo):
            p = os.path.join(tmp, rel)
            d = os.path.dirname(p)
            if d and not os.path.isdir(d):
                os.makedirs(d)
            io.open(p, "w", encoding="utf-8", newline="\n").write(testo)

        scrivi("src/esiste.ts", "// c'e'\n")
        scrivi("CLAUDE.md", "Il file `src/esiste.ts` c'e'. Il file `src/sparito.ts` no.\n")
        scrivi(".claude/memory/progress.md", "Voce datata che nomina `src/cancellato.ts`.\n")
        scrivi(".claude/templates/CLAUDE.md", "Il modello nomina `src/qualsiasi.ts`.\n")

        trovati, fonte, cartelle = analizza(tmp)
        vivi = [t for _d, _n, t in trovati["vivo"]]
        prova("un documento vivo che nomina un file assente si segnala",
              "src/sparito.ts" in vivi, str(vivi))
        prova("negativo: un file che esiste non si segnala", "src/esiste.ts" not in vivi, str(vivi))
        prova("una voce datata finisce fra gli storici",
              any(t == "src/cancellato.ts" for _d, _n, t in trovati["storico"]), str(trovati))
        prova("un percorso dentro i modelli finisce fra i modelli",
              any(t == "src/qualsiasi.ts" for _d, _n, t in trovati["modello"]), str(trovati))
        prova("le radici si ricavano senza configurazione", "src/" in cartelle, str(cartelle))
        prova("senza git la fonte delle radici si dichiara", fonte == "cartella", fonte)

        # I marcatori di soppressione, che coprono il falso positivo piu' frequente.
        scrivi("CLAUDE.md", "Il file `src/rimosso.ts` non esiste piu'. " + MARCATORE_RIGA + "\n")
        trovati, _f, _c = analizza(tmp)
        prova("negativo: il marcatore di riga sopprime la segnalazione",
              trovati["vivo"] == [], str(trovati["vivo"]))

        scrivi("CLAUDE.md", MARCATORE_INIZIO + "\nTabella:\n`src/a.ts` -> `src/b.ts`\n"
               + MARCATORE_FINE + "\nE qui `src/fuori.ts` invece conta.\n")
        trovati, _f, _c = analizza(tmp)
        vivi = [t for _d, _n, t in trovati["vivo"]]
        prova("negativo: il blocco soppresso non produce segnalazioni",
              "src/a.ts" not in vivi and "src/b.ts" not in vivi, str(vivi))
        prova("dopo la fine del blocco la segnalazione riprende",
              "src/fuori.ts" in vivi, str(vivi))

        # La quarta categoria, e il fatto che senza dichiararla non si attivi.
        scrivi(".claude/rules/una-regola.md",
               "La regola cita `.claude/memory/index.md` e lo strumento `tools/md-unwrap.py`.\n")
        scrivi(".claude/templates/tools/md-unwrap.py", "# lo strumento vive nel bundle\n")
        # La radice `tools/` deve esistere, altrimenti il token non e' nemmeno un percorso
        # da controllare e la prova passerebbe per la ragione sbagliata.
        scrivi("tools/altro.py", "# la cartella degli strumenti del progetto esiste")
        senza, _f, _c = analizza(tmp, bundle=False)
        prova("negativo: senza dichiararlo, in un progetto ospite quelle citazioni restano difetti",
              len([t for _d, _n, t in senza["vivo"]]) >= 2, str(senza["vivo"]))
        con, _f, _c = analizza(tmp, bundle=True)
        bundle = [t for _d, _n, t in con["bundle"]]
        prova("in modalita' bundle l'anatomia ospite non e' un riferimento rotto",
              ".claude/memory/index.md" in bundle, str(bundle))
        prova("in modalita' bundle lo strumento nominato dalla destinazione non e' rotto",
              "tools/md-unwrap.py" in bundle, str(bundle))
        scrivi(".claude/templates/profili/README.md",
               "templates/profili/<nome>.md  ->  <radice>/.claude/rules/profilo-scelto.md\n")
        scrivi(".claude/rules/altra-regola.md",
               "La regola cita `.claude/rules/profilo-scelto.md`, che un pacchetto creera'.")
        con2, _f, _c = analizza(tmp, bundle=True)
        prova("una destinazione dichiarata con un nome diverso dalla sorgente non e' rotta",
              any(t == ".claude/rules/profilo-scelto.md" for _d, _n, t in con2["bundle"]),
              str([t for _d, _n, t in con2["vivo"]]))

        prova("negativo: in modalita' bundle un file che il bundle non porta resta un difetto",
              any(t == "src/sparito.ts" for _d, _n, t in con["vivo"])
              or all(t != "src/sparito.ts" for _d, _n, t in con["bundle"]), str(con))

        # I casi che senza le loro difese produrrebbero rumore.
        scrivi("CLAUDE.md", "La funzione `src/esiste.ts:faQualcosa` e il glob `src/*.ts`, "
                            "e il segnaposto `src/<nome>.ts`, e la prosa src/nuda.ts\n")
        trovati, _f, _c = analizza(tmp)
        vivi = [t for _d, _n, t in trovati["vivo"]]
        prova("negativo: un simbolo dopo i due punti non falsa il percorso",
              "src/esiste.ts" not in vivi and "src/esiste.ts:faQualcosa" not in vivi, str(vivi))
        prova("negativo: un carattere jolly non e' un percorso", "src/*.ts" not in vivi, str(vivi))
        prova("negativo: un segnaposto non e' un percorso",
              not any("<nome>" in t for t in vivi), str(vivi))
        prova("negativo: un percorso in prosa nuda non si conta",
              "src/nuda.ts" not in vivi, str(vivi))

        # Il falso positivo trovato usando lo strumento su un documento vero.
        scrivi("CLAUDE.md", "Si lancia `src/esiste.ts --con-argomenti` e poi "
                            "`src/assente.ts --altro`.")
        trovati, _f, _c = analizza(tmp)
        vivi = [t for _d, _n, t in trovati["vivo"]]
        prova("negativo: un comando con i suoi argomenti non e' un percorso rotto",
              "src/esiste.ts" not in vivi and not any(" " in t for t in vivi), str(vivi))
        prova("il percorso dentro un comando si controlla comunque",
              "src/assente.ts" in vivi, str(vivi))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    larghezza = max(len(n) for n, _, _ in esiti)
    falliti = 0
    for nome, ok, dettaglio in esiti:
        if not ok:
            falliti += 1
        print("  %s  %s%s" % (nome.ljust(larghezza), "ok" if ok else "FALLITO",
                              ("  " + dettaglio[:150]) if (dettaglio and not ok) else ""))
    print("")
    print("%d prove, %d fallite." % (len(esiti), falliti))
    return 1 if falliti else 0


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--solo-vivi", action="store_true",
                   help="stampa la sola categoria da correggere")
    p.add_argument("--bundle", action="store_true",
                   help="questo repository e' il bundle dello standard e non un progetto che lo ha "
                        "adottato: i percorsi dell'anatomia ospite non sono riferimenti rotti")
    p.add_argument("--radice", help="radice del progetto; per difetto la cartella corrente")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()

    if a.self_test:
        return self_test()

    trovati, fonte, _cartelle = analizza(a.radice, bundle=a.bundle)
    etichette = {
        "vivo": "DA CORREGGERE (documento vivo che nomina un file assente)",
        "storico": "STORICO (voce datata: era vera quel giorno, non si riscrive)",
        "modello": "MODELLO (convenzione per progetti nuovi, non un file di questo)",
        "bundle": "BUNDLE (anatomia o strumento che il bundle prescrive a un progetto ospite)",
    }
    for chiave in ("vivo", "storico", "modello", "bundle"):
        if a.solo_vivi and chiave != "vivo":
            continue
        voci = trovati[chiave]
        print("")
        print("=== %s: %d ===" % (etichette[chiave], len(voci)))
        visti = set()
        for documento, numero, token in voci:
            firma = (documento, token)
            if firma in visti:
                continue
            visti.add(firma)
            print("  %s:%d  ->  %s" % (documento, numero, token))

    print("")
    if fonte == "cartella":
        print("nota: git non ha risposto, le radici vengono dal contenuto della cartella e "
              "possono comprendere materiale non tracciato")
    if trovati["vivo"]:
        print("%d riferimenti da correggere in documenti vivi." % len(trovati["vivo"]))
        return 1
    print("nessun riferimento rotto nei documenti vivi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
