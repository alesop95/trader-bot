"""Impedisce che un documento di governance o un'uscita di compilazione finisca in un commit.

Esiste perche' la correzione a posteriori non e' una riparazione. Un documento che descrive
fornitori, accordi e lacune dichiarate, una volta committato, resta recuperabile da chiunque
abbia accesso al remoto anche dopo essere stato rimosso: l'unico momento in cui il problema si
risolve davvero e' prima del commit, e l'unica alternativa e' riscrivere la storia del
repository. Le regole che lo vietano sono scritte, ma una regola scritta non ferma un comando:
questo controllo si mette fra l'intenzione e il commit.

Le quattro verifiche, in ordine di quanto costa sbagliarle.

La prima e' la chiave di volta: le cartelle dichiarate private devono essere ignorate da git, e
nessun file che vi sta dentro deve risultare tracciato. Tutto il resto dell'impianto di
separazione fra codice e dati poggia su quell'assunto, e basta una riga tolta da un .gitignore
perche' decada in silenzio su ogni file insieme.

La seconda riguarda le uscite di compilazione, cioe' il sito generato da MkDocs e simili. Una
cartella di uscita e' una copia dell'intero albero dei sorgenti: se non e' ignorata, un comando
abituale la committa, e se contiene la resa di un documento privato la pubblica.

La terza cerca gli artefatti documentali fuori dal privato. Un documento di governance non entra
in un repository come prosa ma come file gia' impaginato: un DOCX, un PDF, un foglio di calcolo,
oppure una pagina HTML che porta incorporato il design system e pesa percio' centinaia di
migliaia di byte. La soglia sull'HTML e' quello che distingue una pagina di documentazione
scritta a mano da un documento prodotto, e si regola dalla configurazione.

La quarta vale dove esiste un censimento delle fonti: le uscite di compilazione devono comparire
fra le sue esclusioni, altrimenti ogni ricostruzione del sito si presenta come qualche centinaio
di documenti sorgente cambiati e il segnale di cambiamento smette di significare qualcosa.

Il controllo non nomina nessun cliente e nessun fornitore, e non legge il contenuto dei file:
guarda collocazione, estensione e dimensione. Puo' percio' vivere in un repository tracciato e
girare in un repository qualunque, che e' il motivo per cui prende la radice come argomento.

Configurazione facoltativa in `.guardia-pubblicazione.json` nella radice esaminata, con le
chiavi `private`, `uscite`, `soglia_html` e `esclusioni_censimento`; senza, valgono i valori di
difetto dichiarati sotto.

Codici di uscita: 0 nessun riscontro, 1 riscontro bloccante, 2 non calcolabile.

    python tools/guardia-pubblicazione.py
    python tools/guardia-pubblicazione.py --radice "D:/progetto"
    python tools/guardia-pubblicazione.py --autotest
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

PRIVATE = ["_notes", "knowledge", "laboratorio"]
USCITE = ["site", "graphify-out", "_site", ".cache"]
SOGLIA_HTML = 200_000
ARTEFATTI = {".docx", ".doc", ".pdf", ".xlsx", ".xls", ".pptx", ".ppt", ".odt", ".rtf"}
ESCLUSIONI_CENSIMENTO = ["_notes/.esclusi-censimento.txt"]


def git(radice, *argomenti):
    """Esegue git nella radice e torna (codice, uscita). Non solleva: il chiamante decide."""
    try:
        p = subprocess.run(["git", "-C", str(radice), *argomenti],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           stdin=subprocess.DEVNULL, timeout=30)
    except (OSError, UnicodeError, subprocess.TimeoutExpired) as e:
        return 127, str(e)
    return p.returncode, (p.stdout or "")


def configura(radice):
    """Legge la configurazione facoltativa e torna i quattro parametri, con i difetti."""
    c = {"private": PRIVATE, "uscite": USCITE, "soglia_html": SOGLIA_HTML,
         "esclusioni_censimento": ESCLUSIONI_CENSIMENTO}
    f = radice / ".guardia-pubblicazione.json"
    if f.is_file():
        try:
            c.update(json.loads(f.read_text(encoding="utf-8-sig")))
        except (OSError, ValueError) as e:
            return None, "configurazione illeggibile: %s" % e
    return c, None


def ignorata(radice, percorso):
    """Vero se git ignora quel percorso. check-ignore torna 0 se ignorato, 1 se no."""
    codice, _ = git(radice, "check-ignore", "-q", "--", percorso)
    return codice == 0


def tracciati(radice, sotto=None):
    """Elenco dei file tracciati, eventualmente sotto un percorso."""
    argomenti = ["ls-files", "-z"]
    if sotto:
        argomenti += ["--", sotto]
    codice, uscita = git(radice, *argomenti)
    if codice != 0:
        return []
    return [x for x in uscita.split("\0") if x]


def controlla(radice, conf):
    """Esegue le quattro verifiche e torna l'elenco dei riscontri, ciascuno una riga."""
    riscontri = []

    for nome in conf["private"]:
        if not (radice / nome).exists():
            continue
        if not ignorata(radice, nome + "/"):
            riscontri.append("cartella privata non ignorata da git: %s/" % nome)
        dentro = tracciati(radice, nome)
        if dentro:
            riscontri.append("file tracciati dentro la cartella privata %s/: %d, il primo e' %s"
                             % (nome, len(dentro), dentro[0]))

    for nome in conf["uscite"]:
        if not (radice / nome).exists():
            continue
        if not ignorata(radice, nome + "/"):
            riscontri.append("uscita di compilazione non ignorata da git: %s/" % nome)
        dentro = tracciati(radice, nome)
        if dentro:
            riscontri.append("file tracciati dentro l'uscita di compilazione %s/: %d, il primo e' %s"
                             % (nome, len(dentro), dentro[0]))

    privati = tuple(n.lower().rstrip("/") + "/" for n in conf["private"])
    soglia = int(conf["soglia_html"])
    for rel in tracciati(radice):
        basso = rel.lower()
        if basso.startswith(privati):
            continue
        suffisso = Path(basso).suffix
        if suffisso in ARTEFATTI:
            riscontri.append("artefatto documentale tracciato fuori dal privato: %s" % rel)
            continue
        if suffisso in (".html", ".htm"):
            f = radice / rel
            try:
                peso = f.stat().st_size
            except OSError:
                continue
            if peso >= soglia:
                riscontri.append("pagina HTML da %d byte tracciata fuori dal privato, sopra la "
                                 "soglia di %d: %s" % (peso, soglia, rel))

    for rel in conf["esclusioni_censimento"]:
        f = radice / rel
        if not f.is_file():
            continue
        try:
            testo = f.read_text(encoding="utf-8-sig")
        except OSError as e:
            riscontri.append("elenco delle esclusioni del censimento illeggibile: %s (%s)" % (rel, e))
            continue
        # Non si cerca il nome come sottostringa: `site` comparirebbe dentro `site-packages` e
        # il controllo si direbbe soddisfatto da una riga che esclude un'altra cosa. Si provano
        # invece le espressioni del file contro un percorso campione, che e' la stessa domanda
        # che il censimento si pone davvero.
        schemi = []
        for riga in testo.splitlines():
            riga = riga.strip()
            if not riga or riga.startswith("#"):
                continue
            try:
                schemi.append(re.compile(riga, re.IGNORECASE))
            except re.error:
                continue
        for nome in conf["uscite"]:
            campione = "D:/progetto/%s/index.html" % nome
            if not any(s.search(campione) for s in schemi):
                riscontri.append("l'uscita di compilazione %s/ non e' esclusa dal censimento: "
                                 "nessuno schema di %s corrisponde a %s"
                                 % (nome, rel, campione))

    return riscontri


