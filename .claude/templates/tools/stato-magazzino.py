#!/usr/bin/env python3
"""Resoconto del magazzino nascosto di Claude Code per Linux e macOS, gemello di
stato-magazzino.ps1.

Perche' serve. Il wipe a fine sessione (session-end-wipe.sh) deve sapere quali sessioni
sono ancora aperte, per togliere subito tutto cio' che appartiene a quelle chiuse e
conservare solo cio' che appartiene a una sessione con un processo vivo. Le stesse regole
servono a chi guarda: quali sessioni sono aperte, quali sono chiuse e aspettano solo il
wipe, e che cosa lanciare. La variante Windows e' stato-magazzino.ps1; le regole sono le
stesse e sono descritte li' per esteso.

Le regole, in breve. Una sessione e' aperta con certezza quando esiste
<account>/sessions/<pid>.json di un processo Claude Code vivo, scritto dopo l'avvio di
quel processo: un PID riusato ha lo stesso numero e un avvio piu' recente del file. Per un
processo vivo senza file si propongono come candidati i verbali con attivita' dopo il suo
avvio che nessuna sessione certa rivendica, prima quelli nati dopo l'avvio e poi gli
altri; il wipe conserva i primi tre finche' quel processo esiste. La sessione da cui
discende lo strumento e' quella che sta chiudendo, se lo ha lanciato l'hook; con
--manuale conta invece come aperta.

Uso:
    python3 stato-magazzino.py                    resoconto compatto, sola lettura
    python3 stato-magazzino.py --senza-testi      senza titoli e richieste
    python3 stato-magazzino.py --chiudi <PID>     chiude una sessione, con conferma da tastiera
    python3 stato-magazzino.py --protezione-sh [--manuale]   per session-end-wipe.sh
    python3 stato-magazzino.py --autotest
"""

import argparse
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ID_RX = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


# --- lettura del magazzino ---------------------------------------------------

def leggi_verbale(path):
    """Un verbale e' un .jsonl per sessione. Se ne leggono le righe che Claude Code scrive
    per l'indice: 'ai-title' (titolo), 'last-prompt' (una riga a ogni turno: la prima e'
    la prima richiesta, l'ultima l'ultima), e la prima occorrenza di timestamp e cwd."""
    v = {'id': path.stem, 'file': str(path), 'byte': path.stat().st_size,
         'ultima': path.stat().st_mtime, 'prima': None, 'cwd': None,
         'titolo': None, 'prima_richiesta': None, 'ultima_richiesta': None, 'turni': 0}
    try:
        with open(path, encoding='utf-8', errors='replace') as fh:
            for riga in fh:
                if v['prima'] is None:
                    m = re.search(r'"timestamp":"([^"]+)"', riga)
                    if m:
                        try:
                            v['prima'] = utc_iso_a_epoch(m.group(1))
                        except ValueError:
                            pass
                if v['cwd'] is None:
                    m = re.search(r'"cwd":"((?:[^"\\]|\\.)*)"', riga)
                    if m:
                        v['cwd'] = m.group(1).replace('\\\\', '\\')
                if riga.startswith('{"type":"last-prompt"') or riga.startswith('{"type":"ai-title"') or riga.startswith('{"type":"custom-title"'):
                    try:
                        o = json.loads(riga)
                    except ValueError:
                        continue
                    if o.get('type') == 'last-prompt' and o.get('lastPrompt'):
                        v['prima_richiesta'] = v['prima_richiesta'] or o['lastPrompt']
                        v['ultima_richiesta'] = o['lastPrompt']
                        v['turni'] += 1
                    elif o.get('type') == 'custom-title' and o.get('customTitle'):
                        v['titolo'] = o['customTitle']
                    elif o.get('type') == 'ai-title' and o.get('aiTitle'):
                        v['titolo'] = o['aiTitle']
    except OSError:
        pass
    return v


def utc_iso_a_epoch(s):
    """'2026-10-09T07:00:00.000Z' -> secondi epoch."""
    import calendar
    return calendar.timegm(time.strptime(s[:19], '%Y-%m-%dT%H:%M:%S'))


