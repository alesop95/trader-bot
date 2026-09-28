#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Presidio del registro di un lavoro a lotti.

Sola lettura salvo il sottocomando `genera`. Zero dipendenze, libreria standard.

PERCHE' NON GUARDA LO STATO DICHIARATO
--------------------------------------
Il campo `stato` di una riga lo scrive l'agente che deve superare il controllo.
Un agente che si dichiara `fatto` senza aver prodotto nulla supererebbe qualunque
verifica basata su quel campo, e non serve malafede: basta un mandato frainteso,
o un'interruzione fra la scrittura dello stato e quella dell'esito.

Questo strumento considera concluso un elemento se e solo se **l'artefatto
esiste, non e' vuoto e supera la soglia minima**. Lo stato dichiarato viene letto
solo per confrontarlo con la realta' e segnalare le discordanze.

CHE COSA NON COPRE, dichiarato come prescrive la disciplina del presidio
-----------------------------------------------------------------------
Distingue la presenza dall'assenza, NON il buono dal mediocre. Sa dire che un
esito esiste ed e' ben formato; non sa dire che sia corretto. Credere il
contrario produce fiducia in una copertura inesistente.

Uso:
  python tools/registro.py stato    <registro.jsonl> [--radice R] [--soglia N]
  python tools/registro.py attendi  <registro.jsonl> [--radice R] [--ogni N] [--fermo N]
  python tools/registro.py prossimo <registro.jsonl> [--quanti N] [--agente A]
  python tools/registro.py genera   <registro.jsonl> --da <cartella> --pattern <glob>
                                    [--radice R] [--artefatti <cartella>] [--estensione .md]

Codici di uscita di `stato`: 0 se non ci sono discordanze, 1 se ce ne sono.
"""
import argparse
import datetime
import hashlib
import json
import os
import sys

STATI = ('da-fare', 'in-corso', 'fatto', 'saltato', 'errore')
SOGLIA_BYTE = 32


def leggi(percorso):
    righe = []
    if not os.path.exists(percorso):
        return righe
    # utf-8-sig e non utf-8: un agente che riscrive il registro da PowerShell vi
    # antepone un BOM, e con 'utf-8' la PRIMA RIGA non si interpreta piu'. Il
    # lettore la scartava in silenzio, e il registro risultava avere un elemento
    # in meno: sembrava una riga persa dall'agente, era il lettore che non la
    # leggeva. Un errore di decodifica che si presenta come dato mancante e' il
    # modo peggiore di sbagliare, perche' porta a cercare il difetto altrove.
    with open(percorso, 'r', encoding='utf-8-sig') as f:
        for n, riga in enumerate(f, 1):
            riga = riga.strip()
            if not riga:
                continue
            try:
                righe.append(json.loads(riga))
            except json.JSONDecodeError as e:
                print('  riga %d non interpretabile, ignorata: %s' % (n, e), file=sys.stderr)
    return righe


def digest(percorso):
    h = hashlib.sha256()
    try:
        with open(percorso, 'rb') as f:
            for blocco in iter(lambda: f.read(65536), b''):
                h.update(blocco)
    except OSError:
        return None
    return h.hexdigest()[:16]


def artefatto_valido(percorso, soglia):
    """Presenza, non qualita'. Tre condizioni, tutte necessarie."""
    if not percorso:
        return False, 'nessun artefatto dichiarato'
    if not os.path.exists(percorso):
        return False, 'artefatto assente'
    try:
        peso = os.path.getsize(percorso)
    except OSError:
        return False, 'artefatto non leggibile'
    if peso == 0:
        return False, 'artefatto vuoto'
    if peso < soglia:
        return False, 'artefatto sotto la soglia minima (%d byte)' % peso
    return True, 'ok'


