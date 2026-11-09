"""Cassetta comune Claude/Codex: file atomici, lettura esplicita, nessuna esecuzione.

Il congedo, e perche' e' stato aggiunto
---------------------------------------
Fino al 2026-11-03 la cassetta sapeva registrare un partecipante e non sapeva congedarlo: lo
stato valeva `registrato` per tutti, lo script di wipe di fine sessione non la toccava, e
`elenca` restituiva quindi sessioni chiuse da giorni accanto a quelle vive. Nello stesso giorno,
in un progetto istanziato, l'elenco mostrava undici partecipanti di cui quattro Codex registrati
fino a quattro giorni prima, e non mostrava la sessione Codex che stava lavorando in quel momento,
perche' non si era mai registrata. Un agente che consultava l'elenco per consegnare un lavoro ne
ricavava due conclusioni false insieme: che esistessero destinatari inesistenti, e che non
esistesse il destinatario reale.

Ne discendono le scelte di questo file. Esiste `congeda`, che marca chiusa una registrazione.
`elenca` mostra per difetto i soli partecipanti vivi, perche' il suo unico uso e' decidere a chi
scrivere e un elenco che mescola vivi e morti serve male proprio li'; `--tutti` mostra anche lo
storico. `invia` rifiuta un destinatario congedato, invece di depositare un messaggio che nessuno
leggera' mai. E `congeda --inattivi-da ORE` chiude le registrazioni piu' vecchie di quel tempo,
perche' una sessione che cade non congeda se stessa e senza questa scopa la cassetta torna a
riempirsi di morti: e' dichiaratamente un'euristica sul tempo, non una misura di vitalita'.

Resta fuori da questo file la meta' che non gli compete: la registrazione all'apertura. Finche'
una sessione non si registra, nessun elenco la vede, e questo file non puo' farci nulla.
"""

from pathlib import Path
import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import uuid


def nome(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value) or ".." in value:
        raise ValueError("nome partecipante non valido")
    return value


def pubblica(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(".tmp-" + uuid.uuid4().hex)
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with tmp.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def registra(root, identifier, agente, progetto):
    identifier = nome(identifier)
    if agente not in ("claude", "codex"):
        raise ValueError("agente non riconosciuto")
    value = {
        "nome": identifier,
        "agente": agente,
        "progetto": str(Path(progetto).resolve()),
        "registrato_il": dt.datetime.now(dt.timezone.utc).isoformat(),
        "stato": "registrato",
    }
    pubblica(Path(root) / identifier / "partecipante.json", value)
    (Path(root) / identifier / "in").mkdir(exist_ok=True)
    return value


def congeda(root, identifier=None, inattivi_da=None):
    """Marca chiusa una registrazione, per nome oppure per eta'. Ritorna le voci toccate."""
    root = Path(root)
    if identifier:
        bersagli = [root / nome(identifier) / "partecipante.json"]
    else:
        limite = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=float(inattivi_da))
        bersagli = []
        for path in sorted(root.glob("*/partecipante.json")):
            voce = json.loads(path.read_text(encoding="utf-8"))
            if voce.get("stato") != "registrato":
                continue
            quando = dt.datetime.fromisoformat(voce["registrato_il"])
            if quando < limite:
                bersagli.append(path)
    fuori = []
    for path in bersagli:
        if not path.is_file():
            raise ValueError("partecipante non registrato: " + path.parent.name)
        voce = json.loads(path.read_text(encoding="utf-8"))
        if voce.get("stato") != "chiuso":
            voce["stato"] = "chiuso"
            voce["chiuso_il"] = dt.datetime.now(dt.timezone.utc).isoformat()
            pubblica(path, voce)
        fuori.append(voce)
    return fuori


def elenco(root, tutti=False):
    """I partecipanti. Per difetto i soli vivi, perche' l'elenco serve a decidere a chi scrivere."""
    fuori = []
    for path in sorted(Path(root).glob("*/partecipante.json")):
        voce = json.loads(path.read_text(encoding="utf-8"))
        if tutti or voce.get("stato") == "registrato":
            fuori.append(voce)
    return fuori


