#!/usr/bin/env python3
"""Dice se il .claude del template e avanti rispetto all'ultima passata di allineamento.

La propagazione di una modifica del template ai progetti istanziati e un comando solo,
`allinea-tutti.ps1 -Applica`, ma va ricordato: il 2026-09-29 dodici progetti sono rimasti
con le norme vecchie per una giornata perché nessuno sapeva che la passata andava rifatta.
Una regola scritta che dice di ricordarlo non basta, per la stessa ragione per cui non
bastava la memoria di chi chiudeva; lo dice quindi `chiudi` sul template, dopo il push,
chiamando questo strumento.

Il confronto e deterministico: ogni progetto del registro `_notes/allineamento/registro.json`
porta l'albero `.claude` del template contro cui e stato misurato l'ultima volta, e se uno
solo e diverso da quello di HEAD la passata non è stata fatta su questo stato del template.
Un registro assente vuol dire che non ne e mai stata fatta una.

Uso, dalla radice del template:
    python .claude/templates/tools/passata-in-sospeso.py

Dal 2026-11-09 distingue due cose che prima confondeva, ed era un difetto: il registro
viene scritto anche da una passata a vuoto, quindi guardare solo l'albero misurato faceva
dire "passata gia' fatta" a un template che nessuno aveva propagato. Si guarda quindi anche
lo stato di ogni progetto: `da-allineare` e `conflitti` vogliono dire misurato e non scritto.

Con --misura, se la propagazione e' dovuta, lancia in sottofondo la sola misura, cioe' la
passata senza -Applica, e torna subito. Nessun file dei progetti viene scritto senza il
proprietario: la misura dice quanti progetti hanno file da ricevere, e l'applicazione resta
un comando suo. E la scelta del proprietario del 2026-11-09, presa dopo una giornata in cui
cinque passate a vuoto sono state lanciate a mano per sapere se ce n'era bisogno.

Uso:
    python .claude/templates/tools/passata-in-sospeso.py            # solo il verdetto
    python .claude/templates/tools/passata-in-sospeso.py --misura   # e avvia la misura

Esce con 0 se non c'è niente da propagare, con 1 se la passata va fatta, con 2 se non
e il template o git non risponde.
"""
import io
import json
import os
import subprocess
import sys
from pathlib import Path


def seleziona(voci: dict) -> list:
    """I soli progetti che esistono ancora e non sono prove in cartelle temporanee.

    Il registro conserva anche le voci delle prove lanciate su cartelle temporanee, che
    nessuno rimisurera' mai: contarle direbbe che la propagazione e' dovuta per sempre.
    """
    fuori = ("\\temp\\", "/temp/")
    return [v for k, v in voci.items()
            if isinstance(v, dict) and v.get("template_albero_claude")
            and Path(k).is_dir() and not any(s in k.lower() for s in fuori)]


def verdetto(misurati: list, albero: str, comando: str) -> tuple:
    """Codice di uscita e righe da stampare, senza toccare il disco.

    Tre esiti e non due. In pari: tutti misurati su questo albero e nessuno in attesa di
    essere scritto. Misurata e non applicata: il registro porta questo albero ma qualche
    progetto e' `da-allineare` o `conflitti`, ed e' il caso che prima veniva scambiato per
    "gia' fatta", perche' una passata a vuoto riscrive il registro come quella che applica.
    Da misurare: qualcuno porta un albero diverso, e che cosa riceverebbe non si sa ancora.
    """
    indietro = [v for v in misurati if v["template_albero_claude"] != albero]
    pendenti = [v for v in misurati if v["template_albero_claude"] == albero
                and v.get("stato") in ("da-allineare", "conflitti")]
    if misurati and not indietro and not pendenti:
        return 0, ["passata gia fatta su questo stato del template (albero .claude %s)" % albero[:7]]
    if pendenti and not indietro:
        quando = max(v.get("misurato_il", "") for v in pendenti)
        conflitti = sum(1 for v in pendenti if v.get("stato") == "conflitti")
        return 1, [
            "misura gia' fatta su questo stato del template (albero .claude %s, del %s):"
            % (albero[:7], quando[:16].replace("T", " ")),
            "   %d progetti hanno file da ricevere%s. Nessuno e' stato scritto: per applicare"
            % (len(pendenti), ", di cui %d in conflitto" % conflitti if conflitti else ""),
            "   " + comando,
        ]
    return 1, [
        "il .claude del template e cambiato dall'ultima passata (%d progetti misurati su un "
        "albero diverso): per propagarlo lanciare" % len(indietro),
        "   " + comando,
        "e poi committare i progetti che la passata elenca come applicati",
    ]