def leggi_diario(base):
    log = base / 'session-end-wipe.log'
    d = {'presente': False, 'modo': None, 'esito': 'nessun diario', 'pid': [], 'testo': None}
    if not log.exists():
        return d
    d['presente'] = True
    righe = [r for r in log.read_text(encoding='utf-8', errors='replace').splitlines() if r.strip()]
    for r in righe:
        m = re.match(r'^\ufeff?session-end-wipe: \S+ \S+\s+modo=(\S+)', r)
        if m:
            d['modo'] = m.group(1)
            break
    rim = next((r for r in righe if r.startswith('Rimandato')), None)
    abo = next((r for r in righe if r.startswith('ABORT')), None)
    if rim:
        d['esito'] = 'rimandato'
        m = re.search(r'\(PID ([\d ,]+)\)', rim)
        if m:
            d['pid'] = [int(x) for x in re.split(r'[ ,]+', m.group(1)) if x]
    elif abo:
        d['esito'], d['testo'] = 'fermato', abo
    elif 'Fatto.' in righe:
        d['esito'] = 'fatto'
    else:
        d['esito'] = 'incompleto'
    return d


def nome_account(home):
    return '.claude' if home.name == '.claude' else re.sub(r'^\.claude-', '', home.name)


def leggi_magazzino(radice):
    account = []
    for h in sorted(Path(radice).glob('.claude*')):
        if not h.is_dir() or not any((h / x).exists() for x in ('projects', 'settings.json', 'sessions')):
            continue
        progetti = []
        if (h / 'projects').is_dir():
            for slug in sorted(p for p in (h / 'projects').iterdir() if p.is_dir()):
                verbali = sorted((leggi_verbale(f) for f in slug.glob('*.jsonl')), key=lambda v: v['ultima'], reverse=True)
                progetti.append({'slug': slug.name, 'verbali': verbali})
        sessioni = []
        if (h / 'sessions').is_dir():
            for f in (h / 'sessions').glob('*.json'):
                try:
                    o = json.loads(f.read_text(encoding='utf-8'))
                except (OSError, ValueError):
                    continue
                if o.get('pid'):
                    sessioni.append({'account': nome_account(h), 'pid': int(o['pid']), 'sessionId': o.get('sessionId'),
                                     'cwd': o.get('cwd'), 'startedAt': o.get('startedAt'), 'mtime': f.stat().st_mtime})
        account.append({'nome': nome_account(h), 'base': str(h), 'diario': leggi_diario(h), 'progetti': progetti,
                        'sessioni': sessioni, 'ha_wipe': (h / 'hooks' / 'session-end-wipe.sh').exists()})
    return {'account': account}


# --- processi -----------------------------------------------------------------

def elenca_processi():
    """pid -> {'ppid', 'avvio' (epoch), 'args'}: da /proc dove c'e', altrimenti da ps."""
    out = {}
    proc = Path('/proc')
    if (proc / 'stat').exists():
        btime = 0
        for r in (proc / 'stat').read_text().splitlines():
            if r.startswith('btime '):
                btime = int(r.split()[1])
        tick = os.sysconf('SC_CLK_TCK')
        for d in proc.iterdir():
            if not d.name.isdigit():
                continue
            try:
                stat = (d / 'stat').read_text()
                campi = stat[stat.rindex(')') + 2:].split()
                args = (d / 'cmdline').read_bytes().replace(b'\0', b' ').decode('utf-8', 'replace').strip()
            except (OSError, ValueError):
                continue
            out[int(d.name)] = {'ppid': int(campi[1]), 'avvio': btime + int(campi[19]) / tick, 'args': args}
        return out
    r = subprocess.run(['ps', '-eo', 'pid=,ppid=,etime=,args='], capture_output=True, text=True)
    adesso = time.time()
    for riga in r.stdout.splitlines():
        p = riga.split(None, 3)
        if len(p) < 4:
            continue
        m = re.match(r'^(?:(\d+)-)?(?:(\d+):)?(\d+):(\d+)$', p[2])
        sec = 0
        if m:
            g, o, mi, s = (int(x) if x else 0 for x in m.groups())
            sec = ((g * 24 + o) * 60 + mi) * 60 + s
        out[int(p[0])] = {'ppid': int(p[1]), 'avvio': adesso - sec, 'args': p[3]}
    return out


