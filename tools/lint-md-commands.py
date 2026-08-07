#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lint dei comandi di shell dentro i blocchi recintati dei file Markdown.

Sola lettura, non scrive nulla, zero dipendenze. Cerca i comandi non copiabili in
una riga sola: continuazioni di riga (`\\` bash, backtick PowerShell, `^` cmd),
heredoc multi-riga, e comandi git che proseguono sulla riga seguente. Serve perche'
`md-unwrap` per contratto non tocca il contenuto dei blocchi recintati, quindi un
comando spezzato dentro un blocco di codice non lo corregge nessuno: va trovato e
sistemato a mano. Attua la verifica richiesta dalla regola
`.claude/rules/git-commands-format.md`.

Un blocco conta come shell solo se lo dichiara la sua info string (`bash`,
`powershell`, `sh`, `console`, ...) oppure se non ha info string e contiene
comandi: un blocco `markdown` o `text` che cita un comando resta prosa, e la prosa
puo' legittimamente finire con un backtick.

Uso: python tools/lint-md-commands.py <cartella> [...]
Esce 0 se non trova nulla, 1 altrimenti, cosi si puo' usare come gate.
"""
import os
import re
import sys

SHELL_INFO = re.compile(r'^(powershell|pwsh|ps1|bash|sh|shell|zsh|console|cmd|batch|bat|terminal)\b', re.I)
RE_FENCE = re.compile(r'^(\s*)(`{3,}|~{3,})(.*)$')
CMD_START = re.compile(r'^\s*(git|gh|python|pip|npm|npx|node|powershell|bash|cd|uv|pipx|docker|claude)(\s|$)')
GIT_START = re.compile(r'^\s*git(\s|$)')

EXCLUDES = {'.git', 'node_modules', '.venv', '__pycache__', 'dist', 'build', 'out', '.next', 'target'}


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDES]
        if '.md-unwrap-ignore' in filenames:
            dirnames[:] = []
            continue
        for name in sorted(filenames):
            if name.lower().endswith(('.md', '.markdown')):
                yield os.path.join(dirpath, name)


def lint(path):
    try:
        with open(path, 'rb') as fh:
            text = fh.read().decode('utf-8')
    except (OSError, UnicodeDecodeError):
        return []
    findings = []
    lines = text.splitlines()
    inside, marker, info, start = False, None, '', 0
    block = []
    for idx, line in enumerate(lines, 1):
        m = RE_FENCE.match(line)
        if not inside:
            if m:
                inside, marker, info, start = True, m.group(2)[0], m.group(3).strip(), idx
                block = []
            continue
        if m and set(line.strip()) == {marker}:
            findings.extend(check_block(path, info, start, block))
            inside = False
            continue
        block.append((idx, line))
    return findings


def check_block(path, info, start, block):
    is_shell = bool(SHELL_INFO.match(info))
    has_cmd = any(CMD_START.match(l) for _, l in block)
    # Un blocco conta come shell solo se lo dichiara la info string, oppure se non
    # ha info string e contiene comandi: un blocco `markdown` o `text` che cita un
    # comando resta prosa, e la prosa puo' legittimamente finire con un backtick.
    if not is_shell and not (not info and has_cmd):
        return []
    # Una continuazione di riga e' un problema quando rompe il copia-incolla sulla
    # shell dichiarata: il backslash dentro un blocco `bash` e' idiomatico e vale
    # come avviso, non come errore, mentre lo stesso backslash in un blocco
    # `powershell` non funziona affatto. Gli avvisi non cambiano il codice di uscita.
    info_l = info.lower()
    shell_ps = bool(re.match(r'^(powershell|pwsh|ps1)\b', info_l))
    out = []
    for n, (idx, line) in enumerate(block):
        body = line.rstrip()
        if body.endswith('\\'):
            # Mai un errore di per se': o e' la continuazione idiomatica di bash,
            # o e' un percorso Windows che finisce con la barra rovesciata, come in
            # `git add docs\`. I due casi non si distinguono con certezza da qui, e
            # quando si tratta davvero di un comando git spezzato lo intercetta il
            # controllo apposta, piu' sotto.
            out.append((path, idx, 'continuazione con backslash', body, False))
        elif body.endswith('`'):
            out.append((path, idx, 'continuazione con backtick PowerShell', body, not shell_ps))
        elif body.endswith('^'):
            out.append((path, idx, 'continuazione con caret cmd', body, True))
        if '<<' in body and re.search(r'<<-?\s*[\'"]?\w+', body):
            out.append((path, idx, 'heredoc multi-riga', body, True))
        # Comando git che prosegue sulla riga dopo senza essere un nuovo comando.
        # Si segnala solo quando la riga seguente ha davvero la forma di una
        # continuazione, cioe' comincia con un'opzione oppure e' rientrata rispetto
        # al comando: altrimenti una riga di stringa in un blocco PowerShell, che e'
        # un'istruzione a se', verrebbe scambiata per continuazione.
        if GIT_START.match(body) and n + 1 < len(block):
            nxt = block[n + 1][1].rstrip()
            rientrata = len(nxt) - len(nxt.lstrip()) > len(body) - len(body.lstrip())
            pare_opzione = nxt.lstrip().startswith('-')
            if nxt and (rientrata or pare_opzione) and not CMD_START.match(nxt) \
               and not nxt.lstrip().startswith('#') \
               and not body.endswith(('|', '&&', '(', '{', ';')):
                out.append((path, block[n + 1][0], 'comando git che continua sulla riga seguente', nxt, True))
    return out


def main():
    roots = sys.argv[1:] or ['.']
    errori = avvisi = 0
    for root in roots:
        for path in walk(root):
            for p, idx, kind, body, grave in lint(path):
                if grave:
                    errori += 1
                else:
                    avvisi += 1
                print('%s:%d  %-8s %-42s %s' % (os.path.relpath(p, root), idx,
                      'ERRORE' if grave else 'avviso', kind, body.strip()[:80]))
    print('')
    print('%d errori, %d avvisi' % (errori, avvisi))
    if avvisi and not errori:
        print('Gli avvisi sono continuazioni idiomatiche della shell dichiarata: '
              'non rompono il copia-incolla su quella shell.')
    return 1 if errori else 0


if __name__ == '__main__':
    sys.exit(main())
