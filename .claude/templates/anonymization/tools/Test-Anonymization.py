# -*- coding: utf-8 -*-
"""
Guard-rail di anonimizzazione sui file del repository.

Perché esiste. Quando un repository è pubblico, o anche solo condiviso più largamente di
chi lo scrive, tutto ciò che entra in un file tracciato è visibile per sempre, anche dopo
una correzione successiva, perché la storia git resta consultabile finché non viene
riscritta. La regola che governa la materia è `.claude/rules/anonymization.md`, ma una
regola scritta non impedisce un residuo: nel progetto in cui questo strumento è nato il
primo audit ne ha trovati centoquarantotto su ottantanove file, **nessuno introdotto di
proposito e nessuno appartenente alla sessione che li ha scoperti**. Un residuo non si
introduce, si eredita, e per questo il controllo si fa sull'intero perimetro e non sui soli
file toccati.

Che cosa cerca, e perché non sono soltanto i segreti. Uno scanner di credenziali cerca
chiavi e token, cioè stringhe con una forma riconoscibile. Questo cerca una categoria
diversa e più insidiosa, cioè i dati che identificano persone, luoghi e infrastrutture:
indirizzi IP reali, indirizzi fisici di apparati, nomi propri di persona, caselle di posta
personali, numeri di telefono, importi, IBAN e partite IVA. Sono dati che nessun pattern
universale riconosce, perché un nome proprio è un nome proprio solo se è di qualcuno:
per questo l'elenco di ciò che va cercato vive fuori dallo script.

Come non tradisce se stesso. Questo script è versionato e **non contiene nessun valore
reale**: prefissi di rete, nomi propri, indirizzi di posta, prefissi telefonici e segreti
letterali da cercare vivono in un file di pattern ignorato da git, accanto alla mappa dei
segnaposto. Se quel file manca, lo script lo dice e si ferma invece di dare un esito verde
che non ha calcolato. È la proprietà che rende pubblicabile lo strumento che serve a
tenere pubblicabile il repository.

Il perimetro, e perché dal 07/09/2026 non è più soltanto ciò che git traccia. Fino a
quella data lo script passava `git ls-files`, cioè i soli file già tracciati, e ne
derivava una lacuna precisa: un file **nuovo**, scritto e non ancora aggiunto all'indice,
era invisibile al controllo proprio nel momento in cui serviva guardarlo, cioè prima di
pubblicarlo. È accaduto il 04/09/2026 con tre file nuovi, e il difetto è della stessa
famiglia degli altri due già corretti in questo progetto, la cartella esclusa del delta e
i pattern di rilevanza: non si sbaglia su ciò che si conosce, si sbaglia sul confine.

Il perimetro predefinito è perciò **ciò che sta per essere pubblicato**: i file tracciati
più quelli non tracciati e non ignorati, che sono esattamente i candidati al prossimo
commit. I riscontri di entrambi i gruppi sono bloccanti, perché entrambi i gruppi finiscono
in pubblico.

Con `--tutti` entrano anche i file **ignorati**, cioè `_notes/` e `output/`. Quelli
contengono valori reali **per costruzione e per decisione**: sono il layer narrativo locale e
gli output degli script, ed è il motivo per cui git li ignora. I loro riscontri vengono
quindi elencati a parte e **non sono bloccanti**: servono a sapere che cosa vive sul disco, non
a dichiarare un difetto. Confonderli con i primi renderebbe lo script inutile, perché
fallirebbe sempre e nessuno lo guarderebbe più.

Uso, dalla radice del progetto:
    python tools/Test-Anonymization.py             # tracciati + non tracciati non ignorati
    python tools/Test-Anonymization.py --tutti     # anche il layer privato, non bloccante
    python tools/Test-Anonymization.py --quiet     # solo il conteggio e l'esito
    python tools/Test-Anonymization.py --max 20    # limita le righe stampate per categoria
    python tools/Test-Anonymization.py --patterns <percorso>   # file di pattern altrove

Codice di uscita: 0 se non ci sono riscontri nelle categorie bloccanti, 1 altrimenti. Le
categorie non bloccanti raccolgono ciò che va guardato da un umano e che è spesso un
falso positivo, per esempio un numero di versione che somiglia a un indirizzo.
"""

