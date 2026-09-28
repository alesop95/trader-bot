#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Suite di test di md-unwrap: fixture, idempotenza, oracolo di rendering, CLI.

Uso: python tests/run-tests.py [-v]
Esce 0 se tutto passa, 1 al primo fallimento riscontrato nella suite.
"""

from __future__ import annotations

import difflib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(os.path.dirname(HERE), 'tools', 'md-unwrap.py')
FIXTURES = os.path.join(HERE, 'fixtures')

VERBOSE = '-v' in sys.argv[1:]


def load_tool():
    spec = importlib.util.spec_from_file_location('md_unwrap', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mu = load_tool()

results = {'pass': 0, 'fail': 0, 'skip': 0}


def report(ok, name, detail=''):
    if ok is None:
        results['skip'] += 1
        print('SKIP  %s%s' % (name, (' - ' + detail) if detail else ''))
        return
    if ok:
        results['pass'] += 1
        if VERBOSE:
            print('ok    %s' % name)
        return
    results['fail'] += 1
    print('FAIL  %s' % name)
    if detail:
        print(''.join('        %s\n' % line for line in detail.splitlines()))


def read(path):
    with open(path, 'rb') as fh:
        return fh.read().decode('utf-8')


def show_diff(expected, got):
    return ''.join(difflib.unified_diff(
        expected.splitlines(keepends=True), got.splitlines(keepends=True),
        fromfile='atteso', tofile='ottenuto',
    )) or '(differenza solo nei terminatori di riga)'


def case_names():
    return sorted(
        name for name in os.listdir(FIXTURES)
        if os.path.isdir(os.path.join(FIXTURES, name))
    )


# --------------------------------------------------------------------------- #
# 1. Trasformazione: output byte per byte uguale all'atteso                    #
# --------------------------------------------------------------------------- #

def test_fixtures():
    for name in case_names():
        folder = os.path.join(FIXTURES, name)
        src = read(os.path.join(folder, 'input.md'))
        expected = read(os.path.join(folder, 'expected.md'))
        got, joins = mu.unwrap(src)
        ok = got == expected
        detail = ''
        if not ok:
            detail = show_diff(expected, got)
            detail += '\nbyte attesi: %r\nbyte ottenuti: %r' % (
                expected.encode('utf-8')[:400], got.encode('utf-8')[:400])
        report(ok, 'fixture %s (%d righe unite)' % (name, joins), detail)


# --------------------------------------------------------------------------- #
# 2. Idempotenza: la seconda corsa non cambia nulla                           #
# --------------------------------------------------------------------------- #

def test_idempotence():
    for name in case_names():
        src = read(os.path.join(FIXTURES, name, 'input.md'))
        once, _ = mu.unwrap(src)
        twice, joins = mu.unwrap(once)
        report(twice == once and joins == 0, 'idempotenza %s' % name,
               show_diff(once, twice) if twice != once else
               ('la seconda corsa dichiara %d righe unite' % joins))


# --------------------------------------------------------------------------- #
# 3. Oracolo di rendering: l'HTML normalizzato non cambia                      #
# --------------------------------------------------------------------------- #

def test_render_oracle():
    if mu.get_oracle() is None:
        report(None, 'oracolo di rendering',
               'markdown-it-py non installato (pip install markdown-it-py)')
        return
    for name in case_names():
        src = read(os.path.join(FIXTURES, name, 'input.md'))
        got, _ = mu.unwrap(src)
        reason = mu.render_equal(src, got)
        detail = ''
        if reason:
            md = mu.get_oracle()
            detail = 'atteso: %s\nottenuto: %s' % (md.render(src), md.render(got))
        report(reason is None, 'oracolo %s' % name, detail)


def test_guarded_pass():
    """La passata prudente non unisce i blocchi attraversati da un code span."""
    src = read(os.path.join(FIXTURES, 'code-span-su-piu-righe', 'input.md'))
    normale, _ = mu.unwrap(src)
    prudente, _ = mu.unwrap(src, guard_spans=True)
    report(normale != src, 'la passata normale unisce il blocco con il code span')
    prima_riga = prudente.splitlines()[0]
    report(prima_riga.endswith('e va') or 'CHIAVE=valore' not in prima_riga,
           'la passata prudente lascia il code span intatto', prima_riga)
    report(mu.render_equal(src, prudente) is None,
           'anche la passata prudente supera l\'oracolo')

    # Il paragrafo con lo schema a caratteri non si unisce in nessuna delle due.
    art = read(os.path.join(FIXTURES, 'schema-a-caratteri', 'input.md'))
    for etichetta, guard in (('normale', False), ('prudente', True)):
        out, _ = mu.unwrap(art, guard_spans=guard)
        report('|   Telefono   |        |   DAC USB    |' in out,
               'lo schema a caratteri sopravvive alla passata %s' % etichetta)


def test_oracle_catches_corruption():
    """L'oracolo deve bocciare una trasformazione che cambia il rendering."""
    before = 'Titolo\n------\n'
    corrupted = 'Titolo ------\n'
    if mu.get_oracle() is None:
        report(None, 'l\'oracolo boccia un rendering diverso',
               'serve markdown-it-py: l\'invariante interna, da sola, non lo vede')
    else:
        reason = mu.verify(before, corrupted, 'auto')
        report(reason is not None, 'l\'oracolo boccia un rendering diverso',
               'nessun motivo restituito su un caso volutamente rotto')

    reason = mu.check_invariant('parola\n', 'parolla\n')
    report(reason is not None, 'l\'invariante boccia una perdita di caratteri')

    reason = mu.check_invariant('a\nb\n', 'a b\n')
    report(reason is None, 'l\'invariante accetta la sola differenza di spazio bianco',
           str(reason))