def contesto(pid):
    """Account e cartella di un processo, letti da /proc: CLAUDE_CONFIG_DIR dall'ambiente,
    la cartella corrente dal collegamento cwd. Aggiunto il 2026-10-09, gemello della lettura
    del PEB in stato-magazzino.ps1. None dove /proc non c'e' o il processo non e' leggibile."""
    base = Path('/proc') / str(pid)
    try:
        env = (base / 'environ').read_bytes().split(b'\0')
        cwd = os.readlink(base / 'cwd')
    except OSError:
        return None
    cfg = next((e.split(b'=', 1)[1].decode('utf-8', 'replace') for e in env if e.startswith(b'CLAUDE_CONFIG_DIR=')), '')
    return {'cwd': cwd.rstrip('/'), 'config_dir': (cfg or os.path.join(os.path.expanduser('~'), '.claude')).rstrip('/')}


def slug_di(percorso):
    """Lo slug con cui Claude Code nomina la cartella di un progetto: ogni carattere che non
    e' una lettera o una cifra diventa un trattino (verificato su Ubuntu e su Windows)."""
    return re.sub(r'[^A-Za-z0-9]', '-', percorso.rstrip('/\\'))


def e_claude_code(args):
    if '--type=' in args:
        return False
    primo = args.split(' ', 1)[0]
    return os.path.basename(primo) in ('claude', 'claude.exe') or '@anthropic-ai/claude-code' in args


def processi_claude(tutti=None, io=None):
    tutti = elenca_processi() if tutti is None else tutti
    io = os.getpid() if io is None else io
    antenati, cur, n = set(), io, 0
    while cur in tutti and n < 64:
        antenati.add(cur)
        cur = tutti[cur]['ppid']
        n += 1
    return [{'pid': pid, 'avvio': p['avvio'], 'args': p['args'], 'proprio': pid in antenati,
             'contesto': p.get('contesto', contesto(pid))}
            for pid, p in tutti.items() if e_claude_code(p['args'])]


def legami(processi, magazzino):
    """Certo: sessions/<pid>.json scritto dopo l'avvio del processo (startedAt in ms, o in
    sua mancanza la data del file), con cinque secondi di tolleranza."""
    file_s = [s for a in magazzino['account'] for s in a['sessioni']]
    tutti_v = [(a['nome'], p['slug'], v) for a in magazzino['account'] for p in a['progetti'] for v in p['verbali']]
    out = []
    for pr in processi:
        f = None
        for s in file_s:
            quando = s['startedAt'] / 1000.0 if s.get('startedAt') else s['mtime']
            if s['pid'] == pr['pid'] and quando >= pr['avvio'] - 5:
                f = s
                break
        out.append({'processo': pr, 'file': f, 'certo': f is not None, 'candidati': [], 'protette': [],
                    'ambito': None, 'account': None, 'slug': None})
    rivendicati = {leg['file']['sessionId'] for leg in out if leg['certo'] and leg['file'].get('sessionId')}
    for leg in out:
        if leg['certo']:
            continue
        avvio = leg['processo']['avvio']
        c = [t for t in tutti_v if t[2]['id'] not in rivendicati and t[2]['ultima'] >= avvio]
        ctx = leg['processo'].get('contesto')
        if ctx and ctx.get('config_dir'):
            # Account e cartella dichiarati dal processo: candidate solo in quel progetto di
            # quell'account, tutte protette.
            acc = next((a for a in magazzino['account'] if os.path.realpath(a['base']) == os.path.realpath(ctx['config_dir'])), None)
            leg['ambito'] = 'processo'
            leg['account'] = acc['nome'] if acc else re.sub(r'^\.claude-', '', os.path.basename(ctx['config_dir']))
            leg['slug'] = slug_di(ctx['cwd']) if ctx.get('cwd') else None
            c = [t for t in c if acc and t[0] == acc['nome'] and (not leg['slug'] or t[1].lower() == leg['slug'].lower())]
        else:
            leg['ambito'] = 'ipotesi'
        nuovi = sorted((t for t in c if t[2]['prima'] and t[2]['prima'] >= avvio - 60), key=lambda t: t[2]['prima'])
        ripresi = sorted((t for t in c if not (t[2]['prima'] and t[2]['prima'] >= avvio - 60)), key=lambda t: t[2]['ultima'], reverse=True)
        leg['candidati'] = nuovi + ripresi
        leg['protette'] = leg['candidati'] if leg['ambito'] == 'processo' else leg['candidati'][:3]
    return out