import argparse
import collections
import io
import json
import os
import re
import subprocess
import sys

# Percorso predefinito del file di pattern. Sta in `_notes/` perché quella cartella è
# ignorata da git in questo sistema di progetto: è il layer che può contenere valori reali.
# Si sposta con --patterns nei progetti che organizzano diversamente il proprio layer privato.
PATTERNS_FILE = os.path.join("_notes", ".anonymization-patterns.json")
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".xlsx", ".docx", ".zip", ".ico", ".drawio",
            # aggiunte il 07/09/2026 con l'allargamento del perimetro: entrando anche i file
            # non tracciati e, con --tutti, quelli ignorati, si incontrano archivi ed eseguibili
            # in cui una ricerca per riga non ha alcun senso e costa solo tempo.
            ".7z", ".rar", ".msi", ".exe", ".dll", ".pyc", ".bin", ".db", ".sqlite", ".qdff",
            ".mp4", ".mov", ".xlsm", ".pptx", ".doc", ".xls", ".vsdx", ".eml", ".msg"}
# Un file molto grande in un layer privato è tipicamente uno storico o un dump: leggerlo
# riga per riga costa minuti e non aggiunge segnale. Si dichiara di averlo saltato.
LIMITE_BYTE = 5 * 1024 * 1024

# Categorie che fanno fallire il controllo: sono valori reali, non ambiguità.
BLOCCANTI = {"IP REALE", "MAC REALE", "NOME PROPRIO", "SEGRETO LETTERALE",
             "EMAIL PERSONALE", "TELEFONO", "IBAN", "CARTA DI PAGAMENTO", "PIVA/CF", "IMPORTO"}

IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b")
MAC = re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
# I prefissi telefonici da cercare non possono stare qui: un numero di telefono è un dato
# personale solo se è di qualcuno, e quali prefissi appartengano al progetto lo sa il file
# dei pattern. Se la chiave `prefissi_telefonici` manca, si ripiega sul solo formato
# internazionale, che è riconoscibile senza sapere nulla del progetto.
PHONE_FALLBACK = re.compile(r"\b\+\d{2}\s?\d{9,10}\b")
MONEY = re.compile(r"(?:€\s?[\d.,]+|\b[\d.]+[,.]\d{2}\s?(?:€|euro|EUR)\b|\b\d+(?:[.,]\d+)?\s?euro\b)", re.I)
# L'IBAN, dal 2026-10-07 in ogni forma in cui lo si scrive davvero. Fino ad allora il
# controllo era `\bIT\d{2}[A-Z0-9]{20,25}\b`, che trovava soltanto un IBAN italiano scritto
# tutto attaccato e in maiuscolo: non la forma a gruppi di quattro separati da spazi, che è
# quella di ogni estratto conto e di ogni modulo, non il minuscolo, non un conto estero. Il
# candidato ammette spazi singoli fra i caratteri e qualsiasi paese; poi si tiene solo se la
# lunghezza è quella del paese e la cifra di controllo modulo 97 della norma ISO 13616 torna,
# cosa che una stringa qualunque fa una volta su novantasette.
IBAN_CANDIDATO = re.compile(r"\b[A-Za-z]{2}\d{2}(?: ?[A-Za-z0-9]){10,32}\b")
LUNGHEZZE_IBAN = {
    "AD": 24, "AT": 20, "BE": 16, "BG": 22, "CH": 21, "CY": 28, "CZ": 24, "DE": 22, "DK": 18,
    "EE": 20, "ES": 24, "FI": 18, "FR": 27, "GB": 22, "GI": 23, "GR": 27, "HR": 21, "HU": 28,
    "IE": 22, "IS": 26, "IT": 27, "LI": 21, "LT": 20, "LU": 20, "LV": 21, "MC": 27, "MT": 31,
    "NL": 18, "NO": 15, "PL": 28, "PT": 25, "RO": 24, "SE": 24, "SI": 19, "SK": 24, "SM": 27,
    "VA": 22,
}
# Il numero di una carta di pagamento, da 13 a 19 cifre, anche a gruppi separati da spazi o
# trattini. In un repository tecnico i numeri lunghi sono ovunque, quindi si tiene solo se
# comincia con un prefisso di circuito (4 Visa, 51-55 e 2221-2720 Mastercard, 34 e 37 American
# Express, 6011, 644-649 e 65 Discover, 35 JCB, 36 e 38 Diners) e se la cifra di controllo di
# Luhn torna.
CARTA_CANDIDATA = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")


