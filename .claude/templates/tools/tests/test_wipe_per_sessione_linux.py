#!/usr/bin/env python3
"""Prova end-to-end di session-end-wipe.sh nel modo per sessione, gemella di
test-wipe-per-sessione.ps1 e con gli stessi sei scenari.

Gira solo su Linux o macOS: costruisce due home finte e le radici temporanea e dei log
MCP finte, avvia un processo vero di nome 'claude' (una copia di sleep) con il suo
sessions/<pid>.json, e lancia il wipe compilato con BASE_PROVA, TEMP_PROVA e MCP_PROVA,
cosi' che non tocchi niente di reale. Gli scenari 5 e 6 lanciano il wipe da dentro un
'claude' finto (una copia di bash), una volta a mano e una volta con il payload di
SessionEnd su stdin: la sessione di quel processo resta nel primo caso; nel secondo il wipe
si rilancia staccato, attende l'uscita del 'claude' finto e la toglie. Lo scenario 7 avvia
un 'claude' finto vivo senza file di sessione, con CLAUDE_CONFIG_DIR di un account W e dalla
cartella di un progetto: il wipe legge account e cartella da /proc, conserva verbali e
scratchpad recenti di quel progetto, toglie quelli vecchi, e non protegge il verbale recente
di un altro account X. Lo scenario dello scrub di .claude.json verifica la riduzione alla configurazione
se c'e' Node, altrimenti che il passo sia saltato e dichiarato.

    python3 tests/test_wipe_per_sessione_linux.py
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

TOOLS = Path(__file__).resolve().parents[1]
A = 'aaaaaaaa-1111-2222-3333-444444444444'
B = 'bbbbbbbb-1111-2222-3333-444444444444'
C = 'cccccccc-1111-2222-3333-444444444444'
D = 'dddddddd-1111-2222-3333-444444444444'
VECCHIO = time.mktime((2026, 1, 1, 0, 0, 0, 0, 0, -1))


def scrivi(p, testo, quando=None):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(testo, encoding='utf-8')
    if quando:
        os.utime(p, (quando, quando))


def cartella(p, quando=None):
    scrivi(p / 'x.txt', 'x', quando)
    if quando:
        os.utime(p, (quando, quando))


@unittest.skipUnless(sys.platform.startswith('linux') or sys.platform == 'darwin', 'solo Linux e macOS')
class WipePerSessione(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='prova-wipe-sh-'))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.T, self.U, self.V = (self.tmp / n for n in ('.claude-accountT', '.claude-accountU', '.claude-accountV'))
        self.tmpr, self.mcpr = self.tmp / 'tmpclaude', self.tmp / 'mcpcache'
        self.bin = self.tmp / 'bin'
        self.bin.mkdir()
        self.procs = []
        self.addCleanup(self.ferma)

    def ferma(self):
        for p in self.procs:
            p.kill()
            p.wait()

    def installa(self, acc, libreria=True):
        h = acc / 'hooks'
        h.mkdir(parents=True, exist_ok=True)
        righe = []
        for r in (TOOLS / 'session-end-wipe.sh').read_text().splitlines():
            t = r.lstrip()
            if t.startswith('KEEP_PREFIXES=') and '<KEEP_PREFIXES>' in r:
                r = 'KEEP_PREFIXES=""'
            elif t.startswith('KEEP_PATH_PREFIXES=') and '<KEEP_PATH_PREFIXES>' in r:
                r = 'KEEP_PATH_PREFIXES=("E:")'
            elif t.startswith('ALLOW_EMPTY_KEEP='):
                r = 'ALLOW_EMPTY_KEEP=1'
            righe.append(r)
        (h / 'session-end-wipe.sh').write_text('\n'.join(righe) + '\n')
        shutil.copy(TOOLS / 'scrub-claude-json.js', h)
        if libreria:
            shutil.copy(TOOLS / 'stato-magazzino.py', h)
        elif (h / 'stato-magazzino.py').exists():
            (h / 'stato-magazzino.py').unlink()

    def env(self, acc):
        return dict(os.environ, BASE_PROVA=str(acc), TEMP_PROVA=str(self.tmpr), MCP_PROVA=str(self.mcpr))

    def esegui(self, acc, *args):
        r = subprocess.run(['bash', str(acc / 'hooks' / 'session-end-wipe.sh'), *args], env=self.env(acc),
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
        return r, (acc / 'session-end-wipe.log').read_text()

    def magazzino(self):
        T = self.T
        for acc in (T, self.U, self.V):
            scrivi(acc / 'settings.json', '{}')
        slug = T / 'projects' / '-home-u-p'
        scrivi(slug / (A + '.jsonl'), '{"type":"queue-operation","timestamp":"%s"}' % time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()))
        cartella(slug / A)
        scrivi(slug / (B + '.jsonl'), '{"type":"queue-operation","timestamp":"2026-01-01T00:00:00.000Z"}', VECCHIO)
        cartella(slug / B, VECCHIO)
        cartella(slug / 'memory', VECCHIO)
        for st in ('file-history', 'session-env'):
            cartella(T / st / A)
            cartella(T / st / B, VECCHIO)
        scrivi(T / 'todos' / ('%s-agent-%s.json' % (A, A)), '[]')
        scrivi(T / 'todos' / ('%s-agent-%s.json' % (B, B)), '[]', VECCHIO)
        cartella(T / 'jobs' / 'aaaaaaaa')
        cartella(T / 'jobs' / 'bbbbbbbb', VECCHIO)
        scrivi(T / 'plans' / 'vecchio-piano-qui.md', 'v', VECCHIO)
        scrivi(T / 'sessions' / '99999.json', '{"pid":99999,"sessionId":"x"}', VECCHIO)
        scrivi(T / 'history.jsonl', '\n'.join(json.dumps({'display': 'richiesta di ' + n, 'timestamp': 1, 'sessionId': i}) for n, i in (('A', A), ('B', B))) + '\n')
        cfg = json.dumps({'oauthAccount': {'x': 1}, 'userID': 'u', 'projects': {'E:/p': {'allowedTools': ['a'], 'hasTrustDialogAccepted': True, 'lastCost': 3, 'exampleFiles': ['f']}, 'C:/x': {'lastCost': 1}}})
        scrivi(T / '.claude.json', cfg)
        scrivi(self.U / '.claude.json', cfg)
        scrivi(self.U / 'projects' / '-home-u-q' / (C + '.jsonl'), '{"type":"queue-operation","timestamp":"2026-01-01T00:00:00.000Z"}', VECCHIO)
        cartella(self.tmpr / '-home-u-p' / A)
        cartella(self.tmpr / '-home-u-p' / B, VECCHIO)
        scrivi(self.tmpr / '-home-u-p' / 'altro.txt', 'v', VECCHIO)
        scrivi(self.mcpr / '-home-u-p' / 'mcp-logs-x' / 'vecchio.txt', 'v', VECCHIO)
        scrivi(self.mcpr / '-home-u-z' / 'mcp-logs-y' / 'vecchio.txt', 'v', VECCHIO)
        # il processo vivo finto, poi il suo file di sessione e i file recenti
        claude = self.bin / 'claude'
        shutil.copy(shutil.which('sleep'), claude)
        p = subprocess.Popen([str(claude), '300'])
        self.procs.append(p)
        time.sleep(1.2)
        scrivi(T / 'sessions' / ('%d.json' % p.pid), json.dumps({'pid': p.pid, 'sessionId': A, 'startedAt': int(time.time() * 1000)}))
        scrivi(T / 'plans' / 'nuovo-piano-qui.md', 'n', time.time() + 5)
        scrivi(self.mcpr / '-home-u-p' / 'mcp-logs-x' / 'nuovo.txt', 'n', time.time() + 5)
        return p

    def test_sei_scenari(self):
        T = self.T
        vivo = self.magazzino()
        c = lambda rel: (T / rel).exists()

        # 1. senza libreria: rinvio totale
        self.installa(T, libreria=False)
        r, log = self.esegui(T)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('Rimandato', log)
        self.assertTrue(c('projects/-home-u-p/%s.jsonl' % B))

        # 2. con la libreria: per sessione
        self.installa(T)
        r, log = self.esegui(T)
        self.assertEqual(r.returncode, 0, r.stderr + log)
        self.assertIn('Fatto.', log)
        self.assertIn(A, log)
        self.assertTrue(c('projects/-home-u-p/%s.jsonl' % A) and c('projects/-home-u-p/' + A), log)
        self.assertFalse(c('projects/-home-u-p/%s.jsonl' % B) or c('projects/-home-u-p/' + B) or c('projects/-home-u-p/memory'), log)
        for st in ('file-history', 'session-env'):
            self.assertTrue(c('%s/%s' % (st, A)), st)
            self.assertFalse(c('%s/%s' % (st, B)), st)
        self.assertTrue(c('todos/%s-agent-%s.json' % (A, A)))
        self.assertFalse(c('todos/%s-agent-%s.json' % (B, B)))
        self.assertTrue(c('jobs/aaaaaaaa'))
        self.assertFalse(c('jobs/bbbbbbbb'))
        self.assertTrue(c('plans/nuovo-piano-qui.md'))
        self.assertFalse(c('plans/vecchio-piano-qui.md'))
        self.assertTrue(c('sessions/%d.json' % vivo.pid))
        self.assertFalse(c('sessions/99999.json'))
        h = (T / 'history.jsonl').read_text()
        self.assertIn('richiesta di A', h)
        self.assertNotIn('richiesta di B', h)
        self.assertTrue((self.tmpr / '-home-u-p' / A).exists())
        self.assertFalse((self.tmpr / '-home-u-p' / B).exists() or (self.tmpr / '-home-u-p' / 'altro.txt').exists())
        self.assertTrue((self.mcpr / '-home-u-p' / 'mcp-logs-x' / 'nuovo.txt').exists())
        self.assertFalse((self.mcpr / '-home-u-p' / 'mcp-logs-x' / 'vecchio.txt').exists())
        self.assertFalse((self.mcpr / '-home-u-z').exists())
        self.assertIn('lastCost', (T / '.claude.json').read_text())
        self.assertIn('Blocco 4 rimandato', log)

        # 3. account senza sessioni aperte
        self.installa(self.U)
        r, log = self.esegui(self.U)
        self.assertEqual(r.returncode, 0, r.stderr + log)
        self.assertFalse((self.U / 'projects' / '-home-u-q').exists())
        j = (self.U / '.claude.json').read_text()
        if shutil.which('node'):
            self.assertIn('"E:/p"', j)
            self.assertIn('hasTrustDialogAccepted', j)
            self.assertNotIn('lastCost', j)
            self.assertNotIn('"C:/x"', j)
            self.assertIn('oauthAccount', j)
        else:
            self.assertIn('node non disponibili', log)
            self.assertEqual(j, (T / '.claude.json').read_text())

        # 4. --forza
        r, log = self.esegui(T, '--forza')
        self.assertFalse(c('projects/-home-u-p') or (self.tmpr / '-home-u-p').exists() or (self.mcpr / '-home-u-p').exists(), log)
        self.assertTrue(c('settings.json') and c('hooks/session-end-wipe.sh'))

        # 5 e 6. il wipe discende da un 'claude' finto: a mano o dall'hook
        self.installa(self.V)
        claude_sh = self.bin / 'claude-sh'
        shutil.copy(shutil.which('bash'), claude_sh)
        nome = self.bin / 'claude'
        nome.unlink()
        claude_sh.rename(nome)
        payload = self.tmp / 'payload.json'
        payload.write_text(json.dumps({'session_id': D, 'hook_event_name': 'SessionEnd', 'reason': 'exit'}))
        for modo in ('manuale', 'hook'):
            scrivi(self.V / 'projects' / '-home-u-v' / (D + '.jsonl'), '{"type":"queue-operation","timestamp":"%s"}' % time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()))
            ingresso = '"%s"' % payload if modo == 'hook' else '/dev/null'
            corpo = ('mkdir -p "%s/sessions"; printf \'{"pid":%%s,"sessionId":"%s","startedAt":%%s}\' "$$" "$(($(date +%%s) * 1000))" > "%s/sessions/$$.json"; '
                     'bash "%s/hooks/session-end-wipe.sh" < %s' % (self.V, D, self.V, self.V, ingresso))
            r = subprocess.run([str(nome), '-c', corpo], env=self.env(self.V), stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
            log = (self.V / 'session-end-wipe.log').read_text()
            if modo == 'hook':
                # la copia rilanciata lavora dopo l'uscita del 'claude' finto: si attende il suo Fatto
                fine = time.time() + 90
                while 'Fatto.' not in log and time.time() < fine:
                    time.sleep(0.5)
                    log = (self.V / 'session-end-wipe.log').read_text()
            resta = (self.V / 'projects' / '-home-u-v' / (D + '.jsonl')).exists()
            if modo == 'manuale':
                self.assertIn('Modo manuale', log)
                self.assertTrue(resta, log)
            else:
                self.assertIn('Modo hook', log)
                self.assertIn("Rilanciato fuori dall'hook", log)
                self.assertIn('Modo distaccato', log)
                self.assertIn('Fatto.', log)
                self.assertFalse(resta, log)

        # 7. processo vivo senza file di sessione, con account e cartella leggibili
        W, X = self.tmp / '.claude-accountW', self.tmp / '.claude-accountX'
        prog = self.tmp / 'progettoW'
        prog.mkdir()
        slug = ''.join(ch if ch.isalnum() and ch.isascii() else '-' for ch in str(prog))
        E, F, G = ('%s-1111-2222-3333-444444444444' % x for x in ('eeeeeeee', 'ffffffff', '99999999'))
        for acc in (W, X):
            scrivi(acc / 'settings.json', '{}')
        scrivi(W / 'projects' / slug / (F + '.jsonl'), '{"type":"queue-operation","timestamp":"2026-01-01T00:00:00.000Z"}', VECCHIO)
        cartella(self.tmpr / slug / 'vecchia-sessione', VECCHIO)
        senza = subprocess.Popen([str(nome), '-c', 'sleep 300; true'], cwd=str(prog), env=dict(os.environ, CLAUDE_CONFIG_DIR=str(W)))
        self.procs.append(senza)
        time.sleep(1.2)
        dopo = time.time() + 2
        ora = '{"type":"queue-operation","timestamp":"%s"}' % time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        scrivi(W / 'projects' / slug / (E + '.jsonl'), ora, dopo)
        cartella(self.tmpr / slug / 'sessione-recente', dopo)
        scrivi(X / 'projects' / '-altro' / (G + '.jsonl'), ora, dopo)
        self.installa(W)
        self.installa(X)
        _r, logw = self.esegui(W)
        _r, logx = self.esegui(X)
        self.assertTrue((W / 'projects' / slug / (E + '.jsonl')).exists(), logw)
        self.assertFalse((W / 'projects' / slug / (F + '.jsonl')).exists(), logw)
        self.assertTrue((self.tmpr / slug / 'sessione-recente').exists(), logw)
        self.assertFalse((self.tmpr / slug / 'vecchia-sessione').exists(), logw)
        self.assertFalse((X / 'projects' / '-altro' / (G + '.jsonl')).exists(), logx)
        self.assertIn('Rimossi per categoria: ', logw)


if __name__ == '__main__':
    unittest.main(verbosity=2)
