#!/usr/bin/env python3
"""Le conversioni da testo a numero o a data che in PowerShell dipendono dalla cultura di sistema.

Perché esiste. Il 2026-10-20 un progetto istanziato leggeva la durata di un video dall'uscita
di ffprobe con `[double]::Parse("300.012000")`. In cultura italiana il punto separa le
migliaia, quindi il valore letto era trecento milioni: la conversione riesce, nessun errore,
e il numero sbagliato arriva fino a un rapporto assurdo a valle. Il difetto non si vede
leggendo il codice né provando su una macchina in inglese, quindi non lo prende nessuna
prova scritta altrove; lo prende soltanto una regola sulla forma della chiamata.

La regola: `[double]::Parse`, `TryParse` e `[Convert]::ToDouble`, e gli stessi per `decimal`,
`single`, `float` e `datetime`, si chiamano con un argomento di cultura, per esempio
`[Globalization.CultureInfo]::InvariantCulture` o una variabile che la contiene. Lo
strumento conta gli argomenti di primo livello della chiamata e accetta la riga se, oltre al
testo da convertire, c'è un argomento che non è un `[ref]` né uno stile (`NumberStyles`,
`DateTimeStyles`): quello è il fornitore di formato. I tipi interi restano fuori, perché con
lo stile predefinito un separatore li fa fallire invece di sbagliare. Il cast `[double]"1.5"`
e l'operatore `-as` sono già invarianti in PowerShell e non si segnalano. Una riga che deve
restare così si marca con `# cultura-ok` e il motivo.

    python .claude/templates/tools/lint-cultura.py [radice]
    python .claude/templates/tools/lint-cultura.py --autotest

Nel template un riscontro ferma `chiudi`; in un progetto istanziato avvisa e basta, salvo
`--rigoroso`, perché il controllo arriva con l'allineamento su codice che non l'ha mai visto.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

TIPI = r"(?:double|decimal|single|float|datetime)"
CHIAMATA = re.compile(
    r"\[(?:System\.)?" + TIPI + r"\]::(?:Try)?Parse\s*\(|\[(?:System\.)?Convert\]::To(?:Double|Decimal|Single|DateTime)\s*\(",
    re.I)
NON_CULTURA = re.compile(r"^\s*(?:\[ref\]|\[(?:System\.)?Globalization\.(?:NumberStyles|DateTimeStyles)\]|'?(?:Any|Float|Number|AllowDecimalPoint|None)'?\s*$)", re.I)
MARCA = "# cultura-ok"
FUORI = {"fixtures", "node_modules", ".git"}


def argomenti(riga: str, inizio: int) -> list:
    """Gli argomenti di primo livello della chiamata la cui parentesi aperta sta in `inizio`."""
    prof, arg, args, apice = 0, "", [], None
    for c in riga[inizio:]:
        if apice:
            arg += c
            if c == apice:
                apice = None
            continue
        if c in "'\"":
            apice = c
            arg += c
        elif c in "([{":
            prof += 1
            if prof > 1:
                arg += c
        elif c in ")]}":
            prof -= 1
            if prof == 0:
                args.append(arg)
                return args
            arg += c
        elif c == "," and prof == 1:
            args.append(arg)
            arg = ""
        elif prof >= 1:
            arg += c
    return args + [arg]


def riscontri_riga(riga: str) -> int:
    if MARCA in riga:
        return 0
    n = 0
    for m in CHIAMATA.finditer(riga):
        args = argomenti(riga, m.end() - 1)
        if not any(a.strip() and not NON_CULTURA.match(a) for a in args[1:]):
            n += 1
    return n


def nel_template(radice: Path) -> bool:
    readme = radice / "README.md"
    return (radice / ".claude" / "PROMPT-nuovo-progetto.md").is_file() and readme.is_file() and \
        "<!-- sync-readme:packages:start -->" in readme.read_text(encoding="utf-8", errors="replace")


def file_powershell(radice: Path) -> list:
    r = subprocess.run(["git", "-C", str(radice), "ls-files", "*.ps1", "*.psm1"], capture_output=True, text=True, encoding="utf-8")
    nomi = r.stdout.split("\n") if r.returncode == 0 else [str(p.relative_to(radice)) for p in radice.rglob("*.ps1")]
    return [radice / n for n in nomi if n.strip() and not FUORI.intersection(Path(n).parts)]


def esamina(radice: Path) -> list:
    trovati = []
    for f in file_powershell(radice):
        try:
            righe = f.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        except OSError:
            continue
        for i, riga in enumerate(righe, 1):
            if riscontri_riga(riga):
                trovati.append((f.relative_to(radice).as_posix(), i, riga.strip()))
    return trovati


def cmd(radice: Path, rigoroso: bool) -> int:
    trovati = esamina(radice)
    for f, i, riga in trovati:
        print("%s:%d: conversione senza cultura: %s" % (f, i, riga[:140]))
    if trovati:
        print("%d conversioni dipendono dalla cultura di sistema: si passa [Globalization.CultureInfo]::InvariantCulture" % len(trovati))
        return 1 if (rigoroso or nel_template(radice)) else 0
    print("lint-cultura: nessuna conversione dipende dalla cultura di sistema")
    return 0


def autotest() -> int:
    casi = rossi = 0

    def caso(nome: str, ok: bool) -> None:
        nonlocal casi, rossi
        casi += 1
        rossi += 0 if ok else 1
        print(("ok   " if ok else "ROSSO ") + nome)

    caso("il caso osservato si segnala", riscontri_riga('$d = [double]::Parse($uscita.Trim())') == 1)
    caso("con la cultura invariante passa", riscontri_riga('$d = [double]::Parse($s, [Globalization.CultureInfo]::InvariantCulture)') == 0)
    caso("una variabile come fornitore di formato passa", riscontri_riga("[double]::Parse((\"$s\" -replace ',','.'), $inv)") == 0)
    caso("TryParse con il solo [ref] si segnala", riscontri_riga('[double]::TryParse($s, [ref]$v)') == 1)
    caso("TryParse con stile, cultura e [ref] passa",
         riscontri_riga("[double]::TryParse($s, [Globalization.NumberStyles]::Float, $inv, [ref]$v)") == 0)
    caso("lo stile da solo non è una cultura", riscontri_riga("[double]::Parse($s, [System.Globalization.NumberStyles]::Float)") == 1)
    caso("una data si segnala come un numero", riscontri_riga('$t = [datetime]::Parse($misure[-1])') == 1)
    caso("Convert.ToDouble senza cultura si segnala", riscontri_riga('[Convert]::ToDouble($x)') == 1)
    caso("le parentesi annidate nel primo argomento non contano come argomenti",
         riscontri_riga("[double]::Parse((Get-Date -UFormat '%s'))") == 1)
    caso("il cast e -as non si segnalano", riscontri_riga('$a = [double]"1.5"; $b = $s -as [double]') == 0)
    caso("i tipi interi restano fuori", riscontri_riga('[int]::Parse($s)') == 0)
    caso("una riga marcata passa", riscontri_riga('[double]::Parse($s)  # cultura-ok: il testo è già invariante') == 0)
    caso("due chiamate sulla stessa riga contano due volte", riscontri_riga('[double]::Parse($a) + [decimal]::Parse($b)') == 2)
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        subprocess.run(["git", "init", "-q", str(r)], check=True)
        (r / "a.ps1").write_text("$x = [double]::Parse($s)\n", encoding="utf-8")
        (r / "fixtures").mkdir()
        (r / "fixtures" / "b.ps1").write_text("$x = [double]::Parse($s)\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(r), "add", "-A"], check=True)
        trovati = esamina(r)
        caso("si leggono i file tracciati, non le fixture", [t[0] for t in trovati] == ["a.ps1"])
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            rc_progetto = cmd(r, False)
            rc_rigoroso = cmd(r, True)
            (r / ".claude").mkdir()
            (r / ".claude" / "PROMPT-nuovo-progetto.md").write_text("x", encoding="utf-8")
            (r / "README.md").write_text("<!-- sync-readme:packages:start -->\n", encoding="utf-8")
            rc_template = cmd(r, False)
        caso("in un progetto avvisa e non ferma", rc_progetto == 0)
        caso("con --rigoroso ferma", rc_rigoroso == 1)
        caso("nel template ferma", rc_template == 1)
    print("\n%d casi superati su %d" % (casi - rossi, casi))
    return 1 if rossi else 0


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Conversioni PowerShell che dipendono dalla cultura di sistema.")
    p.add_argument("radice", nargs="?", default=".")
    p.add_argument("--autotest", action="store_true")
    p.add_argument("--rigoroso", action="store_true")
    a = p.parse_args(argv)
    if a.autotest:
        return autotest()
    return cmd(Path(a.radice), a.rigoroso)


if __name__ == "__main__":
    sys.exit(main())