def cmd_stato(args):
    righe = leggi(args.registro)
    if not righe:
        print('Registro vuoto o inesistente: %s' % args.registro)
        return 0

    conteggi = dict((s, 0) for s in STATI)
    sconosciuti = 0
    discordanze = []
    conclusi_reali = 0
    da_rilavorare = []
    senza_sorgente = 0

    for r in righe:
        stato = r.get('stato', '')
        if stato in conteggi:
            conteggi[stato] += 1
        else:
            sconosciuti += 1

        art = r.get('artefatto') or ''
        if art and not os.path.isabs(art):
            art = os.path.join(args.radice, art)

        ok, motivo = artefatto_valido(art, args.soglia)
        if ok:
            conclusi_reali += 1

        # LA VERIFICA CHE CONTA: lo stato dichiarato contro la realta' su disco.
        if stato == 'fatto' and not ok:
            discordanze.append((r.get('id', '?'), 'dichiarato fatto ma ' + motivo))
        if stato != 'fatto' and ok and stato not in ('saltato', 'errore'):
            discordanze.append((r.get('id', '?'), 'artefatto presente ma stato "%s"' % stato))

        # Un elemento modificato dopo essere stato concluso torna da lavorare:
        # senza questo, un registro diventa una bugia che si consolida.
        #
        # Si usa il campo `sorgente`, scritto da `genera`, e NON l'`id`: l'id e'
        # un identificativo logico relativo alla cartella del corpus, che il
        # registro da solo non conosce. Costruire il percorso dall'id faceva
        # fallire ogni verifica di hash IN SILENZIO, perche' il file non veniva
        # trovato e il controllo si limitava a non eseguirsi. Un controllo che
        # non trova il proprio dato non protesta: semplicemente non controlla.
        sorgente = r.get('sorgente') or ''
        if sorgente and not os.path.isabs(sorgente):
            sorgente = os.path.join(args.radice, sorgente)
        atteso = r.get('hash')
        if stato == 'fatto' and atteso:
            if not sorgente or not os.path.exists(sorgente):
                senza_sorgente += 1
            else:
                attuale = digest(sorgente)
                if attuale and attuale != atteso:
                    da_rilavorare.append(r.get('id', '?'))

        # La nota e' obbligatoria dove l'esito non e' un successo.
        if stato in ('saltato', 'errore') and not (r.get('nota') or '').strip():
            discordanze.append((r.get('id', '?'), 'stato "%s" senza nota' % stato))

    totale = len(righe)
    print('Registro: %s' % args.registro)
    print('Elementi: %d' % totale)
    print('')
    print('  Stato dichiarato')
    for s in STATI:
        if conteggi[s]:
            print('    %-10s %d' % (s, conteggi[s]))
    if sconosciuti:
        print('    %-10s %d' % ('(ignoto)', sconosciuti))
    print('')
    print('  Verifica sugli artefatti (questa e la verifica che conta)')
    print('    conclusi verificati   %d su %d' % (conclusi_reali, totale))
    print('    residui reali         %d' % (totale - conclusi_reali))

    # Un controllo che non ha potuto eseguirsi va DICHIARATO, non taciuto:
    # altrimenti un registro senza sorgenti risolvibili sembra pulito.
    if senza_sorgente:
        print('')
        print('  ATTENZIONE: %d elementi conclusi senza sorgente risolvibile.' % senza_sorgente)
        print('  Per essi la verifica di modifica NON e stata eseguita, quindi il')
        print('  loro esito e ignoto, non ok. Controlla --radice o rigenera il registro.')

    if da_rilavorare:
        print('')
        print('  Sorgente cambiata dopo la conclusione, da rilavorare: %d' % len(da_rilavorare))
        for i in da_rilavorare[:10]:
            print('    %s' % i)
        if len(da_rilavorare) > 10:
            print('    ... e altri %d' % (len(da_rilavorare) - 10))

    if discordanze:
        print('')
        print('  DISCORDANZE fra dichiarato e reale: %d' % len(discordanze))
        print('  Non sono dettagli da sistemare in silenzio: sono la prova che')
        print('  qualcosa nel mandato non ha funzionato. Guardarle prima di rilanciare.')
        for i, motivo in discordanze[:20]:
            print('    %-50s %s' % (i[:50], motivo))
        if len(discordanze) > 20:
            print('    ... e altre %d' % (len(discordanze) - 20))
        print('')
        print('  NOTA: questo presidio distingue la presenza dalla assenza,')
        print('  non il buono dal mediocre. Un artefatto valido non e un artefatto corretto.')
        return 1

    print('')
    print('  Nessuna discordanza.')
    return 0



def cmd_attendi(args):
    """Osserva il registro finche' il lavoro non si ferma.

    Risponde alla domanda pratica "come faccio a sapere quando ha finito",
    che non si risolve guardando il file di sessione dell'agente: quello viene
    scritto con ritardo e il suo orario NON dice se il lavoro stia procedendo.
    Il registro invece cambia a ogni elemento chiuso, quindi e' l'unico segnale
    affidabile.
    """
    import time
    precedente = -1
    fermo = 0
    print('In attesa. Controllo ogni %d secondi; dichiaro finito dopo %d controlli senza progresso.'
          % (args.ogni, args.fermo))
    print('Interrompi con Ctrl+C quando vuoi: non tocca nulla.')
    print('')
    while True:
        righe = leggi(args.registro)
        conclusi = 0
        for r in righe:
            art = r.get('artefatto') or ''
            if art and not os.path.isabs(art):
                art = os.path.join(args.radice, art)
            ok, _ = artefatto_valido(art, SOGLIA_BYTE)
            if ok:
                conclusi += 1
        totale = len(righe)
        ora = time.strftime('%H:%M:%S')
        if conclusi != precedente:
            fermo = 0
            print('  %s  %d su %d conclusi  (+%d)' % (ora, conclusi, totale, 0 if precedente < 0 else conclusi - precedente))
        else:
            fermo += 1
            print('  %s  %d su %d conclusi  (fermo da %d controlli)' % (ora, conclusi, totale, fermo))
        precedente = conclusi

        if conclusi >= totale:
            print('')
            print('FINITO: tutti gli elementi sono conclusi.')
            return 0
        if fermo >= args.fermo:
            print('')
            print('FINITO: nessun progresso da %d controlli. Restano %d elementi.'
                  % (fermo, totale - conclusi))
            print('Esegui ora `stato` per la verifica completa e le discordanze.')
            return 0
        time.sleep(args.ogni)


