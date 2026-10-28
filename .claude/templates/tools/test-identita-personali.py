#!/usr/bin/env python3
"""Nessun identificativo personale nei file che il template propaga, né in un commit di un progetto.

Perché esiste. Fino al commit 74b6f6b il template aveva una regola versionata sulle identità git
di questa macchina che conteneva, accanto al profilo di lavoro, il profilo personale: utente,
email e alias SSH. L'inizializzazione e l'allineamento copiano le regole in ogni progetto, quindi
quel profilo è finito, committato e spinto, nei repository aziendali; il 2026-10-21 lo si è
trovato nella storia di dieci di loro, e toglierlo ha richiesto di riscriverne la storia e di
chiedere a GitHub di eliminare i riferimenti delle pull request. Lo stesso giorno si è visto che
il dato poteva entrare anche senza il template, scritto a mano nella documentazione di un
progetto. Le barriere quindi sono due.

Nel template, senza opzioni, lo strumento cerca ogni voce dell'elenco nei file tracciati sotto
`.claude/`, cioè in ciò che l'allineamento propaga; `chiudi` lo lancia e ferma il commit del
template, `allinea-tutti.ps1` lo lancia e non parte. In qualunque progetto, con `--stage`, cerca
le voci nei file in stage, letti dall'indice, e nell'identità con cui il commit verrà firmato:
`chiudi` lo lancia fra lo stage e il commit, e il passo `.githooks/pre-commit.d/identita-personali`
lo lancia nei commit manuali. In entrambi i modi esce con 1 se trova qualcosa.

L'elenco non è mai versionato, perché è esso stesso un dato personale. Si cerca, nell'ordine, in
`_notes/allineamento/identita-personali.txt` del template e in `~/.config/identita-personali.txt`
della macchina; una voce per riga, # per i commenti. Una voce può essere in chiaro, e allora si
cerca come sottostringa senza distinguere maiuscole, oppure nella forma `sha256:<impronta>` del
testo in minuscolo, e allora si confronta con l'impronta di ogni parola e di ogni indirizzo email
della riga: è la forma da usare sulle macchine aziendali, dove il dato in chiaro non deve stare.
`--impronta <testo>` stampa la riga da aggiungere. Nel template un elenco mancante ferma, perché un
controllo senza elenco direbbe sempre pulito; in un progetto avvisa ad alta voce e non ferma, così
una macchina senza elenco non blocca ogni commit, ma lo dice a ogni commit.

    python .claude/templates/tools/test-identita-personali.py
    python .claude/templates/tools/test-identita-personali.py --stage
    python .claude/templates/tools/test-identita-personali.py --tracciati
    python .claude/templates/tools/test-identita-personali.py --impronta "testo"
    python .claude/templates/tools/test-identita-personali.py --autotest
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PERIMETRO = [".claude"]
FUORI = {"_notes", "__pycache__", ".git", "node_modules"}
ELENCHI = [Path("_notes") / "allineamento" / "identita-personali.txt", Path.home() / ".config" / "identita-personali.txt"]
QUESTO = "test-identita-personali.py"
LIMITE_BYTE = 2 * 1024 * 1024
AMMESSE = Path(".claude") / "templates" / "tools" / "identita-forme-ammesse.txt"
PERCORSO_TEMPLATE = Path.home() / ".config" / "template-claude-path.txt"
FORME = [
    ("indirizzo", re.compile(r"[A-Za-z0-9._%+@-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I)),
    ("chiave", re.compile(r"\bid_(?:rsa|dsa|ecdsa|ed25519)[A-Za-z0-9_.-]*", re.I)),
]
NON_CONTROLLATO = 2
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PAROLA = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*")


def impronta(testo: str) -> str:
    return "sha256:" + hashlib.sha256(testo.strip().lower().encode("utf-8")).hexdigest()


def leggi_elenco(radice: Path, esplicito: str = "", stage: bool = False) -> tuple:
    # Il controllo dei commit usa l'elenco della macchina, con il suo ambito: quello del template
    # serve a ciò che il template propaga, e non dice quali repository della macchina sono aziendali.
    candidati = [Path(esplicito)] if esplicito else ([ELENCHI[1]] if stage else [radice / ELENCHI[0], ELENCHI[1]])
    for f in candidati:
        if f.is_file():
            voci = [r.strip() for r in f.read_text(encoding="utf-8").splitlines() if r.strip() and not r.strip().startswith("#")]
            return f, voci
    return None, []


def ambiti(voci: list) -> list:
    """Le righe `ambito: x` dell'elenco: frammenti di remoto o di email che rendono aziendale un
    repository. Su una macchina che ospita anche progetti personali il controllo dei commit vale
    solo dove uno di essi compare; senza righe di ambito vale ovunque."""
    return [v.split(":", 1)[1].strip().lower() for v in voci if v.lower().startswith("ambito:") and v.split(":", 1)[1].strip()]


def voci_di_lavoro(voci: list) -> list:
    """Le righe `lavoro: x` dell'elenco: gli identificativi del profilo di lavoro. Si cercano nel
    verso opposto a quelli personali, cioe' nei repository FUORI dall'ambito aziendale, perche' in
    un progetto personale e' l'identita' di lavoro a non doverci stare. Senza queste righe il
    controllo resta quello di prima, a senso unico."""
    return [v.split(":", 1)[1].strip() for v in voci if v.lower().startswith("lavoro:") and v.split(":", 1)[1].strip()]


def nell_ambito(radice: Path, frammenti: list) -> bool:
    if not frammenti:
        return True
    remoti = git(radice, "remote", "-v").stdout.decode("utf-8", errors="replace")
    email = git(radice, "config", "user.email").stdout.decode("utf-8", errors="replace")
    testo = (remoti + "\n" + email).lower()
    return any(f in testo for f in frammenti)


class Cercatore:
    def __init__(self, voci: list):
        voci = [v for v in voci if not v.lower().startswith(("ambito:", "lavoro:"))]
        self.chiare = [v.lower() for v in voci if not v.startswith("sha256:")]
        self.impronte = {v.lower() for v in voci if v.startswith("sha256:")}

    def trova(self, riga: str) -> bool:
        bassa = riga.lower()
        if any(v in bassa for v in self.chiare):
            return True
        if not self.impronte:
            return False
        candidati = set(EMAIL.findall(bassa))
        for parola in PAROLA.findall(bassa):
            candidati.add(parola)
            candidati.update(p for p in re.split(r"[._+-]", parola) if p)
        return any(impronta(c) in self.impronte for c in candidati)


def git(radice: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(radice), *args], capture_output=True)


def file_del_perimetro(radice: Path) -> list:
    """I file tracciati da git, perché l'allineamento propaga ciò che è committato e non i file
    locali ignorati, come `settings.local.json`; fuori da un repository, tutti i file."""
    r = git(radice, "ls-files", "-z", *PERIMETRO)
    if r.returncode == 0:
        return [radice / p for p in r.stdout.decode("utf-8", errors="replace").split("\0") if p]
    return [f for base in PERIMETRO for f in sorted((radice / base).rglob("*"))]


def cerca_template(radice: Path, cercatore: Cercatore) -> list:
    trovate = []
    for f in file_del_perimetro(radice):
        rel = f.relative_to(radice)
        if not f.is_file() or FUORI.intersection(rel.parts) or f.name in (QUESTO, AMMESSE.name):
            continue
        try:
            testo = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        trovate += [(rel.as_posix(), n) for n, riga in enumerate(testo.splitlines(), 1) if cercatore.trova(riga)]
    return trovate


def cerca_stage(radice: Path, cercatore: Cercatore) -> list:
    """I file in stage letti dall'indice, cioè ciò che il commit conterrà davvero, più l'identità
    con cui verrà firmato: autore e committer."""
    trovate = []
    nomi = git(radice, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR").stdout.decode("utf-8", errors="replace")
    for rel in [p for p in nomi.split("\0") if p]:
        if Path(rel).name in (QUESTO, AMMESSE.name):
            continue
        testo = git(radice, "show", ":" + rel).stdout.decode("utf-8", errors="ignore")
        trovate += [(rel, n) for n, riga in enumerate(testo.splitlines(), 1) if cercatore.trova(riga)]
    for var in ("GIT_AUTHOR_IDENT", "GIT_COMMITTER_IDENT"):
        ident = git(radice, "var", var).stdout.decode("utf-8", errors="replace")
        if ident and cercatore.trova(ident.rsplit(">", 1)[0]):
            trovate.append(("identita del commit (%s)" % var.split("_")[1].lower(), 0))
    return trovate


def file_tracciati(radice: Path) -> list:
    """Tutti i file tracciati del repository, non il solo perimetro del template: serve a
    ritrovare cio' che e' entrato prima che il controllo esistesse, e che ne' `--stage` ne' il
    controllo del template rileggono mai piu'."""
    r = git(radice, "ls-files", "-z")
    if r.returncode != 0:
        return []
    return [radice / p for p in r.stdout.decode("utf-8", errors="replace").split("\0") if p]


