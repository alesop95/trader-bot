# -*- coding: utf-8 -*-
"""Mantiene i wrapper Codex allineati alle skill canoniche del progetto.

Le procedure restano sotto ``.claude/skills``. Per ciascuna crea un wrapper minimale sotto
``.agents/skills`` che espone a Codex nome e descrizione e gli fa leggere il file canonico.
Non copia il corpo della skill, così una modifica della procedura ha una sola fonte di verità.

Uso:
    python tools/sync-codex-skills.py
    python tools/sync-codex-skills.py --check
    python .claude/templates/tools/sync-codex-skills.py --project-root . --check
"""

import argparse
import os
import re
import sys
import textwrap
from pathlib import Path

MARCATORE = "<!-- generato da sync-codex-skills.py; non modificare -->"


def _frontmatter(testo):
    """Estrae i pochi campi necessari senza introdurre una dipendenza YAML."""
    righe = testo.splitlines()
    if not righe or righe[0].strip() != "---":
        return {}
    try:
        fine = righe.index("---", 1)
    except ValueError:
        return {}

    campi = {}
    indice = 1
    while indice < fine:
        riscontro = re.match(r"^([a-zA-Z0-9_-]+):\s*(.*)$", righe[indice])
        if not riscontro:
            indice += 1
            continue
        chiave, valore = riscontro.groups()
        if valore in (">", ">-", "|", "|-"):
            blocco = []
            indice += 1
            while indice < fine and (not righe[indice] or righe[indice][0].isspace()):
                blocco.append(righe[indice].strip())
                indice += 1
            campi[chiave] = " ".join(parte for parte in blocco if parte)
            continue
        campi[chiave] = valore.strip().strip('"\'')
        indice += 1
    return campi


def _wrapper(nome, descrizione, percorso_canonico, base_wrapper):
    descrizione = descrizione or "Esegue la procedura canonica del progetto quando viene richiesta esplicitamente."
    righe = textwrap.wrap(descrizione, width=92, break_long_words=False, break_on_hyphens=False)
    descrizione_yaml = "\n".join("  " + riga for riga in righe)
    percorso = os.path.relpath(percorso_canonico, base_wrapper).replace(os.sep, "/")
    return (
        "---\n"
        "name: %s\n" % nome
        + "description: >\n%s\n" % descrizione_yaml
        + "---\n\n"
        + MARCATORE + "\n\n"
        + "Leggere integralmente [`%s`](%s) e seguirne la procedura canonica. " % (percorso, percorso)
        + "Risolvere i percorsi relativi dalla directory della skill canonica. Tradurre la sintassi o "
        + "i nomi degli strumenti specifici di Claude negli equivalenti disponibili in Codex senza "
        + "indebolire controlli, gate o limiti di autorizzazione.\n"
    )


def _policy_esplicita():
    return "policy:\n  allow_implicit_invocation: false\n"


def _attesi(radice, destinazione):
    sorgente = radice / ".claude" / "skills"
    if not sorgente.is_dir():
        raise SystemExit("Cartella delle skill canoniche non trovata: %s" % sorgente)
    attesi = {}
    for cartella in sorted(percorso for percorso in sorgente.iterdir() if percorso.is_dir()):
        skill = cartella / "SKILL.md"
        if not skill.is_file():
            continue
        metadati = _frontmatter(skill.read_text(encoding="utf-8-sig"))
        nome = metadati.get("name") or cartella.name
        if nome != cartella.name:
            raise SystemExit("Nome skill diverso dalla cartella: %s dichiara %s" % (cartella, nome))
        base = destinazione / nome
        attesi[base / "SKILL.md"] = _wrapper(nome, metadati.get("description", ""), skill, base)
        if metadati.get("disable-model-invocation", "").lower() == "true":
            attesi[base / "agents" / "openai.yaml"] = _policy_esplicita()
    return attesi


def sincronizza(radice, destinazione, solo_controllo=False):
    attesi = _attesi(radice, destinazione)
    difformi = []
    for percorso, contenuto in attesi.items():
        presente = percorso.read_text(encoding="utf-8-sig") if percorso.is_file() else None
        if presente == contenuto:
            continue
        difformi.append(percorso)
        if not solo_controllo:
            percorso.parent.mkdir(parents=True, exist_ok=True)
            percorso.write_text(contenuto, encoding="utf-8", newline="\n")

    nomi_attesi = {percorso.relative_to(destinazione).parts[0] for percorso in attesi}
    if destinazione.is_dir():
        for cartella in sorted(percorso for percorso in destinazione.iterdir() if percorso.is_dir()):
            skill = cartella / "SKILL.md"
            generata = skill.is_file() and MARCATORE in skill.read_text(encoding="utf-8-sig")
            if cartella.name not in nomi_attesi and generata:
                difformi.append(skill)
                if not solo_controllo:
                    skill.unlink()
                    policy = cartella / "agents" / "openai.yaml"
                    if policy.is_file() and policy.read_text(encoding="utf-8-sig") == _policy_esplicita():
                        policy.unlink()
                    if policy.parent.is_dir() and not any(policy.parent.iterdir()):
                        policy.parent.rmdir()
                    if not any(cartella.iterdir()):
                        cartella.rmdir()
                continue
            policy = cartella / "agents" / "openai.yaml"
            if generata and policy not in attesi and policy.is_file() and policy.read_text(encoding="utf-8-sig") == _policy_esplicita():
                difformi.append(policy)
                if not solo_controllo:
                    policy.unlink()
                    if not any(policy.parent.iterdir()):
                        policy.parent.rmdir()
    if difformi:
        azione = "da sincronizzare" if solo_controllo else "sincronizzati"
        for percorso in difformi:
            try:
                mostrato = percorso.relative_to(radice)
            except ValueError:
                mostrato = percorso
            print("%s: %s" % (azione, mostrato))
        return 1 if solo_controllo else 0
    print("Wrapper Codex allineati alle skill canoniche.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".", help="radice del progetto; predefinita: directory corrente")
    parser.add_argument("--destination", help="directory alternativa dei wrapper, utile per test isolati")
    parser.add_argument("--check", action="store_true", help="non scrive e restituisce 1 se i wrapper sono assenti o stale")
    argomenti = parser.parse_args(argv)
    radice = Path(argomenti.project_root).resolve()
    destinazione = Path(argomenti.destination).resolve() if argomenti.destination else radice / ".agents" / "skills"
    return sincronizza(radice, destinazione, argomenti.check)


if __name__ == "__main__":
    sys.exit(main())