def iban_valido(testo):
    """Restituisce l'IBAN normalizzato se `testo`, o un suo inizio, è un IBAN valido."""
    s = re.sub(r"\s", "", testo).upper()
    n = LUNGHEZZE_IBAN.get(s[:2])
    if not n or len(s) < n:
        return None
    s = s[:n]
    numero = "".join(str(int(c, 36)) for c in s[4:] + s[:4])
    return s if int(numero) % 97 == 1 else None


def carta_valida(testo):
    """Restituisce le cifre se `testo` è il numero di una carta di pagamento plausibile."""
    cifre = re.sub(r"[ -]", "", testo)
    n = len(cifre)
    if not 13 <= n <= 19:
        return None
    # Oltre le sedici cifre una carta si scrive a gruppi. Il vincolo nasce dalla prima misura su
    # un progetto vero, il 2026-10-07: l'identificativo di un canale Discord, diciotto cifre
    # attaccate che cominciano per 4, passava Luhn come capita a un numero su dieci. Gli
    # identificativi di Discord e dei social hanno 17-19 cifre e non hanno mai separatori.
    if n > 16 and n == len(testo):
        return None
    p2, p3, p4 = int(cifre[:2]), int(cifre[:3]), int(cifre[:4])
    # Le lunghezze che ciascun circuito ammette: una lunghezza fuori dal circuito è un altro numero.
    if cifre[0] == "4":
        ammesse = (13, 16, 19)
    elif 51 <= p2 <= 55 or 2221 <= p4 <= 2720:
        ammesse = (16,)
    elif p2 in (34, 37):
        ammesse = (15,)
    elif p2 in (36, 38):
        ammesse = range(14, 20)
    elif p2 in (35, 65) or p4 == 6011 or 644 <= p3 <= 649:
        ammesse = range(16, 20)
    else:
        return None
    if n not in ammesse:
        return None
    somma = 0
    for i, c in enumerate(reversed(cifre)):
        d = int(c) * (2 if i % 2 else 1)
        somma += d - 9 if d > 9 else d
    return cifre if somma % 10 == 0 else None


PIVA =re.compile(r"\b(?:P\.?\s?IVA|partita iva|cod\.?\s?fisc|codice fiscale)\b[^\n]{0,40}\d{11,16}", re.I)
# Domini riservati alla documentazione da RFC 2606: non esistono, non sono registrabili
# e non possono appartenere a nessuno, quindi una casella su di essi è un esempio e non il
# dato di una persona. È la stessa ammissione per costruzione che vale per i blocchi di
# indirizzi di RFC 5737, e la sua assenza era un'asimmetria: senza di essa ogni documento
# che usa un indirizzo di esempio produce un riscontro bloccante, e chi scrive documentazione
# impara a ignorare l'esito del controllo.
DOMINI_DOC = ("example.com", "example.org", "example.net", "example.edu", ".example")

# Segnaposto legittimi per la posta: persona-a@, referente-esempio-1@, e simili.
MAIL_PLACEHOLDER = re.compile(r"^(persona|referente|collaboratore|consulente|tirocinante)-", re.I)


def trova_radice(partenza=None):
    """Risale fino alla radice del repository partendo dalla posizione di questo file.

    Perché dalla posizione del file e non dalla cartella corrente. La cartella corrente
    dipende da chi invoca, e chi invoca può essere una sessione interattiva, un hook, una
    attività pianificata o un altro script: sono quattro cartelle diverse per lo stesso
    comando, e il messaggio d'errore che ne segue parla d'altro. La posizione del file
    invece è un fatto. Il criterio funziona identico su Windows e su Linux perché non
    guarda separatori né lettere di unità.

    `.git` si cerca sia come cartella sia come file, perché in un worktree o in un
    sottomodulo è un file che punta altrove: trattarla come sola cartella è un difetto
    che si manifesta soltanto in quei due casi, cioè tardi.
    """
    corrente = os.path.abspath(partenza or os.path.dirname(os.path.abspath(__file__)))
    while True:
        candidata = os.path.join(corrente, ".git")
        if os.path.isdir(candidata) or os.path.isfile(candidata):
            return corrente
        genitore = os.path.dirname(corrente)
        if genitore == corrente:
            return None
        corrente = genitore