def protezione(lg):
    ids, primo, incerti, acc_vivi, vive = {}, None, [], set(), []
    slug_account, slug_comune = {}, {}
    for leg in lg:
        pr = leg['processo']
        if pr['proprio']:
            continue
        vive.append(pr['pid'])
        primo = pr['avvio'] if primo is None else min(primo, pr['avvio'])
        if leg['certo']:
            if leg['file'].get('sessionId'):
                ids[leg['file']['sessionId']] = 'PID %d, certa' % pr['pid']
            acc_vivi.add(leg['file']['account'])
        else:
            incerti.append(pr['pid'])
            etichetta = ('PID %d, stesso account e progetto' if leg['ambito'] == 'processo' else 'forse PID %d') % pr['pid']
            for acc, _slug, v in leg['protette']:
                ids.setdefault(v['id'], etichetta)
                acc_vivi.add(acc)
            if leg['ambito'] == 'processo':
                if leg['account']:
                    acc_vivi.add(leg['account'])
                if leg['slug']:
                    for tab, k in ((slug_account, ('%s|%s' % (leg['account'], leg['slug'])).lower()), (slug_comune, leg['slug'].lower())):
                        tab[k] = min(tab.get(k, pr['avvio']), pr['avvio'])
    return {'ids': ids, 'primo': primo, 'incerti': incerti, 'account_vivi': sorted(acc_vivi), 'vive': vive,
            'slug_account': slug_account, 'slug_comune': slug_comune}


# --- stampa ---------------------------------------------------------------------

def breve(s, n):
    t = re.sub(r'\s+', ' ', s or '').strip()
    return t if len(t) <= n else t[:n - 3] + '...'


def data(e):
    return time.strftime('%d/%m %H:%M', time.localtime(e)) if e else '?'


def compatto(mag, lg, senza_testi):
    aperte = {leg['file']['sessionId']: leg['processo']['pid'] for leg in lg if leg['certo'] and leg['file'].get('sessionId')}
    forse = {}
    for leg in lg:
        if not leg['certo']:
            for _a, _s, v in leg['protette']:
                forse.setdefault(v['id'], []).append(leg['processo']['pid'])
    print('\n== Magazzino di Claude Code, %s   (sola lettura)' % time.strftime('%Y-%m-%d %H:%M'))
    print('\nAPERTE ORA, con un processo vivo: %d' % len(lg))
    for leg in sorted(lg, key=lambda x: x['processo']['avvio']):
        pr = leg['processo']
        mia = '   [questa]' if pr['proprio'] else ''
        if leg['certo']:
            v = next((v for a in mag['account'] for p in a['progetti'] for v in p['verbali'] if v['id'] == leg['file']['sessionId']), None)
            tit = '' if senza_testi or not v else '  "%s"' % breve(v['titolo'], 50)
            print('  PID %-7d %-9s %s%s   dal %s%s' % (pr['pid'], leg['file']['account'], leg['file'].get('cwd') or '', tit, data(pr['avvio']), mia))
        elif leg['ambito'] == 'processo':
            seguito = ("le righe 'forse %d' sotto sono sue" % pr['pid']) if leg['protette'] else 'nessun suo verbale su disco'
            print('  PID %-7d %-9s %s   dal %s   senza file di sessione: account e cartella letti dal processo, %s.%s' % (pr['pid'], leg['account'], pr['contesto']['cwd'], data(pr['avvio']), seguito, mia))
        else:
            print("  PID %-7d %-9s account non determinabile, dal %s: nessun file di sessione e processo non leggibile. Le righe 'forse %d' sotto sono le candidate per ipotesi.%s" % (pr['pid'], '?', data(pr['avvio']), pr['pid'], mia))
    chiuse = [(a['nome'], p['slug'], v) for a in mag['account'] for p in a['progetti'] for v in p['verbali'] if v['id'] not in aperte]
    print('\nCHIUSE, DA PULIRE, senza processo: %d' % len(chiuse))
    for acc, slug, v in sorted(chiuse, key=lambda t: (t[0], -t[2]['ultima'])):
        tit = '' if senza_testi else '  ' + breve(v['titolo'] or '(senza titolo)', 40)
        fs = '   forse ' + ', '.join(map(str, forse[v['id']])) if v['id'] in forse else ''
        print('  %-9s %-34s %s  ultima %s%s%s' % (acc, breve(slug, 34), v['id'][:8], data(v['ultima']), tit, fs))
    print('\nCOSA FARE')
    niente = True
    vivi = {leg['processo']['pid'] for leg in lg}
    for a in mag['account']:
        n = sum(1 for c in chiuse if c[0] == a['nome'])
        if not n:
            continue
        niente = False
        d = a['diario']
        if not a['ha_wipe']:
            perche = 'wipe non installato'
        elif d['modo'] and d['modo'] != 'wipe':
            perche = "l'ultima corsa del wipe era una prova (modo %s), che non rimuove niente" % d['modo']
        elif d['esito'] == 'rimandato':
            ancora = [p for p in d['pid'] if p in vivi]
            perche = ('ultimo wipe rimandato per PID %s, ancora aperti' % ', '.join(map(str, ancora))) if ancora else "ultimo wipe rimandato, ma chi lo bloccava ora e' chiuso"
        elif d['esito'] == 'fermato':
            perche = 'ultimo wipe fermato da una guardia'
        elif d['esito'] == 'incompleto':
            perche = "l'ultima corsa del wipe si e' interrotta prima di finire, senza rimuovere tutto"
        else:
            perche = "chiuse dopo l'ultimo wipe"
        print('  %s: %d chiuse, %s.' % (a['nome'], n, perche))
        if a['ha_wipe']:
            print('    bash "%s"' % os.path.join(a['base'], 'hooks', 'session-end-wipe.sh'))
    code = [x for x in elenca_processi().values() if os.path.basename(x['args'].split(' ', 1)[0]) in ('code', 'code-insiders')]
    if code:
        print("  VS Code e' aperto dal %s: il suo pannello delle sessioni puo' mostrare sessioni gia' cancellate finche' non lo chiudi del tutto e lo riapri. L'estensione offre solo Archive, che nasconde senza cancellare." % data(min(x['avvio'] for x in code)))
    if niente:
        print('  niente da pulire.')
    elif any(not leg['processo']['proprio'] for leg in lg):
        print("  Il wipe toglie le chiuse e conserva le aperte e le righe forse. Le aperte si puliscono quando le chiudi. Per chiudere un PID: --chiudi <PID>.")
    print()


