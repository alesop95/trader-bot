#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Misura il carico degli instruction file che Claude Code legge a ogni avvio di sessione.

Sola lettura, non scrive nulla, zero dipendenze. Claude Code concatena in contesto,
prima che l'utente scriva il primo messaggio, il CLAUDE.md utente, quello di progetto,
il CLAUDE.local.md, ogni file .md trovato ricorsivamente sotto .claude/rules/ che non
porti un frontmatter `paths:`, e ogni file tirato dentro da un import a chiocciola.
Oltre una soglia complessiva la sessione si apre con un avviso; molto prima di quella
soglia il carico si paga comunque, in contesto speso a ogni sessione e in aderenza,
perche' file piu' corti producono aderenza migliore.

Questo strumento attua la verifica della sezione 24 di PROJECT-SYSTEM.md: elenca cio'
che viene davvero caricato, dal piu' pesante, e fallisce oltre la soglia di guardia,
cosi' che il budget sia un controllo e non un proposito.

La parte utente, cioe' il CLAUDE.md e le regole della directory di configurazione, si
misura ma non si conteggia nella soglia: sta fuori dal repository, nessun commit la
controlla e cambia da macchina a macchina. Viene mostrata a parte perche' concorre
comunque al limite della piattaforma, e chi legge deve poterla vedere.

Uso: python tools/misura-istruzioni.py [--root .] [--soglia 100000] [--limite 150000]
Esce 0 se la parte di progetto sta sotto la soglia, 1 altrimenti.
"""
import argparse
import os
import re
import sys

LIMITE_PIATTAFORMA = 150000   # soglia oltre la quale Claude Code avvisa all'avvio
SOGLIA_PROGETTO = 100000      # guardia sulla sola parte versionata, lascia margine alla parte utente

RE_FENCE = re.compile(r'^\s*(`{3,}|~{3,})')
RE_IMPORT = re.compile(r'(?<![\w`/])@([A-Za-z0-9_~./\\-]+)')
MAX_HOP = 4                   # profondita' massima degli import, come documentata


def leggi(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        return fh.read()


def ha_paths(testo):
    """Vero se il frontmatter dichiara `paths:`, cioe' se la regola e' condizionale."""
    if not testo.startswith('---'):
        return False
    for riga in testo.split('\n')[1:]:
        if riga.strip() in ('---', '...'):
            return False
        if re.match(r'^paths\s*:', riga):
            return True
    return False


def togli_codice(testo):
    """Rimuove blocchi recintati e code span, dove una chiocciola non e' un import."""
    fuori, dentro = [], False
    for riga in testo.split('\n'):
        if RE_FENCE.match(riga):
            dentro = not dentro
            continue
        if not dentro:
            fuori.append(re.sub(r'`[^`]*`', '', riga))
    return '\n'.join(fuori)


def imports(path, testo, visti, hop=1):
    """Percorsi tirati dentro da un import a chiocciola, ricorsivamente, fino a MAX_HOP salti."""
    out = []
    if hop > MAX_HOP:
        return out
    base = os.path.dirname(os.path.abspath(path))
    for grezzo in RE_IMPORT.findall(togli_codice(testo)):
        cand = os.path.expanduser(grezzo)
        cand = cand if os.path.isabs(cand) else os.path.join(base, cand)
        cand = os.path.normpath(cand)
        if not os.path.isfile(cand) or cand in visti:
            continue
        visti.add(cand)
        out.append(cand)
        out.extend(imports(cand, leggi(cand), visti, hop + 1))
    return out