# Indirizzi che non dicono niente di nessuno: non sono dati di qualcuno e non vanno fermati.
RETI_INNOCUE = ("127.", "0.0.0.0", "255.255.255.255", "169.254.", "192.0.2.", "198.51.100.", "203.0.113.")


def rilevatore():
    """Carica i rilevatori del guard-rail sui dati di cliente, se stanno nell'albero.

    La cassetta e' condivisa fra progetti aziendali e personali, quindi il controllo
    sul contenuto non puo' dipendere dall'attenzione di chi scrive il messaggio: sta
    qui dentro, al momento del deposito. Gli schemi sono gli stessi del guard-rail,
    perche' due elenchi di schemi divergono e quello meno usato invecchia.
    """
    qui = Path(__file__).resolve()
    candidati = [
        qui.parents[2] / "anonymization" / "tools" / "Test-Anonymization.py",
        qui.parents[4] / ".claude" / "templates" / "anonymization" / "tools" / "Test-Anonymization.py",
    ]
    for candidato in candidati:
        if candidato.is_file():
            spec = importlib.util.spec_from_file_location("anonimizzazione_posta", candidato)
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            return modulo
    return None


def contenuto_vietato(testo, modulo=None):
    """Categorie di dato reale trovate nel testo, senza i valori.

    I valori non si restituiscono e non si stampano: finirebbero nel terminale e
    nella trascrizione della sessione, cioe' proprio fuori dal perimetro che questo
    controllo esiste per difendere.
    """
    modulo = modulo or rilevatore()
    if modulo is None:
        raise ValueError(
            "manca il rilevatore degli schemi (anonymization/tools/Test-Anonymization.py): "
            "senza, il deposito non si puo' controllare e non si esegue"
        )
    trovate = {}

    def segna(categoria, quante=1):
        if quante:
            trovate[categoria] = trovate.get(categoria, 0) + quante

    segna("EMAIL", len(modulo.EMAIL.findall(testo)))
    segna("MAC", len(modulo.MAC.findall(testo)))
    segna("IMPORTO", len(modulo.MONEY.findall(testo)))
    segna("TELEFONO", len(modulo.PHONE_FALLBACK.findall(testo)))
    segna("IP", sum(1 for v in modulo.IPV4.findall(testo) if not v.startswith(RETI_INNOCUE)))
    segna("IBAN", sum(1 for v in modulo.IBAN_CANDIDATO.findall(testo) if modulo.iban_valido(v)))
    segna("CARTA", sum(1 for v in modulo.CARTA_CANDIDATA.findall(testo) if modulo.carta_valida(v)))
    return sorted(trovate.items())