def carica_pattern(percorso=PATTERNS_FILE):
    """Carica il file di pattern, oppure si ferma dichiarandolo.

    Fermarsi invece di proseguire con un elenco vuoto è una scelta e non una svista: un
    controllo senza pattern non trova nulla e stamperebbe un verde, che è la peggiore
    delle uscite possibili perché assomiglia a un esito senza esserlo."""
    if not os.path.exists(percorso):
        sys.stderr.write(
            "File dei pattern non trovato: %s\n"
            "Serve per sapere che cosa cercare, e non è versionato perché contiene i valori\n"
            "reali del progetto. Si costruisce dalla mappa dei segnaposto, partendo da\n"
            "patterns.example.json di questo pacchetto.\n"
            "Senza di esso questo controllo non si dichiara verde: si ferma.\n" % percorso)
        sys.exit(2)
    with io.open(percorso, encoding="utf-8") as fh:
        pat = json.load(fh)
    obbligatorie = ("reti_documentali_ammesse", "ip_ammessi", "prefissi_reali",
                    "mac_ammessi_prefissi", "email_ammesse", "nomi_propri")
    mancanti = [k for k in obbligatorie if k not in pat]
    if mancanti:
        sys.stderr.write(
            "Il file dei pattern non ha le chiavi obbligatorie: %s\n"
            "Vedi patterns.example.json per la forma attesa.\n" % ", ".join(mancanti))
        sys.exit(2)
    return pat


