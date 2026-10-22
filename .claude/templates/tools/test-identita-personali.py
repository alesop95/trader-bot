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


def nell_ambito(radice: Path, frammenti: list) -> bool:
    if not frammenti:
        return True
    remoti = git(radice, "remote", "-v").stdout.decode("utf-8", errors="replace")
    email = git(radice, "config", "user.email").stdout.decode("utf-8", errors="replace")
    testo = (remoti + "\n" + email).lower()
    return any(f in testo for f in frammenti)


class Cercatore:
    def __init__(self, voci: list):
        voci = [v for v in voci if not v.lower().startswith("ambito:")]
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
        if not f.is_file() or FUORI.intersection(rel.parts) or f.name == QUESTO:
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
        if Path(rel).name == QUESTO:
            continue
        testo = git(radice, "show", ":" + rel).stdout.decode("utf-8", errors="ignore")
        trovate += [(rel, n) for n, riga in enumerate(testo.splitlines(), 1) if cercatore.trova(riga)]
    for var in ("GIT_AUTHOR_IDENT", "GIT_COMMITTER_IDENT"):
        ident = git(radice, "var", var).stdout.decode("utf-8", errors="replace")
        if ident and cercatore.trova(ident.rsplit(">", 1)[0]):
            trovate.append(("identita del commit (%s)" % var.split("_")[1].lower(), 0))
    return trovate


def controlla(radice: Path, esplicito: str = "", stage: bool = False) -> int:
    f, voci = leggi_elenco(radice, esplicito, stage)
    if not voci:
        dove = "%s oppure %s" % (ELENCHI[0].as_posix(), ELENCHI[1].as_posix())
        if stage:
            print("identita personali: AVVISO, nessun elenco su questa macchina (%s): questo commit non è controllato" % dove)
            return 0
        print("identita personali: manca l'elenco (%s): senza elenco il controllo non vede niente" % dove)
        return 1
    if stage and not nell_ambito(radice, ambiti(voci)):
        print("identita personali: repository fuori dall'ambito aziendale dichiarato nell'elenco, non controllato")
        return 0
    cercatore = Cercatore(voci)
    trovate = cerca_stage(radice, cercatore) if stage else cerca_template(radice, cercatore)
    for rel, n in trovate:
        # L'identificativo non si stampa: questa uscita finisce in log e trascrizioni.
        print("   %s%s contiene un identificativo personale" % (rel, ":%d" % n if n else ""))
    if trovate:
        dove = "nel commit in preparazione" if stage else "nei file che il template propaga"
        print("identita personali: %d occorrenze %s; toglierle prima di committare" % (len(trovate), dove))
        return 1
    print("identita personali: nessuna delle %d voci %s" % (len(voci), "nel commit" if stage else "nei file che il template propaga"))
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
        caso("--stage fuori ambito non controlla un repository personale", rc == 0 and "fuori dall'ambito" in out)
        subprocess.run(["git", "-C", str(r), "remote", "add", "origin", "git@alias:Azienda.example-org/x.git"], check=True)
        caso("--stage con un remoto aziendale controlla anche con l'email personale", esegui(str(elenco), stage=True)[0] == 1)
        subprocess.run(["git", "-C", str(r), "config", "user.email", "lavoro@azienda.example"], check=True)
        elenco.unlink()
        rc, out = esegui(str(r / "manca.txt"), stage=True)
        caso("--stage senza elenco avvisa e non ferma", rc == 0 and "AVVISO" in out)
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
    p.add_argument("--impronta", default="", help="stampa la riga sha256 da aggiungere all'elenco")
    p.add_argument("--autotest", action="store_true")
    a = p.parse_args(argv)
    if a.autotest:
        return autotest()
    if a.impronta:
        print(impronta(a.impronta))
        return 0
    return controlla(Path(a.radice), a.elenco, a.stage)


if __name__ == "__main__":
    sys.exit(main())