def invia(root, sender, recipient, subject, body):
    sender, recipient = nome(sender), nome(recipient)
    root = Path(root)
    for identifier in (sender, recipient):
        scheda = root / identifier / "partecipante.json"
        if not scheda.is_file():
            raise ValueError("partecipante non registrato: " + identifier)
        # Un messaggio a un congedato non verra' mai letto: meglio un errore che un deposito muto.
        if json.loads(scheda.read_text(encoding="utf-8")).get("stato") == "chiuso":
            raise ValueError("partecipante congedato, non ricevera' il messaggio: " + identifier)
    if len(body.encode("utf-8")) > 131072:
        raise ValueError("messaggio oltre128KiB")
    # Il controllo sul contenuto non ha una via di scavalcamento, per costruzione: la
    # lezione da cui nasce e' che un agente che dichiara una via di fuga la usa lo stesso
    # (L-019 di un progetto istanziato, 2026-11-09). Un messaggio che deve nominare un
    # dato reale si riscrive, oppure il dato resta nel progetto che lo possiede.
    categorie = contenuto_vietato(subject + "\n" + body)
    if categorie:
        raise ValueError(
            "il messaggio contiene dati reali e non viene depositato: "
            + ", ".join("%s x%d" % (c, n) for c, n in categorie)
            + ". La cassetta e' condivisa fra progetti: si riscrive il messaggio senza quei valori."
        )
    message = {
        "id": uuid.uuid4().hex,
        "da": sender,
        "a": recipient,
        "oggetto": subject,
        "testo": body,
        "creato_il": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    path = (
        root
        / recipient
        / "in"
        / (
            dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            + "-"
            + message["id"]
            + ".json"
        )
    )
    pubblica(path, message)
    return message


def leggi(root, identifier, archivia=False):
    identifier = nome(identifier)
    inbox = Path(root) / identifier / "in"
    result = []
    for path in sorted(inbox.glob("*.json")):
        message = json.loads(path.read_text(encoding="utf-8"))
        if message.get("a") != identifier:
            raise ValueError("destinatario incoerente: " + path.name)
        result.append(message)
        if archivia:
            dest = inbox.parent / "letti" / path.name
            dest.parent.mkdir(exist_ok=True)
            path.rename(dest)
    return result


def autotest():
    """Prove su una cassetta costruita in una cartella temporanea. Non tocca nulla di reale."""
    import tempfile

    esiti = []

    def prova(nome_prova, ok, extra=""):
        esiti.append(ok)
        print("  %-66s %s" % (nome_prova, "ok" if ok else "FALLITO  " + str(extra)))

    with tempfile.TemporaryDirectory() as d:
        registra(d, "viva", "claude", d)
        registra(d, "morta", "codex", d)
        prova("elenca mostra due partecipanti vivi", len(elenco(d)) == 2, elenco(d))
        congeda(d, "morta")
        vivi = [v["nome"] for v in elenco(d)]
        prova("dopo il congedo elenca ne mostra uno solo", vivi == ["viva"], vivi)
        tutti = [(v["nome"], v["stato"]) for v in elenco(d, tutti=True)]
        prova("con --tutti si rivede lo storico con il suo stato",
              ("morta", "chiuso") in tutti and len(tutti) == 2, tutti)
        prova("il congedo scrive quando e' avvenuto",
              "chiuso_il" in [v for v in elenco(d, tutti=True) if v["nome"] == "morta"][0])
        try:
            invia(d, "viva", "morta", "x", "y")
            prova("inviare a un congedato fallisce", False)
        except ValueError as e:
            prova("inviare a un congedato fallisce dicendo perche'", "congedato" in str(e), str(e))
        invia(d, "viva", "viva", "x", "y")
        prova("inviare a un vivo continua a funzionare", len(leggi(d, "viva")) == 1)
        congeda(d, "morta")
        prova("congedare due volte non e' un errore", True)
        try:
            congeda(d, "inesistente")
            prova("congedare un nome mai registrato fallisce", False)
        except ValueError:
            prova("congedare un nome mai registrato fallisce", True)
        # Il difetto del 2026-11-03 viveva fra argparse e la funzione, non dentro la funzione:
        # si riproduce solo chiamando la riga di comando con la variabile d'ambiente valorizzata.
        import subprocess
        import sys as _sys
        registra(d, "ambiente", "claude", d)
        amb = dict(os.environ, PROJECT_AGENT_MAILBOX_ID="ambiente")
        subprocess.run([_sys.executable, __file__, "--root", d, "congeda", "--inattivi-da", "99"],
                       capture_output=True, env=amb)
        stato_amb = [v for v in elenco(d, tutti=True) if v["nome"] == "ambiente"][0]["stato"]
        prova("la scopa per eta' non congeda la sessione corrente per via del default",
              stato_amb == "registrato", stato_amb)
        congeda(d, "ambiente")
        n = len(congeda(d, None, 0))
        prova("la scopa per eta' chiude i vivi piu' vecchi del limite", n == 1, n)
        prova("dopo la scopa non resta nessun vivo", elenco(d) == [], elenco(d))
        # Il controllo sul contenuto al deposito: la cassetta e' condivisa fra progetti
        # aziendali e personali, e un messaggio con dati reali la fa uscire dal perimetro.
        registra(d, "mittente", "claude", d)
        rotti = [
            ("un IBAN valido", "IBAN", "il conto e' GB82 WEST 12345698765432"),
            ("un indirizzo di posta", "EMAIL", "scrivi a prova@example.invalid"),
            ("un indirizzo di rete della macchina", "IP", "la macchina risponde su 192.168.20.25"),
            ("un importo in euro", "IMPORTO", "la fattura e' di 12,34 euro"),
        ]
        for descrizione, categoria, testo in rotti:
            try:
                invia(d, "mittente", "mittente", "oggetto", testo)
                prova("il deposito rifiuta " + descrizione, False)
            except ValueError as e:
                prova(
                    "il deposito rifiuta " + descrizione + " nominando la categoria",
                    categoria in str(e) and testo.split()[-1] not in str(e),
                    str(e),
                )
        prima = len(leggi(d, "mittente"))
        invia(d, "mittente", "mittente", "allineamento", "la passata ha scritto 7 file su 45 progetti, zero conflitti")
        prova("un messaggio tecnico senza dati reali passa", len(leggi(d, "mittente")) == prima + 1)
        prova(
            "un indirizzo di loopback non e' un dato di nessuno",
            contenuto_vietato("il servizio ascolta su 127.0.0.1 porta 8000") == [],
            contenuto_vietato("il servizio ascolta su 127.0.0.1 porta 8000"),
        )

    print("\n%d prove, %d fallite." % (len(esiti), esiti.count(False)))
    return 0 if all(esiti) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=os.environ.get("PROJECT_AGENT_MAILBOX_ROOT"))
    sub = parser.add_subparsers(dest="azione", required=True)
    reg = sub.add_parser("registra")
    reg.add_argument("--nome", required=True)
    reg.add_argument("--agente", choices=["claude", "codex"], required=True)
    reg.add_argument("--progetto", required=True)
    send = sub.add_parser("invia")
    send.add_argument("--da", dest="sender", required=True)
    send.add_argument("--a", dest="recipient", required=True)
    send.add_argument("--oggetto", required=True)
    group = send.add_mutually_exclusive_group(required=True)
    group.add_argument("--testo")
    group.add_argument("--testo-file")
    read = sub.add_parser("leggi")
    read.add_argument("--nome", default=os.environ.get("PROJECT_AGENT_MAILBOX_ID"))
    read.add_argument("--archivia", action="store_true")
    bye = sub.add_parser("congeda")
    gruppo_bye = bye.add_mutually_exclusive_group(required=True)
    gruppo_bye.add_argument("--nome", default=os.environ.get("PROJECT_AGENT_MAILBOX_ID"))
    gruppo_bye.add_argument("--inattivi-da", type=float, metavar="ORE")
    lst = sub.add_parser("elenca")
    lst.add_argument("--tutti", action="store_true", help="mostra anche i congedati")
    sub.add_parser("autotest")
    args = parser.parse_args()
    if not args.root:
        parser.error("specificare --root oppure PROJECT_AGENT_MAILBOX_ROOT")
    try:
        if args.azione == "registra":
            result = registra(args.root, args.nome, args.agente, args.progetto)
        elif args.azione == "invia":
            body = (
                Path(args.testo_file).read_text(encoding="utf-8")
                if args.testo_file
                else args.testo
            )
            result = invia(args.root, args.sender, args.recipient, args.oggetto, body)
        elif args.azione == "leggi":
            if not args.nome:
                parser.error("specificare --nome oppure PROJECT_AGENT_MAILBOX_ID")
            result = leggi(args.root, args.nome, args.archivia)
        elif args.azione == "congeda":
            # `--nome` ha un default dall'ambiente, quindi il gruppo mutuamente esclusivo non
            # impedisce che sia valorizzato quando si chiede la scopa per eta'. Senza questa riga
            # `congeda --inattivi-da 24` congedava la sessione corrente e lasciava stare le vecchie:
            # misurato sulla cassetta reale il 2026-11-03, prima che il difetto raggiungesse i
            # launcher. La scopa vince sempre sul default, mai su un nome scritto a mano.
            result = congeda(args.root, None if args.inattivi_da is not None else args.nome,
                             args.inattivi_da)
        elif args.azione == "autotest":
            return autotest()
        else:
            result = elenco(args.root, args.tutti)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print("posta: " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