def raccogli(radice):
    """(percorso, caratteri, nota) di cio' che viene caricato, nell'ordine di scoperta."""
    voci, visti = [], set()

    def aggiungi(path, nota=''):
        ap = os.path.normpath(os.path.abspath(path))
        if ap in visti or not os.path.isfile(ap):
            return None
        visti.add(ap)
        testo = leggi(ap)
        voci.append((ap, len(testo), nota))
        return testo

    istruzioni = ['CLAUDE.md', os.path.join('.claude', 'CLAUDE.md'), 'CLAUDE.local.md']
    # AGENTS.md si conta solo dove nessuno dei tre esiste: con un CLAUDE.md in radice o sopra,
    # Claude legge quello e non AGENTS.md. Contarlo comunque gonfierebbe la misura di un file
    # che la sessione non carica, che e' il difetto di perimetro contro cui questo strumento serve.
    if not any(os.path.isfile(os.path.join(radice, n)) for n in istruzioni):
        istruzioni.append('AGENTS.md')

    for nome in istruzioni:
        path = os.path.join(radice, nome)
        testo = aggiungi(path)
        if testo is not None:
            for imp in imports(path, testo, visti):
                voci.append((imp, len(leggi(imp)), 'import'))

    rules = os.path.join(radice, '.claude', 'rules')
    for dirpath, dirnames, filenames in os.walk(rules):
        dirnames[:] = [d for d in dirnames if d != '__pycache__']
        for nome in sorted(filenames):
            if not nome.endswith('.md'):
                continue
            path = os.path.join(dirpath, nome)
            testo = leggi(path)
            if ha_paths(testo):
                # Dichiarata condizionale: entra in contesto solo quando Claude legge un file
                # che corrisponde ai suoi glob, quindi non pesa sull'avvio. Si stampa comunque,
                # perche' una guardia silenziosa sembra una svista a chi legge l'uscita.
                voci.append((os.path.normpath(os.path.abspath(path)), len(testo), 'paths: non pesa'))
                continue
            aggiungi(path, 'regola sempre attiva')
    return voci


def parte_utente():
    base = os.environ.get('CLAUDE_CONFIG_DIR') or os.path.join(os.path.expanduser('~'), '.claude')
    voci = []
    cand = os.path.join(base, 'CLAUDE.md')
    if os.path.isfile(cand):
        voci.append((cand, len(leggi(cand)), 'utente'))
    for dirpath, _dirnames, filenames in os.walk(os.path.join(base, 'rules')):
        for nome in sorted(filenames):
            if not nome.endswith('.md'):
                continue
            p = os.path.join(dirpath, nome)
            testo = leggi(p)
            if not ha_paths(testo):
                voci.append((p, len(testo), 'utente'))
    return voci


def fmt(n):
    return '{:,}'.format(n).replace(',', '.')


def stampa(titolo, voci, radice):
    print(titolo)
    if not voci:
        print('  (nessuno)')
        return 0
    totale = 0
    for path, n, nota in sorted(voci, key=lambda v: -v[1]):
        if nota != 'paths: non pesa':
            totale += n
        try:
            mostra = os.path.relpath(path, radice)
        except ValueError:
            mostra = path
        print('  %9s  %-54s %s' % (fmt(n), mostra, nota))
    return totale


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', default='.', help='radice del progetto (default: cartella corrente)')
    ap.add_argument('--soglia', type=int, default=SOGLIA_PROGETTO, help='guardia sulla parte di progetto')
    ap.add_argument('--limite', type=int, default=LIMITE_PIATTAFORMA, help='limite complessivo della piattaforma')
    args = ap.parse_args()

    radice = os.path.abspath(args.root)
    tot_p = stampa('Parte di progetto, versionata:', raccogli(radice), radice)
    print('')
    tot_u = stampa('Parte utente, fuori dal repository e non versionata:', parte_utente(), os.path.expanduser('~'))
    print('')
    print('progetto %s caratteri, soglia di guardia %s' % (fmt(tot_p), fmt(args.soglia)))
    print('totale con la parte utente %s, limite della piattaforma %s' % (fmt(tot_p + tot_u), fmt(args.limite)))

    if tot_p > args.soglia:
        print('')
        print('ERRORE: la parte di progetto supera la soglia di guardia di %s caratteri.' % fmt(tot_p - args.soglia))
        print('Una norma che non vale in ogni sessione non sta in .claude/rules/: vive come')
        print('RIFERIMENTO.md dentro la propria skill, con la riga di innesco nel CLAUDE.md.')
        print('Vedi la sezione 24 di .claude/PROJECT-SYSTEM.md.')
        return 1
    if tot_p + tot_u > args.limite:
        print('')
        print('Avviso: la parte di progetto sta sotto la guardia, ma sommata a quella utente')
        print('supera il limite della piattaforma. Alleggerire la parte utente su questa macchina.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