# --------------------------------------------------------------------------- #
# 4. CLI: --check, --diff, scrittura in-place, esclusioni, codici di uscita    #
# --------------------------------------------------------------------------- #

def run_cli(args, cwd):
    proc = subprocess.run(
        [sys.executable, TOOL] + args, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    return proc.returncode, proc.stdout.decode('utf-8', 'replace')


def test_cli():
    with tempfile.TemporaryDirectory() as tmp:
        # Albero di prova: due file da cambiare, uno già a posto, uno in una
        # cartella esclusa di default, uno con estensione non trattata.
        changing = ['paragrafo-hard-wrapped', 'elenco-numerato']
        for name in changing + ['gia-srotolato']:
            shutil.copy(os.path.join(FIXTURES, name, 'input.md'),
                        os.path.join(tmp, name + '.md'))
        os.makedirs(os.path.join(tmp, 'node_modules'))
        shutil.copy(os.path.join(FIXTURES, 'paragrafo-hard-wrapped', 'input.md'),
                    os.path.join(tmp, 'node_modules', 'escluso.md'))
        os.makedirs(os.path.join(tmp, 'docs'))
        shutil.copy(os.path.join(FIXTURES, 'elenco-puntato', 'input.md'),
                    os.path.join(tmp, 'docs', 'annidato.md'))
        shutil.copy(os.path.join(FIXTURES, 'paragrafo-hard-wrapped', 'input.md'),
                    os.path.join(tmp, 'non-markdown.txt'))
        escluso_prima = read(os.path.join(tmp, 'node_modules', 'escluso.md'))
        txt_prima = read(os.path.join(tmp, 'non-markdown.txt'))

        code, out = run_cli(['--check', '.'], tmp)
        report(code == 1, '--check esce 1 quando qualcosa cambierebbe', out)
        report('3 da modificare' in out, '--check conta i tre file da modificare', out)
        report('node_modules' not in out, '--check ignora node_modules', out)
        report(read(os.path.join(tmp, 'paragrafo-hard-wrapped.md')) ==
               read(os.path.join(FIXTURES, 'paragrafo-hard-wrapped', 'input.md')),
               '--check non scrive nulla')

        code, out = run_cli(['--diff', '.'], tmp)
        report(code == 0, '--diff esce 0', out)
        report('--- paragrafo-hard-wrapped.md (originale)' in out,
               '--diff mostra il diff unificato', out)
        report(read(os.path.join(tmp, 'paragrafo-hard-wrapped.md')) ==
               read(os.path.join(FIXTURES, 'paragrafo-hard-wrapped', 'input.md')),
               '--diff non scrive nulla')

        code, out = run_cli(['.'], tmp)
        report(code == 0, 'scrittura in-place esce 0', out)
        for name in changing:
            report(read(os.path.join(tmp, name + '.md')) ==
                   read(os.path.join(FIXTURES, name, 'expected.md')),
                   'scrittura in-place di %s' % name)
        report(read(os.path.join(tmp, 'docs', 'annidato.md')) ==
               read(os.path.join(FIXTURES, 'elenco-puntato', 'expected.md')),
               'ricorsione nelle sottocartelle')
        report(read(os.path.join(tmp, 'node_modules', 'escluso.md')) == escluso_prima,
               'i file nelle cartelle escluse non vengono toccati')
        report(read(os.path.join(tmp, 'non-markdown.txt')) == txt_prima,
               'le estensioni non trattate non vengono toccate')

        code, out = run_cli(['--check', '.'], tmp)
        report(code == 0, '--check esce 0 dopo la scrittura (idempotenza via CLI)', out)

        code, out = run_cli(['--check', '--exclude', 'docs', '.'], tmp)
        report(code == 0 and 'docs' not in out, '--exclude aggiunge un pattern', out)

        code, out = run_cli(['--check', 'file-che-non-esiste.md'], tmp)
        report(code == 2, 'un percorso inesistente esce 2', out)

        # Marcatore .md-unwrap-ignore: il sottoalbero non si tocca nemmeno se
        # passato per nome.
        protetto = os.path.join(tmp, 'protetto')
        os.makedirs(protetto)
        shutil.copy(os.path.join(FIXTURES, 'paragrafo-hard-wrapped', 'input.md'),
                    os.path.join(protetto, 'intoccabile.md'))
        with open(os.path.join(protetto, mu.IGNORE_MARKER), 'w') as fh:
            fh.write('non toccare\n')
        prima = read(os.path.join(protetto, 'intoccabile.md'))
        code, out = run_cli(['--check', '.'], tmp)
        report(code == 0 and '1 ignorati per marcatore' in out,
               'il marcatore .md-unwrap-ignore esclude il sottoalbero', out)
        code, out = run_cli(['protetto/intoccabile.md'], tmp)
        report(read(os.path.join(protetto, 'intoccabile.md')) == prima,
               'il marcatore vale anche sul file passato per nome', out)

        # --only-tracked: fuori da un repository git nessun file è tracciato,
        # quindi nulla viene scritto e tutto viene dichiarato.
        shutil.copy(os.path.join(FIXTURES, 'citazione', 'input.md'),
                    os.path.join(tmp, 'senza-git.md'))
        prima = read(os.path.join(tmp, 'senza-git.md'))
        code, out = run_cli(['--only-tracked', '.'], tmp)
        report(read(os.path.join(tmp, 'senza-git.md')) == prima and code == 2 and
               'non e un repository git' in out,
               '--only-tracked non scrive i file senza rete di recupero', out)
        os.remove(os.path.join(tmp, 'senza-git.md'))  # non sporcare i controlli seguenti

        code, out = run_cli(['--check', '--oracle', 'require', '.'], tmp)
        expected_code = 0 if mu.get_oracle() else 2
        report(code == expected_code,
               '--oracle require: esce %d' % expected_code, out)


def main():
    print('md-unwrap: suite di test')
    print('strumento: %s' % TOOL)
    print('oracolo di rendering: %s' % ('markdown-it-py attivo' if mu.get_oracle()
                                        else 'assente, solo invariante interna'))
    print('')
    test_fixtures()
    test_idempotence()
    test_render_oracle()
    test_guarded_pass()
    test_oracle_catches_corruption()
    test_cli()
    print('')
    print('%d passati, %d falliti, %d saltati' % (
        results['pass'], results['fail'], results['skip']))
    return 1 if results['fail'] else 0


if __name__ == '__main__':
    sys.exit(main())