def cerca_tracciati(radice: Path, cercatore: Cercatore) -> list:
    """Come il controllo del template ma su tutti i file tracciati, saltando i binari e i file
    molto grandi, che non contengono identita' scritte a mano e costerebbero l'intera scansione."""
    trovate = []
    for f in file_tracciati(radice):
        rel = f.relative_to(radice)
        if not f.is_file() or FUORI.intersection(rel.parts) or f.name in (QUESTO, AMMESSE.name):
            continue
        try:
            if f.stat().st_size > LIMITE_BYTE:
                continue
            grezzo = f.read_bytes()
        except OSError:
            continue
        if b"\0" in grezzo[:8192]:
            continue
        testo = grezzo.decode("utf-8", errors="ignore")
        trovate += [(rel.as_posix(), n) for n, riga in enumerate(testo.splitlines(), 1) if cercatore.trova(riga)]
    return trovate


def forme_ammesse(radice: Path) -> set:
    f = radice / AMMESSE
    if not f.is_file():
        return set()
    return {r.strip().lower() for r in f.read_text(encoding="utf-8").splitlines() if r.strip() and not r.strip().startswith("#")}


def cerca_forme(radice: Path) -> list:
    """Nel perimetro che il template propaga non entra NESSUN indirizzo e NESSUN nome di file di
    chiave che non sia un esempio dichiarato. E' il controllo che non dipende da un elenco di
    identita' note: riconosce la forma del dato invece dei colpevoli gia' schedati, quindi ferma
    anche l'indirizzo di un collega, o uno nuovo che nessuno ha pensato di censire."""
    ammesse = forme_ammesse(radice)
    trovate = []
    for f in file_del_perimetro(radice):
        rel = f.relative_to(radice)
        if not f.is_file() or FUORI.intersection(rel.parts) or f.name in (QUESTO, AMMESSE.name):
            continue
        try:
            testo = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for n, riga in enumerate(testo.splitlines(), 1):
            for nome, forma in FORME:
                for v in forma.findall(riga):
                    if v.lower() not in ammesse:
                        trovate.append((rel.as_posix(), n, nome))
    return trovate