def cmd_prossimo(args):
    righe = leggi(args.registro)
    candidati = [r for r in righe if r.get('stato') in ('da-fare', 'in-corso')]
    if args.agente:
        candidati = [r for r in candidati if (r.get('agente') or args.agente) == args.agente]
    if not candidati:
        print('Nessun elemento da lavorare.')
        return 0
    print('Prossimi %d di %d rimasti:' % (min(args.quanti, len(candidati)), len(candidati)))
    for r in candidati[:args.quanti]:
        print('  %s' % r.get('id', '?'))
    return 0


def cmd_genera(args):
    import fnmatch
    if os.path.exists(args.registro) and not args.forza:
        print('Il registro esiste gia: %s' % args.registro, file=sys.stderr)
        print('Non lo sovrascrivo, conterrebbe lavoro gia fatto. Usa --forza se sei sicuro.', file=sys.stderr)
        return 1

    elementi = []
    for radice, _dirs, files in os.walk(args.da):
        _dirs[:] = [d for d in _dirs if d not in ('.git', 'node_modules', '.venv', '__pycache__')]
        for nome in sorted(files):
            if not fnmatch.fnmatch(nome, args.pattern):
                continue
            intero = os.path.join(radice, nome)
            rel = os.path.relpath(intero, args.da).replace('\\', '/')
            art = ''
            if args.artefatti:
                art = os.path.join(args.artefatti, rel + args.estensione).replace('\\', '/')
            elementi.append({
                'id': rel,
                # Percorso con cui `stato` ritrova il file per verificarne l'hash.
                # Senza di esso la verifica di modifica non puo' eseguirsi.
                'sorgente': os.path.relpath(intero, args.radice).replace('\\', '/'),
                'hash': digest(intero),
                'stato': 'da-fare',
                'agente': '',
                'artefatto': art,
                'nota': '',
                'aggiornato': datetime.datetime.now().isoformat(timespec='seconds'),
            })

    cartella = os.path.dirname(os.path.abspath(args.registro))
    if cartella and not os.path.isdir(cartella):
        os.makedirs(cartella, exist_ok=True)
    with open(args.registro, 'w', encoding='utf-8') as f:
        for e in elementi:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')

    print('Registro generato: %s' % args.registro)
    print('Elementi: %d' % len(elementi))
    print('')
    print('Prima di lavorare, due domande dal cancello del pacchetto:')
    print('  quanti di questi %d richiedono davvero giudizio di un modello?' % len(elementi))
    print('  quanto costa uno, misurato e non assunto?')
    return 0


def main():
    p = argparse.ArgumentParser(description='Presidio del registro di un lavoro a lotti.')
    sub = p.add_subparsers(dest='cmd')

    a = sub.add_parser('stato', help='verifica gli artefatti e segnala le discordanze')
    a.add_argument('registro')
    a.add_argument('--radice', default='.', help='radice a cui sono relativi id e artefatti')
    a.add_argument('--soglia', type=int, default=SOGLIA_BYTE, help='byte minimi di un artefatto valido')
    a.set_defaults(func=cmd_stato)

    w = sub.add_parser('attendi', help='osserva finche' + chr(39) + 'il lavoro non si ferma')
    w.add_argument('registro')
    w.add_argument('--radice', default='.')
    w.add_argument('--ogni', type=int, default=30, help='secondi fra un controllo e il successivo')
    w.add_argument('--fermo', type=int, default=3, help='controlli senza progresso dopo i quali si dichiara finito')
    w.set_defaults(func=cmd_attendi)

    b = sub.add_parser('prossimo', help='elenca i prossimi elementi da lavorare')
    b.add_argument('registro')
    b.add_argument('--quanti', type=int, default=10)
    b.add_argument('--agente', default='')
    b.set_defaults(func=cmd_prossimo)

    c = sub.add_parser('genera', help='crea il registro dagli elementi di una cartella')
    c.add_argument('registro')
    c.add_argument('--da', required=True)
    c.add_argument('--pattern', default='*')
    c.add_argument('--artefatti', default='')
    c.add_argument('--estensione', default='.md')
    c.add_argument('--radice', default='.', help='radice a cui rendere relativo il percorso della sorgente')
    c.add_argument('--forza', action='store_true')
    c.set_defaults(func=cmd_genera)

    args = p.parse_args()
    if not getattr(args, 'cmd', None):
        p.print_help()
        return 2
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