# --- autotest -------------------------------------------------------------------

def autotest():
    casi = [0, 0]

    def atteso(nome, cond):
        casi[0] += 1
        if cond:
            print('  ok    ' + nome)
        else:
            casi[1] += 1
            print('  FALLITO ' + nome)
    with tempfile.TemporaryDirectory(prefix='stato-magazzino-prova-') as tmp:
        acc = Path(tmp) / '.claude-accountP'
        proj = acc / 'projects' / 'E--prova'
        proj.mkdir(parents=True)
        (acc / 'sessions').mkdir()
        avvio = time.time() - 7200

        def iso(e):
            return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(e))

        def scrivi(nome, righe, ultima):
            f = proj / (nome + '.jsonl')
            f.write_text('\n'.join(righe) + '\n', encoding='utf-8')
            os.utime(f, (ultima, ultima))
        scrivi('aaaaaaaa-1', ['{"type":"queue-operation","timestamp":"%s"}' % iso(avvio + 60),
                              '{"type":"user","cwd":"E:\\\\prova","timestamp":"x"}',
                              '{"type":"last-prompt","lastPrompt":"prima richiesta di A con citt\u00e0"}',
                              '{"type":"ai-title","aiTitle":"Titolo provvisorio"}',
                              '{"type":"last-prompt","lastPrompt":"ultima richiesta di A"}',
                              '{"type":"ai-title","aiTitle":"Titolo finale di A"}'], time.time())
        scrivi('bbbbbbbb-2', ['{"type":"queue-operation","timestamp":"%s"}' % iso(avvio + 300)], time.time())
        scrivi('cccccccc-3', ['{"type":"queue-operation","timestamp":"%s"}' % iso(avvio - 18000)], avvio - 3600)
        scrivi('dddddddd-4', ['{"type":"queue-operation","timestamp":"%s"}' % iso(avvio - 10800)], time.time())
        (acc / 'sessions' / '111.json').write_text(json.dumps({'pid': 111, 'sessionId': 'aaaaaaaa-1', 'startedAt': int((avvio + 1) * 1000)}))
        (acc / 'sessions' / '333.json').write_text(json.dumps({'pid': 333, 'sessionId': 'dddddddd-4', 'startedAt': int((avvio - 86400) * 1000)}))
        (acc / 'session-end-wipe.log').write_text('session-end-wipe: 2026-10-08 17:56:48  modo=wipe  base=x\nRimandato: 2 altre sessioni di Claude Code aperte (PID 111, 444). x\nNessuna rimozione eseguita.\n')
        m = leggi_magazzino(tmp)
        vA = next(v for v in m['account'][0]['progetti'][0]['verbali'] if v['id'] == 'aaaaaaaa-1')
        atteso('prima richiesta = primo last-prompt, accento intatto', vA['prima_richiesta'] == 'prima richiesta di A con citt\u00e0')
        atteso('ultima richiesta = ultimo last-prompt', vA['ultima_richiesta'] == 'ultima richiesta di A')
        atteso('titolo = ultimo ai-title', vA['titolo'] == 'Titolo finale di A')
        atteso('cwd con barra singola', vA['cwd'] == 'E:\\prova')
        atteso('diario rimandato con due PID', m['account'][0]['diario']['esito'] == 'rimandato' and m['account'][0]['diario']['pid'] == [111, 444])
        procs = [{'pid': 111, 'avvio': avvio, 'args': 'claude', 'proprio': False},
                 {'pid': 222, 'avvio': avvio, 'args': 'claude', 'proprio': False},
                 {'pid': 333, 'avvio': avvio, 'args': 'claude', 'proprio': True}]
        lg = legami(procs, m)
        leg = {x['processo']['pid']: x for x in lg}
        ids222 = [t[2]['id'] for t in leg[222]['candidati']]
        atteso('file di sessione scritto dopo l\'avvio: legame certo', leg[111]['certo'])
        atteso('file di sessione piu\' vecchio del processo (PID riusato): non certo', not leg[333]['certo'])
        atteso('PID senza file: verbale nato dopo l\'avvio per primo', ids222[:1] == ['bbbbbbbb-2'])
        atteso('PID senza file: verbale fermo prima dell\'avvio escluso', 'cccccccc-3' not in ids222)
        atteso('PID senza file: verbale rivendicato escluso', 'aaaaaaaa-1' not in ids222)
        atteso('PID senza file: verbale ripreso dopo i nuovi', ids222[1:2] == ['dddddddd-4'])
        pz = protezione(lg)
        atteso('protezione: certa e candidata protette, ferma no', 'aaaaaaaa-1' in pz['ids'] and 'bbbbbbbb-2' in pz['ids'] and 'cccccccc-3' not in pz['ids'])
        atteso('protezione: la sessione propria non conta fra le vive', 333 not in pz['vive'] and 222 in pz['incerti'])
        altro = Path(tmp) / '.claude-accountQ' / 'projects' / '-home-u-altro'
        altro.mkdir(parents=True)
        fq = altro / 'eeeeeeee-5.jsonl'
        fq.write_text('{"type":"queue-operation","timestamp":"%s"}\n' % iso(avvio + 120), encoding='utf-8')
        m2 = leggi_magazzino(tmp)
        procs2 = [{'pid': 555, 'avvio': avvio, 'args': 'claude', 'proprio': False,
                   'contesto': {'cwd': 'E:\\prova', 'config_dir': str(acc)}},
                  {'pid': 666, 'avvio': avvio, 'args': 'claude', 'proprio': False, 'contesto': None}]
        l2 = {x['processo']['pid']: x for x in legami(procs2, m2)}
        ids555 = [t[2]['id'] for t in l2[555]['candidati']]
        ids666 = [t[2]['id'] for t in l2[666]['candidati']]
        atteso('processo leggibile: candidate solo nel suo account e progetto', 'eeeeeeee-5' not in ids555 and 'bbbbbbbb-2' in ids555 and l2[555]['ambito'] == 'processo')
        atteso('processo non leggibile: l\'ipotesi guarda tutti gli account', 'eeeeeeee-5' in ids666 and l2[666]['ambito'] == 'ipotesi')
        pz2 = protezione(list(l2.values()))
        atteso('processo leggibile: progetto registrato per scratchpad e verbali', 'e--prova' in pz2['slug_comune'] and 'accountp|e--prova' in pz2['slug_account'])
        atteso('slug: ogni carattere non alfanumerico diventa un trattino', slug_di('E:\\retrogame-mod-pok-dev\\') == 'E--retrogame-mod-pok-dev' and slug_di('/var/tmp/x y') == '-var-tmp-x-y')
        tutti = {10: {'ppid': 1, 'avvio': 0, 'args': '/home/u/.local/bin/claude --resume'},
                 11: {'ppid': 10, 'avvio': 0, 'args': 'bash session-end-wipe.sh'},
                 12: {'ppid': 1, 'avvio': 0, 'args': 'node /usr/lib/node_modules/@anthropic-ai/claude-code/cli.js'},
                 13: {'ppid': 1, 'avvio': 0, 'args': 'claude-helper --type=renderer'},
                 14: {'ppid': 1, 'avvio': 0, 'args': 'vim claude.txt'}}
        for v in tutti.values():
            v['contesto'] = None
        pc = {p['pid']: p for p in processi_claude(tutti, 11)}
        atteso('processi: binario claude e pacchetto node riconosciuti', 10 in pc and 12 in pc)
        atteso('processi: ausiliari e omonimi esclusi', 13 not in pc and 14 not in pc)
        atteso('processi: l\'antenato e\' marcato proprio', pc[10]['proprio'] and not pc[12]['proprio'])
    print('autotest: %d casi, %d falliti' % tuple(casi))
    return 1 if casi[1] else 0