def strumento_disallineato(radice: Path) -> str:
    """Il template e' la sola copia che conta: se quella del progetto e' diversa, il controllo che
    gira non e' quello che si crede di avere. Il percorso del template sta in un file della
    macchina, non qui dentro, perche' un percorso concreto in un file versionato e' il difetto che
    questo strumento esiste per impedire."""
    try:
        if not PERCORSO_TEMPLATE.is_file():
            return ""
        tpl = Path(PERCORSO_TEMPLATE.read_text(encoding="utf-8").strip())
        mio = Path(__file__).resolve()
        suo = (tpl / ".claude" / "templates" / "tools" / QUESTO).resolve()
        if suo == mio or not suo.is_file():
            return ""
        suo_bytes = suo.read_bytes().replace(b"\r\n", b"\n")
        mio_bytes = mio.read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(suo_bytes).digest() != hashlib.sha256(mio_bytes).digest():
            return "AVVISO: questa copia del controllo e' diversa da quella del template; allineare il progetto"
    except OSError:
        pass
    return ""


def controlla(radice: Path, esplicito: str = "", stage: bool = False, tracciati: bool = False) -> int:
    avviso = strumento_disallineato(radice)
    if avviso:
        print(avviso)
    forme = [] if (stage or tracciati) else cerca_forme(radice)
    for rel, n, nome in forme:
        print("   %s:%d ha la forma di un %s e non e' fra gli esempi ammessi" % (rel, n, nome))
    f, voci = leggi_elenco(radice, esplicito, stage or tracciati)
    if not voci:
        dove = "%s oppure %s" % (ELENCHI[0].as_posix(), ELENCHI[1].as_posix())
        if stage:
            print("identita personali: nessun elenco su questa macchina (%s): il commit NON e' controllato, installare l'elenco" % dove)
            return NON_CONTROLLATO
        print("identita personali: manca l'elenco (%s): senza elenco il controllo non vede niente" % dove)
        return 1
    lavoro = voci_di_lavoro(voci)
    dentro = nell_ambito(radice, ambiti(voci))
    verso = ""
    if stage or tracciati:
        # In un repository aziendale non deve comparire l'identita' personale; in uno personale
        # non deve comparire quella di lavoro. Il verso lo decide l'ambito, non chi lancia.
        if dentro:
            cercatore = Cercatore(voci)
        elif lavoro:
            cercatore = Cercatore(lavoro)
            verso = " di lavoro"
        else:
            print("identita personali: fuori dall'ambito aziendale e nessuna voce `lavoro:` nell'elenco: NON controllato")
            return NON_CONTROLLATO
    else:
        # Cio' che il template propaga finisce in entrambi i tipi di repository: nessuna delle due.
        cercatore = Cercatore(voci + lavoro)
    if tracciati:
        trovate = cerca_tracciati(radice, cercatore)
    elif stage:
        trovate = cerca_stage(radice, cercatore)
    else:
        trovate = cerca_template(radice, cercatore)
    for rel, n in trovate:
        # L'identificativo non si stampa: questa uscita finisce in log e trascrizioni.
        print("   %s%s contiene un identificativo%s" % (rel, ":%d" % n if n else "", verso or " personale"))
    if forme:
        print("identita personali: %d stringhe con la forma di un'identita' nei file che il template propaga" % len(forme))
    if trovate:
        dove = "fra i file tracciati" if tracciati else ("nel commit in preparazione" if stage else "nei file che il template propaga")
        print("identita personali: %d occorrenze %s; toglierle prima di committare" % (len(trovate), dove))
        return 1
    if forme:
        return 1
    if forme:
        return 1
    print("identita personali: nessuna delle %d voci %s" % (len(voci), "fra i file tracciati" if tracciati else ("nel commit" if stage else "nei file che il template propaga")))
    return 0