def avvia_misura(radice: Path) -> None:
    """Lancia in sottofondo la sola misura, cioe' la passata senza -Applica.

    Non scrive niente nei progetti e non aspetta: la misura dura decine di minuti e il
    suo esito si legge al giro successivo dal registro, che la passata riscrive in fondo.
    Tre guardie, ciascuna con la sua ragione. Non parte dove `allinea-tutti.ps1` non puo'
    girare, perche' un avvio che fallisce in sottofondo non lo vede nessuno. Non parte se
    il lucchetto della passata esiste, perche' due passate insieme si contenderebbero i
    file dei progetti. E scrive la propria uscita in un file invece che a video, perche'
    un processo staccato che scrive sul terminale del proprietario lo sporca a meta' di
    un altro lavoro.
    """
    if os.name != "nt":
        print("   (la misura in sottofondo non parte: allinea-tutti esiste solo in PowerShell)")
        return
    base = radice / "_notes/allineamento"
    if (base / ".in-corso").exists():
        print("   (una passata e' gia' in corso: non ne avvio una seconda)")
        return
    base.mkdir(parents=True, exist_ok=True)
    uscita = base / "ultima-misura.txt"
    try:
        with io.open(uscita, "w", encoding="utf-8") as f:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                 str(radice / ".claude/templates/tools/allinea-tutti.ps1")],
                cwd=str(radice), stdout=f, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, creationflags=0x00000008 | 0x00000200)
    except OSError as e:
        print("   (misura non avviata: %s)" % e)
        return
    print("   misura avviata in sottofondo, senza scrivere niente nei progetti:")
    print("   l'esito si legge in %s, e al prossimo avvio questo controllo dira' quanti" % uscita)
    print("   progetti hanno file da ricevere, cosi' la passata si applica solo se conviene")


def main() -> int:
    radice = Path.cwd()
    if not (radice / ".claude/PROJECT-SYSTEM.md").is_file() or not (radice / ".claude/templates/PACKAGES.md").is_file():
        print("non e la radice del template", file=sys.stderr)
        return 2
    r = subprocess.run(["git", "rev-parse", "HEAD:.claude"], capture_output=True, text=True, cwd=radice)
    if r.returncode != 0:
        print("git non risponde: " + r.stderr.strip(), file=sys.stderr)
        return 2
    albero = r.stdout.strip()
    registro = radice / "_notes/allineamento/registro.json"
    # Il suggerimento segue la macchina su cui gira: su Linux un comando PowerShell
    # manda chi legge verso un programma che non esiste, e un suggerimento sbagliato
    # costa piu' di nessun suggerimento perche' sembra autorevole.
    if os.name == "nt":
        comando = ('powershell -NoProfile -ExecutionPolicy Bypass -File '
                   '".claude/templates/tools/allinea-tutti.ps1" -Applica')
    else:
        comando = ('la propagazione non ha ancora una forma per questo sistema: '
                   'allinea-tutti esiste solo in PowerShell')
    if not registro.is_file():
        # Mai misurato: e' il caso in cui una misura serve piu' che mai, quindi passa di qui
        # e non torna subito, altrimenti --misura non avrebbe effetto proprio al primo giro.
        print("nessuna passata registrata: per portare questo stato del template ai progetti lanciare")
        print("   " + comando)
        if "--misura" in sys.argv:
            avvia_misura(radice)
        return 1
    try:
        voci = json.loads(registro.read_text(encoding="utf-8"))
    except ValueError:
        print("registro illeggibile: " + str(registro), file=sys.stderr)
        return 2
    misurati = seleziona(voci)
    codice, righe = verdetto(misurati, albero, comando)
    for riga in righe:
        print(riga)
    if codice == 0:
        return 0
    if "--misura" in sys.argv:
        avvia_misura(radice)
    return 1


if __name__ == "__main__":
    sys.exit(main())