def autotest():
    """Costruisce due repository finti, uno pulito e uno con ogni difetto, e verifica l'esito.

    Serve perche' un controllo che non viene provato scopre di non funzionare il giorno in cui
    avrebbe dovuto fermare qualcosa, e in quel giorno il suo silenzio si legge come un via libera.
    """
    base = Path(tempfile.mkdtemp(prefix="guardia-"))
    try:
        for nome, sporco in (("pulito", False), ("sporco", True)):
            r = base / nome
            (r / "_notes").mkdir(parents=True)
            (r / "docs").mkdir()
            (r / "site").mkdir()
            if git(r, "init", "-q")[0] != 0:
                print("autotest non calcolabile: git non disponibile")
                return 2
            git(r, "config", "user.email", "prova@esempio.invalid")
            git(r, "config", "user.name", "Prova")
            (r / "_notes" / "pagina.html").write_text("x" * 300_000, encoding="utf-8")
            (r / "docs" / "guida.md").write_text("# guida\n", encoding="utf-8")
            (r / "site" / "index.html").write_text("<html></html>", encoding="utf-8")
            if sporco:
                (r / ".gitignore").write_text("", encoding="utf-8")
                (r / "docs" / "registro.html").write_text("y" * 300_000, encoding="utf-8")
                (r / "docs" / "nomina.docx").write_bytes(b"PK\x03\x04")
            else:
                (r / ".gitignore").write_text("/_notes/\n/site/\n", encoding="utf-8")
            # Si popola l'indice e non si committa: ls-files legge l'indice, e un commit
            # passerebbe dagli hook della macchina, che non sono materia di questa prova.
            git(r, "add", "-A")
            conf, errore = configura(r)
            if errore:
                print("autotest non calcolabile: %s" % errore)
                return 2
            riscontri = controlla(r, conf)
            if sporco and len(riscontri) < 4:
                print("autotest fallito: il repository sporco ha prodotto %d riscontri invece di "
                      "almeno 4" % len(riscontri))
                for x in riscontri:
                    print("   " + x)
                return 1
            if not sporco and riscontri:
                print("autotest fallito: il repository pulito ha prodotto %d riscontri"
                      % len(riscontri))
                for x in riscontri:
                    print("   " + x)
                return 1
        print("autotest: il repository pulito passa, quello con i difetti viene fermato")
        return 0
    finally:
        shutil.rmtree(base, ignore_errors=True)


def main(argv=None):
    p = argparse.ArgumentParser(description="Guardia sulla pubblicazione: nessun documento di "
                                            "governance e nessuna uscita di compilazione in un commit.")
    p.add_argument("--radice", default=".", help="radice del repository da esaminare")
    p.add_argument("--autotest", action="store_true", help="prova il controllo su repository finti")
    a = p.parse_args(argv)

    if a.autotest:
        return autotest()

    radice = Path(a.radice).resolve()
    if not radice.is_dir():
        print("radice inesistente: %s" % radice)
        return 2
    if git(radice, "rev-parse", "--git-dir")[0] != 0:
        print("non e' un repository git, oppure git non e' disponibile: %s" % radice)
        return 2

    conf, errore = configura(radice)
    if errore:
        print(errore)
        return 2

    riscontri = controlla(radice, conf)
    if not riscontri:
        print("guardia-pubblicazione: nessun riscontro su %s" % radice)
        return 0
    print("guardia-pubblicazione: %d riscontri su %s" % (len(riscontri), radice))
    for x in riscontri:
        print("   " + x)
    print("Un riscontro non si aggira allargando le esclusioni: si sposta il file nel privato, "
          "oppure si ignora la cartella di uscita.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