def autotest() -> int:
    import contextlib
    import io

    casi = rossi = 0

    def caso(nome, ok):
        nonlocal casi, rossi
        casi += 1
        rossi += 0 if ok else 1
        print(("ok   " if ok else "ROSSO ") + nome)

    with tempfile.TemporaryDirectory() as d:
        r = Path(d)

        def esegui(*a, **k):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = controlla(r, *a, **k)
            return rc, buf.getvalue()

        (r / ".claude" / "rules").mkdir(parents=True)
        (r / AMMESSE.parent).mkdir(parents=True, exist_ok=True)
        (r / AMMESSE).write_text("lavoro@azienda.example@N@persona.privata@posta.example@N@utentepriv@posta.example@N@".replace("@N@", chr(10)), encoding="utf-8")
        (r / "_notes" / "allineamento").mkdir(parents=True)
        (r / ".claude" / "rules" / "identita.md").write_text("Profilo di lavoro: lavoro@azienda.example\n", encoding="utf-8")
        (r / "README.md").write_text("persona.privata@posta.example fuori dal perimetro\n", encoding="utf-8")
        rc, out = esegui(str(r / "manca.txt"))
        caso("senza elenco il controllo del template fallisce invece di dire pulito", rc == 1 and "manca l'elenco" in out)
        elenco = r / "_notes" / "allineamento" / "identita-personali.txt"
        elenco.write_text("# commento\nPersona.Privata@posta.example\nutentepriv\n", encoding="utf-8")
        rc, out = esegui()
        caso("un perimetro pulito passa, e un file fuori perimetro non conta", rc == 0 and "nessuna delle 2 voci" in out)
        (r / ".claude" / "rules" / "identita.md").write_text("Profilo personale: utente UtentePriv, persona.privata@posta.example\n", encoding="utf-8")
        rc, out = esegui()
        caso("un identificativo in una regola ferma, senza distinguere maiuscole", rc == 1 and "identita.md:1" in out)
        caso("l'identificativo non si stampa", "persona.privata" not in out.lower() and "utentepriv" not in out.lower())
        (r / ".claude" / "rules" / "identita.md").write_text("pulito\n", encoding="utf-8")
        (r / ".claude" / "_notes").mkdir()
        (r / ".claude" / "_notes" / "x.md").write_text("utentepriv\n", encoding="utf-8")
        caso("le note locali sotto .claude non contano", esegui()[0] == 0)

        # forme: cio' che ha l'aspetto di un'identita' si ferma anche se non e' in nessun elenco
        (r / ".claude" / "rules" / "identita.md").write_text("scrivere a mario.rossi@dittavera.it\n", encoding="utf-8")
        rc, out = esegui()
        caso("un indirizzo mai censito si ferma lo stesso, per la sua forma", rc == 1 and "forma di un indirizzo" in out)
        caso("il valore non si stampa nemmeno qui", "mario.rossi" not in out)
        ammesse = r / AMMESSE
        ammesse.write_text(ammesse.read_text(encoding="utf-8") + "mario.rossi@dittavera.it\n", encoding="utf-8")
        caso("lo stesso indirizzo dichiarato come esempio ammesso passa", esegui()[0] == 0)
        (r / ".claude" / "rules" / "identita.md").write_text("chiave id_ed25519_qualcosa\n", encoding="utf-8")
        rc, out = esegui()
        caso("un nome di file di chiave si ferma per la sua forma", rc == 1 and "forma di un chiave" in out)
        (r / ".claude" / "rules" / "identita.md").write_text("pulito\n", encoding="utf-8")
        caso("tolte le forme, il perimetro torna verde", esegui()[0] == 0)

        # impronte
        elenco.write_text("%s\n%s\n" % (impronta("persona.privata@posta.example"), impronta("utentepriv")), encoding="utf-8")
        (r / ".claude" / "rules" / "identita.md").write_text("remoto git@alias:UtentePriv/progetto.git\n", encoding="utf-8")
        caso("un'impronta riconosce la parola dentro un indirizzo, senza il testo in chiaro", esegui()[0] == 1)
        (r / ".claude" / "rules" / "identita.md").write_text("scrivere a Persona.Privata@posta.example\n", encoding="utf-8")
        caso("un'impronta riconosce un indirizzo email", esegui()[0] == 1)
        (r / ".claude" / "rules" / "identita.md").write_text("utentepriva e altroutentepriv sono altre parole\n", encoding="utf-8")
        caso("un'impronta non scatta su parole che soltanto la contengono", esegui()[0] == 0)

        # --stage in un repository vero
        subprocess.run(["git", "init", "-q", str(r)], check=True)
        subprocess.run(["git", "-C", str(r), "config", "user.name", "Lavoro"], check=True)
        subprocess.run(["git", "-C", str(r), "config", "user.email", "lavoro@azienda.example"], check=True)
        (r / "doc.md").write_text("nessun dato\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(r), "add", "doc.md"], check=True)
        rc, out = esegui(str(elenco), stage=True)
        caso("--stage passa un commit pulito", rc == 0)
        (r / "doc.md").write_text("contatto: persona.privata@posta.example\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(r), "add", "doc.md"], check=True)
        rc, out = esegui(str(elenco), stage=True)
        caso("--stage ferma un file in stage con il dato, letto dall'indice", rc == 1 and "doc.md:1" in out)
        (r / "doc.md").write_text("nessun dato\n", encoding="utf-8")
        caso("--stage guarda l'indice e non l'albero di lavoro", esegui(str(elenco), stage=True)[0] == 1)
        subprocess.run(["git", "-C", str(r), "add", "doc.md"], check=True)
        subprocess.run(["git", "-C", str(r), "config", "user.email", "Persona.Privata@posta.example"], check=True)
        rc, out = esegui(str(elenco), stage=True)
        caso("--stage ferma un commit firmato con l'identità personale", rc == 1 and "identita del commit" in out)
        subprocess.run(["git", "-C", str(r), "config", "user.email", "lavoro@azienda.example"], check=True)
        # ambito: un repository personale non si controlla, uno aziendale sì
        elenco.write_text("ambito: azienda.example\n%s\n" % impronta("persona.privata@posta.example"), encoding="utf-8")
        (r / "doc.md").write_text("contatto: persona.privata@posta.example\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(r), "add", "doc.md"], check=True)
        caso("--stage nell'ambito aziendale (email di lavoro) ferma", esegui(str(elenco), stage=True)[0] == 1)
        subprocess.run(["git", "-C", str(r), "config", "user.email", "io@privato.example"], check=True)
        rc, out = esegui(str(elenco), stage=True)
        caso("--stage fuori ambito senza voci di lavoro NON e' verde: esce 2", rc == NON_CONTROLLATO and "NON controllato" in out)
        subprocess.run(["git", "-C", str(r), "remote", "add", "origin", "git@alias:Azienda.example-org/x.git"], check=True)
        caso("--stage con un remoto aziendale controlla anche con l'email personale", esegui(str(elenco), stage=True)[0] == 1)
        subprocess.run(["git", "-C", str(r), "config", "user.email", "lavoro@azienda.example"], check=True)
        elenco.write_text("%s\n" % impronta("persona.privata@posta.example"), encoding="utf-8")
        (r / "doc.md").write_text("nessun dato\n", encoding="utf-8")
        (r / "vecchio.md").write_text("scritto prima del controllo: persona.privata@posta.example\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(r), "add", "doc.md", "vecchio.md"], check=True)
        subprocess.run(["git", "-C", str(r), "commit", "-q", "-m", "x", "--no-verify"], check=True)
        caso("--stage non vede un file gia' committato: non c'e' niente in stage", esegui(str(elenco), stage=True)[0] == 0)
        caso("il controllo del template non lo vede: e' fuori dal perimetro .claude", esegui(str(elenco))[0] == 0)
        rc, out = esegui(str(elenco), tracciati=True)
        caso("--tracciati lo trova, ed e' l'unico modo di ritrovarlo", rc == 1 and "vecchio.md:1" in out)
        caso("--tracciati non stampa l'identificativo", "persona.privata" not in out.lower())
        (r / "vecchio.md").write_text("ripulito\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(r), "add", "vecchio.md"], check=True)
        subprocess.run(["git", "-C", str(r), "commit", "-q", "-m", "y", "--no-verify"], check=True)
        caso("--tracciati passa quando il file e' stato ripulito", esegui(str(elenco), tracciati=True)[0] == 0)
        # verso opposto: in un repository personale non deve comparire l'identita' di lavoro
        subprocess.run(["git", "-C", str(r), "remote", "set-url", "origin", "git@alias:utentepriv/x.git"], check=True)
        subprocess.run(["git", "-C", str(r), "config", "user.email", "io@privato.example"], check=True)
        elenco.write_text("ambito: azienda.example\n%s\nlavoro: %s\n" % (impronta("persona.privata@posta.example"), impronta("lavoro@azienda.example")), encoding="utf-8")
        (r / "vecchio.md").write_text("configurato con lavoro@azienda.example\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(r), "add", "vecchio.md"], check=True)
        subprocess.run(["git", "-C", str(r), "commit", "-q", "-m", "z", "--no-verify"], check=True)
        rc, out = esegui(str(elenco), tracciati=True)
        caso("fuori ambito, --tracciati trova l'identita' di lavoro", rc == 1 and "vecchio.md:1" in out and "di lavoro" in out)
        (r / "vecchio.md").write_text("persona.privata@posta.example, che qui e' legittima\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(r), "add", "vecchio.md"], check=True)
        subprocess.run(["git", "-C", str(r), "commit", "-q", "-m", "w", "--no-verify"], check=True)
        caso("fuori ambito, l'identita' personale non e' un reperto", esegui(str(elenco), tracciati=True)[0] == 0)
        (r / ".claude" / "rules" / "identita.md").write_text("lavoro@azienda.example\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(r), "add", ".claude/rules/identita.md"], check=True)
        caso("il template rifiuta entrambe le identita', non una sola", esegui(str(elenco))[0] == 1)
        (r / ".claude" / "rules" / "identita.md").write_text("pulito\n", encoding="utf-8")
        elenco.write_text("ambito: azienda.example\n%s\n" % impronta("persona.privata@posta.example"), encoding="utf-8")
        rc, out = esegui(str(elenco), tracciati=True)
        caso("--tracciati fuori ambito senza voci di lavoro esce 2, non 0", rc == NON_CONTROLLATO and "NON controllato" in out)
        elenco.unlink()
        rc, out = esegui(str(r / "manca.txt"), stage=True)
        caso("--stage senza elenco ferma invece di avvisare", rc == NON_CONTROLLATO and "NON e' controllato" in out)
    caso("l'impronta è quella del testo in minuscolo", impronta(" Ab@C.d ") == impronta("ab@c.d"))
    print("\n%d casi superati su %d" % (casi - rossi, casi))
    return 1 if rossi else 0


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Nessun identificativo personale nei file propagati o in un commit.")
    p.add_argument("--radice", default=".")
    p.add_argument("--elenco", default="")
    p.add_argument("--stage", action="store_true", help="controlla i file in stage e l'identità del commit")
    p.add_argument("--tracciati", action="store_true", help="controlla tutti i file tracciati del repository, non solo il perimetro del template")
    p.add_argument("--impronta", default="", help="stampa la riga sha256 da aggiungere all'elenco")
    p.add_argument("--autotest", action="store_true")
    a = p.parse_args(argv)
    if a.autotest:
        return autotest()
    if a.impronta:
        print(impronta(a.impronta))
        return 0
    return controlla(Path(a.radice), a.elenco, a.stage, a.tracciati)


if __name__ == "__main__":
    sys.exit(main())