def _git(*argomenti):
    out = subprocess.run(["git"] + list(argomenti), capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout
    return [f for f in out.split("\n") if f.strip()]


def file_perimetro(includi_ignorati):
    """Restituisce [(percorso, origine)] con origine tracciato/non tracciato/ignorato.

    L'ordine conta: prima ciò che è già pubblico, poi ciò che sta per diventarlo, poi
    il layer privato. È anche l'ordine di gravità con cui i riscontri vanno letti.
    """
    elenco = [(f, "tracciato") for f in _git("ls-files")]
    elenco += [(f, "non tracciato") for f in _git("ls-files", "--others", "--exclude-standard")]
    if includi_ignorati:
        elenco += [(f, "ignorato") for f in _git("ls-files", "--others", "--ignored",
                                                 "--exclude-standard")]
    visti = set()
    unici = []
    for f, origine in elenco:
        if f not in visti:
            visti.add(f)
            unici.append((f, origine))
    return unici


def analizza(pat, files):
    """`files` è una lista di coppie (percorso, origine). L'origine viaggia con il
    riscontro fino alla stampa, perché lo stesso valore reale ha significato opposto a
    seconda di dove sta: in un file tracciato è un leak, in `_notes/` è il dato."""
    trovati = collections.defaultdict(list)
    saltati = []

    def aggiungi(cat, path, ln, riga, hit, origine="tracciato"):
        trovati[cat].append((path, ln, hit, riga.strip()[:190], origine))

    prefissi_tel = pat.get("prefissi_telefonici", [])
    if prefissi_tel:
        alternative = "|".join(re.escape(x) + r"\s?\d{5,8}" for x in prefissi_tel)
        phone = re.compile(r"\b(?:%s|\+\d{2}\s?\d{9,10})\b" % alternative)
    else:
        phone = PHONE_FALLBACK

    doc_nets = tuple(pat["reti_documentali_ammesse"])
    ip_ok = set(pat["ip_ammessi"])
    reali = tuple(pat["prefissi_reali"])
    mac_ok = tuple(m.upper() for m in pat["mac_ammessi_prefissi"])
    mail_ok = set(m.lower() for m in pat["email_ammesse"])
    nomi = pat["nomi_propri"]
    nomi_ctx = pat.get("nomi_ammessi_in_contesto", [])
    segreti = pat.get("segreti_letterali", [])

    for f, origine in files:
        if os.path.splitext(f)[1].lower() in SKIP_EXT:
            continue
        try:
            if os.path.getsize(f) > LIMITE_BYTE:
                saltati.append(f)
                continue
            with io.open(f, encoding="utf-8", errors="replace") as fh:
                contenuto = fh.read()
        except (IOError, OSError):
            continue

        for ln, riga in enumerate(contenuto.split("\n"), 1):
            for m in IPV4.finditer(riga):
                ip = m.group(0)
                base = ip.split("/")[0]
                if base in ip_ok or base.startswith(doc_nets):
                    continue
                if base.startswith(reali):
                    aggiungi("IP REALE", f, ln, riga, ip, origine)
                elif base.startswith(("10.", "192.168.", "172.")):
                    aggiungi("IP privato fuori schema", f, ln, riga, ip, origine)
                else:
                    aggiungi("IP pubblico da valutare", f, ln, riga, ip, origine)

            for m in MAC.finditer(riga):
                mac = m.group(0).upper()
                if mac.startswith(mac_ok):
                    continue
                aggiungi("MAC REALE", f, ln, riga, mac, origine)

            for m in EMAIL.finditer(riga):
                mail = m.group(0)
                locale = mail.split("@")[0]
                dominio = mail.split("@")[-1].lower()
                if (mail.lower() in mail_ok
                        or MAIL_PLACEHOLDER.match(locale)
                        or dominio.endswith(DOMINI_DOC)):
                    continue
                aggiungi("EMAIL PERSONALE", f, ln, riga, mail, origine)

            for regex, cat in ((phone, "TELEFONO"), (MONEY, "IMPORTO"), (PIVA, "PIVA/CF")):
                for m in regex.finditer(riga):
                    aggiungi(cat, f, ln, riga, m.group(0)[:60], origine)

            for m in IBAN_CANDIDATO.finditer(riga):
                if iban_valido(m.group(0)):
                    aggiungi("IBAN", f, ln, riga, "<IBAN oscurato>", origine)

            for m in CARTA_CANDIDATA.finditer(riga):
                if carta_valida(m.group(0)):
                    aggiungi("CARTA DI PAGAMENTO", f, ln, riga, "<numero oscurato>", origine)

            for s in segreti:
                if s in riga:
                    aggiungi("SEGRETO LETTERALE", f, ln, riga, "<valore oscurato>", origine)

            bassa = riga.lower()
            for n in nomi:
                if n.lower() not in bassa:
                    continue
                # un nome dentro la ragione sociale legale è ammesso per decisione
                if any(c.lower() in bassa for c in nomi_ctx):
                    continue
                aggiungi("NOME PROPRIO", f, ln, riga, n, origine)

    return trovati, saltati


def autotest():
    """Prova dei riconoscitori di IBAN e carte di pagamento, dal 2026-10-07.

    I valori sono quelli pubblicati come esempio dalla norma e dai circuiti, e si compongono
    a pezzi: scritti interi in questo file, il controllo li troverebbe nel proprio sorgente.
    Ogni caso positivo ha accanto un negativo che differisce per una sola proprietà, perché
    una prova che passa anche con il riconoscitore spento non misura niente.
    """
    it = "IT60" + " X054 2811 1010 0000 0123 456"
    gb = "GB82" + " WEST 1234 5698 7654 32"
    casi_iban = [
        (it, True, "italiano a gruppi di quattro"),
        (it.replace(" ", ""), True, "italiano attaccato"),
        (it.lower(), True, "minuscolo"),
        (gb, True, "britannico"),
        ("bonifico su " + it.replace(" ", "") + " entro venerdì", True, "dentro una frase"),
        ("IT61" + it[4:], False, "cifra di controllo sbagliata"),
        (it[:14], False, "troncato"),
        ("AB12" + " CDEF GHIJ KLMN OP", False, "paese inesistente"),
        ("PK67" + " offset 0x0E", False, "testo tecnico"),
    ]
    casi_carta = [
        ("4111" + " 1111" + " 1111" + " 1111", True, "Visa a gruppi"),
        ("5500" + "-0000" + "-0000" + "-0004", True, "Mastercard con trattini"),
        ("378282" + "246310005", True, "American Express attaccata"),
        ("4111" + " 1111" + " 1111" + " 1112", False, "Luhn sbagliato"),
        ("1583996519" + "325147137", False, "identificativo di un post, prefisso 1"),
        ("9111" + "1111" + "1111" + "1111", False, "prefisso di nessun circuito"),
    ]

    def _luhn_ok(cifre):
        somma = 0
        for i, c in enumerate(reversed(cifre)):
            d = int(c) * (2 if i % 2 else 1)
            somma += d - 9 if d > 9 else d
        return somma % 10 == 0

    def con_luhn(corpo):
        """Aggiunge a `corpo` la cifra di controllo di Luhn: serve a costruire numeri che la
        superano, così che i negativi sotto falliscano per la regola che vogliono provare."""
        return next(corpo + c for c in "0123456789" if _luhn_ok(corpo + c))

    diciotto = con_luhn("4" + "7" * 16)
    diciannove = con_luhn("4" + "1" * 17)
    a_gruppi = " ".join(diciannove[i:i + 4] for i in range(0, 19, 4))
    casi_carta += [
        (diciotto, False, "diciotto cifre attaccate che passano Luhn, come un identificativo Discord"),
        (diciannove, False, "diciannove cifre attaccate"),
        (a_gruppi, True, "Visa a diciannove cifre scritta a gruppi"),
    ]
    if not (_luhn_ok(diciotto) and _luhn_ok(diciannove)):
        print("autotest: i numeri costruiti non passano Luhn, la prova non è valida")
        return 1
    errori = 0
    for testo, atteso, nome in casi_iban:
        ottenuto = any(iban_valido(m.group(0)) for m in IBAN_CANDIDATO.finditer(testo))
        if ottenuto != atteso:
            errori += 1
            print("IBAN, %s: atteso %s, ottenuto %s" % (nome, atteso, ottenuto))
    for testo, atteso, nome in casi_carta:
        ottenuto = any(carta_valida(m.group(0)) for m in CARTA_CANDIDATA.finditer(testo))
        if ottenuto != atteso:
            errori += 1
            print("carta, %s: atteso %s, ottenuto %s" % (nome, atteso, ottenuto))
    # Il percorso completo: un file con un IBAN a gruppi e una carta, passato ad `analizza`
    # con un file di pattern minimo, deve dare un riscontro per categoria e il valore oscurato.
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "prova.md")
        with io.open(f, "w", encoding="utf-8") as fh:
            fh.write("Conto %s, carta %s.\n" % (it, casi_carta[0][0]))
        pat = {"reti_documentali_ammesse": [], "ip_ammessi": [], "prefissi_reali": [],
               "mac_ammessi_prefissi": [], "email_ammesse": [], "nomi_propri": []}
        trovati, _ = analizza(pat, [(f, "tracciato")])
        for cat in ("IBAN", "CARTA DI PAGAMENTO"):
            voci = trovati.get(cat, [])
            if len(voci) != 1 or "oscurat" not in voci[0][2]:
                errori += 1
                print("analizza, %s: atteso un riscontro oscurato, ottenuti %d" % (cat, len(voci)))
    totale = len(casi_iban) + len(casi_carta) + 2
    print("autotest: %d casi, %d errori" % (totale, errori))
    return 1 if errori else 0