# --- principale -----------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--radice', default=os.path.expanduser('~'))
    ap.add_argument('--senza-testi', action='store_true')
    ap.add_argument('--chiudi', type=int, default=0)
    ap.add_argument('--protezione-sh', action='store_true', help='assegnazioni di shell per session-end-wipe.sh')
    ap.add_argument('--manuale', action='store_true', help='la sessione da cui discende conta come aperta')
    ap.add_argument('--autotest', action='store_true')
    a = ap.parse_args()
    if a.autotest:
        return autotest()
    procs = processi_claude()
    if a.manuale:
        for p in procs:
            p['proprio'] = False
    mag = leggi_magazzino(a.radice)
    lg = legami(procs, mag)
    if a.protezione_sh:
        pz = protezione(lg)
        print('PROT_IDS=%s' % shlex.quote(' '.join(pz['ids'])))
        print('PROT_PRIMO=%s' % shlex.quote(str(int(pz['primo'])) if pz['primo'] else ''))
        print('PROT_VIVE=%s' % shlex.quote(' '.join(map(str, pz['vive']))))
        print('PROT_INCERTI=%s' % shlex.quote(' '.join(map(str, pz['incerti']))))
        print('PROT_ACCOUNT_VIVI=%s' % shlex.quote(' '.join(pz['account_vivi'])))
        print('PROT_DETTAGLI=%s' % shlex.quote('; '.join('%s (%s)' % kv for kv in pz['ids'].items())))
        print('PROT_SLUG_ACCOUNT=%s' % shlex.quote(' '.join('%s=%d' % (k, int(v)) for k, v in pz['slug_account'].items())))
        print('PROT_SLUG_COMUNE=%s' % shlex.quote(' '.join('%s=%d' % (k, int(v)) for k, v in pz['slug_comune'].items())))
        return 0
    if a.chiudi:
        p = next((x for x in procs if x['pid'] == a.chiudi), None)
        if not p:
            print("il PID %d non e' una sessione di Claude Code aperta: rifiuto." % a.chiudi)
            return 1
        if p['proprio']:
            print("il PID %d e' la sessione da cui gira questo strumento: rifiuto." % a.chiudi)
            return 1
        compatto(mag, [leg for leg in lg if leg['processo']['pid'] == a.chiudi], a.senza_testi)
        print("Chiudere il PID %d termina la sessione senza che il suo hook SessionEnd parta: il verbale resta e il wipe va rilanciato dopo." % a.chiudi)
        if not sys.stdin.isatty():
            print('nessuna tastiera disponibile: annullato.')
            return 1
        if input('Per confermare riscrivi il PID (%d), qualunque altra risposta annulla: ' % a.chiudi).strip() != str(a.chiudi):
            print('annullato, nessun processo chiuso.')
            return 0
        os.kill(a.chiudi, signal.SIGTERM)
        print('PID %d chiuso.' % a.chiudi)
        return 0
    compatto(mag, lg, a.senza_testi)
    return 0


if __name__ == '__main__':
    sys.exit(main())