def main():
    if "--autotest" in sys.argv[1:]:
        return autotest()
    ap = argparse.ArgumentParser(description="Guard-rail di anonimizzazione sui file del repository.")
    ap.add_argument("--quiet", action="store_true", help="stampa solo il riepilogo")
    ap.add_argument("--max", type=int, default=40, help="righe stampate per categoria")
    ap.add_argument("--tutti", action="store_true",
                    help="include anche i file ignorati (_notes/, output/): riscontri non bloccanti")
    ap.add_argument("--radice", default=None,
                    help="radice del repository (default: risalita dalla posizione dello script)")
    ap.add_argument("--patterns", default=PATTERNS_FILE,
                    help="percorso del file di pattern (default: %s)" % PATTERNS_FILE)
    args = ap.parse_args()

    radice = args.radice or trova_radice()
    if not radice:
        sys.stderr.write(
            "Radice del repository non trovata risalendo da %s.\n"
            "Indicarla con --radice, oppure eseguire lo strumento da dentro il repository.\n"
            % os.path.dirname(os.path.abspath(__file__)))
        return 2
    # Si entra nella radice: da qui in avanti ogni percorso relativo, compresi quelli
    # che git restituisce, è interpretabile senza sapere da dove si è partiti.
    os.chdir(radice)

    pat = carica_pattern(args.patterns)
    files = file_perimetro(args.tutti)
    trovati, saltati = analizza(pat, files)
    conteggio = collections.Counter(origine for _, origine in files)

    ordine = ["IP REALE", "MAC REALE", "SEGRETO LETTERALE", "NOME PROPRIO", "EMAIL PERSONALE",
              "TELEFONO", "IBAN", "CARTA DI PAGAMENTO", "PIVA/CF", "IMPORTO",
              "IP privato fuori schema", "IP pubblico da valutare"]

    bloccanti = 0
    da_guardare = 0
    privati = 0
    for cat in ordine:
        tutte = trovati.get(cat, [])
        if not tutte:
            continue
        # La separazione è il cuore dell'allargamento del perimetro: un valore reale in un
        # file pubblicabile è un difetto, lo stesso valore in `_notes/` è il dato per cui
        # `_notes/` esiste. Contarli insieme farebbe fallire lo script sempre.
        pubbliche = [v for v in tutte if v[4] != "ignorato"]
        riservate = [v for v in tutte if v[4] == "ignorato"]
        privati += len(riservate)
        if not pubbliche:
            continue
        if cat in BLOCCANTI:
            bloccanti += len(pubbliche)
        else:
            da_guardare += len(pubbliche)
        if args.quiet:
            continue
        etichetta = "BLOCCANTE" if cat in BLOCCANTI else "da valutare"
        print("\n" + "=" * 78)
        print("%s  [%s]  -  %d riscontri" % (cat, etichetta, len(pubbliche)))
        print("=" * 78)
        for path, ln, hit, testo, origine in pubbliche[:args.max]:
            marca = "" if origine == "tracciato" else "  <-- NON TRACCIATO, sta per essere pubblicato"
            print("  %s:%s  [%s]%s" % (path, ln, hit, marca))
            print("      %s" % testo)
        if len(pubbliche) > args.max:
            print("  ... e altri %d (usare --max)" % (len(pubbliche) - args.max))

    if args.tutti and privati and not args.quiet:
        print("\n" + "=" * 78)
        print("LAYER PRIVATO  [non bloccante]  -  %d riscontri in file ignorati da git" % privati)
        print("=" * 78)
        per_file = collections.Counter()
        for cat in ordine:
            for path, ln, hit, testo, origine in trovati.get(cat, []):
                if origine == "ignorato":
                    per_file[path] += 1
        for path, quanti in per_file.most_common(args.max):
            print("  %5d  %s" % (quanti, path))
        if len(per_file) > args.max:
            print("  ... e altri %d file (usare --max)" % (len(per_file) - args.max))
        print("\n  Questi file contengono valori reali per costruzione: sono il layer narrativo")
        print("  locale e gli output degli script, ed è la ragione per cui git li ignora. Il")
        print("  numero serve a sapere che cosa vive sul disco. Diventa un problema solo se uno")
        print("  di questi percorsi venisse tracciato, e in quel caso comparirebbe qui sopra")
        print("  come NON TRACCIATO, cioè fra i bloccanti.")

    print("\n%d file esaminati: %d tracciati, %d non tracciati, %d ignorati." % (
        len(files), conteggio.get("tracciato", 0), conteggio.get("non tracciato", 0),
        conteggio.get("ignorato", 0)))
    if saltati:
        print("%d file saltati perché oltre %d MB." % (len(saltati), LIMITE_BYTE // (1024 * 1024)))
    if not args.tutti:
        print("Layer privato (_notes/, output/) NON esaminato: usare --tutti per contarlo.")
    print("Riscontri bloccanti: %d.  Da valutare a mano: %d.%s" % (
        bloccanti, da_guardare,
        ("  Nel layer privato, non bloccanti: %d." % privati) if args.tutti else ""))
    if bloccanti:
        print("ESITO: FALLITO. Bonificare i riscontri bloccanti prima del commit.")
        return 1
    print("ESITO: pulito sulle categorie bloccanti.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
