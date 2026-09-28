#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Esporta i canali di community scelti dal progetto, invocando DiscordChatExporter.

Perché esiste
--------------
L'esportazione periodica dei canali di community è una operazione rara, poche volte
l'anno, e proprio per questo è quella che si sbaglia: fra una corsa e la successiva nessuno
ricorda quali canali contavano, con quali opzioni, e perché quel canale e non un altro.
Uno strumento che porta con sé la scelta dei canali e la sua motivazione trasforma una
procedura da ricordare in una da eseguire.

La scelta dei canali non è un dato di configurazione ma conoscenza del progetto
ospite: dice quale canale risponde a quale domanda aperta. Vive quindi in questo file
insieme al codice che la usa, e si stampa con `--elenco` per poterla leggere senza aprire
il sorgente. All'istanziazione la tabella va sostituita: quella che il file porta è un
esempio della forma, non una configurazione di partenza.

Il token non tocca il disco
---------------------------
Il token si chiede in modo interattivo e non compare né sulla riga di comando né in un
file. La ragione è concreta e va conosciuta perché è un errore facile e già osservato:
PowerShell registra la cronologia dei comandi in un file di testo in chiaro, il cui
percorso si ottiene con `(Get-PSReadlineOption).HistorySavePath`, quindi un token passato
come argomento finisce su disco senza che nessuno lo abbia scritto lì, e ripulirlo richiede
di modificare quel file a mano. La richiesta interattiva non lascia quella traccia.

Resta possibile passarlo dall'ambiente con DISCORD_USER_TOKEN per chi automatizza, ed è
una scelta di chi lo fa: anche l'ambiente di un processo è leggibile, e la cadenza rara
rende il costo di digitarlo nullo.

Quale token, e perché la scelta va registrata
---------------------------------------------
Questo strumento funziona sia con il token di un bot sia con quello di un account
personale, e la differenza non è tecnica ma di regole: la seconda via è vietata dalle
condizioni d'uso della piattaforma, con la terminazione dell'account come sanzione
dichiarata, e la norma `.claude/skills/fonti-non-recuperabili/RIFERIMENTO.md` espone il criterio per
esteso. Se un progetto la sceglie, la scelta va registrata come decisione con i suoi
termini reali e non fatta scivolare dentro un altro lavoro.

Dove un bot può essere invitato, la via preferibile resta `tools/fetch-discord.py` dello
stesso pacchetto, che non mette a rischio nulla e legge il solo incremento fra due corse.

Uso
---
    python tools/export-discord.py --elenco
    python tools/export-discord.py --tier 1 --dry-run
    python tools/export-discord.py --tier 1
    python tools/export-discord.py --tier 1 --html
    python tools/export-discord.py --server NomeDelServer
    python tools/export-discord.py --sigla SIGLA --dry-run
    python tools/export-discord.py --guilds --dry-run
    python tools/export-discord.py --guilds

Il percorso dell'eseguibile di DiscordChatExporter si passa con `--dce` oppure si mette
nella variabile d'ambiente DCE_PATH. Non è una dipendenza del repository e non vi entra: la
procedura di installazione è nel README di questo pacchetto.

Che cosa fa e che cosa non fa
-----------------------------
Non riesporta un canale il cui file esiste già, a meno che non si passi `--forza`: una
esportazione ripetuta per errore costa tempo e richieste al servizio senza aggiungere
nulla. Non tocca il contenuto: la riduzione a Markdown filtrato è il passo successivo, e
lo fa lo strumento di conversione degli export, che questo pacchetto dichiara fra ciò
che gli manca. E non cancella nulla.
"""

import argparse
import getpass
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USCITA = os.path.join(ROOT, "_notes", "fonti", "dce")

# ---------------------------------------------------------------------------------------
# La scelta dei canali del progetto ospite. Ogni voce dice a quale domanda aperta quel
# canale risponde, perché un canale senza domanda è un canale che produrrà materiale da
# leggere e non risposte. La sigla è quella con cui il progetto identifica il proprio
# sottoinsieme di lavoro, dove ne usi una.
#
# Schema: (gruppo di priorità, server, canale, id, sigla, domanda a cui serve)
# ---------------------------------------------------------------------------------------
CANALI = [
    # ATTENZIONE: queste voci sono un esempio e vanno sostituite con i canali del progetto
    # ospite. Non sono una configurazione di partenza ragionevole: sono la forma della
    # tabella. Cancellarle e scrivere le proprie è il primo passo dell'istanziazione.
    #
    # La disciplina da conservare, che è la parte riusabile di questo pacchetto, è che
    # ogni voce dichiari a quale domanda aperta del progetto quel canale risponde. Un
    # canale scelto per argomento produce materiale da leggere; un canale scelto per
    # domanda produce risposte. La differenza si vede al momento di leggere l'export, non
    # al momento di scriverlo, e allora è troppo tardi.
    #
    # I gruppi servono a esportare per priorità invece che tutto insieme: il primo tiene
    # i canali piccoli e sopra una domanda dichiarata, l'ultimo quelli da fare a richiesta
    # quando una domanda specifica lo giustifichi.
    (1, "NomeDelServer", "nome-del-canale", "000000000000000000", "SIGLA",
     "la domanda aperta del progetto a cui questo canale risponde, scritta per esteso: "
     "è ciò che permetterà di decidere, fra sei mesi, se vale ancora esportarlo"),
    (2, "NomeDelServer", "un-altro-canale", "000000000000000001", "SIGLA",
     "una seconda domanda, in un gruppo di priorità inferiore"),
]

# ---------------------------------------------------------------------------------------
# I server da esportare interi, invece che canale per canale. Servono al caso in cui la
# selezione costerebbe più di quanto risparmi: un server piccolo e monotematico, oppure uno
# di cui non si conoscono gli identificativi dei canali. Il meccanismo è exportguild di
# DiscordChatExporter, che non richiede alcun identificativo di canale.
#
# La regola per scegliere fra le due tabelle, che è la parte riusabile: dove gli
# identificativi dei canali si conoscono, la selezione per canale resta preferibile, perché
# un archivio di trenta canali scelti è leggibile e uno di un server intero no. Dove non si
# conoscono, la scelta corretta non è indovinarli, perché un identificativo inventato produce
# un errore che non nomina il campo sbagliato: è cambiare granularità.
#
# Schema: (server, id del server, sigla, domanda a cui serve)
# ---------------------------------------------------------------------------------------
GUILDS = [
    # Anche queste voci sono un esempio da sostituire, come quelle di CANALI.
    ("NomeDelServerPiccolo", "000000000000000002", "SIGLA",
     "la domanda a cui questo server risponde, e la ragione per cui si esporta intero "
     "invece che per canali scelti"),
]

# I server esclusi, con il motivo, perché una esclusione senza motivo è indistinguibile
# da una dimenticanza e verrà riaperta dalla prossima sessione. Anche questa tabella è un
# esempio da sostituire.
ESCLUSI = {
    "NomeDelServerEscluso": "il motivo per cui non serve, scritto in modo che non vada "
                            "riaperto senza una ragione nuova",
}


def token():
    """Il token, dall'ambiente o chiesto in modo interattivo, mai dalla riga di comando.

    La riga di comando è esclusa deliberatamente: PowerShell registra la cronologia dei
    comandi in un file in chiaro, quindi un token passato come argomento finisce su disco
    senza che nessuno lo abbia scritto lì.
    """
    t = os.environ.get("DISCORD_USER_TOKEN")
    if t:
        return t.strip()
    print("Il token non viene mostrato mentre lo incolli e non finisce in alcun file.")
    t = getpass.getpass("Token Discord: ").strip()
    if not t:
        sys.exit("nessun token: nulla da fare")
    return t


def eseguibile(indicato):
    for candidato in (indicato, os.environ.get("DCE_PATH")):
        if candidato and os.path.exists(candidato):
            return candidato
    sys.exit("manca il percorso di DiscordChatExporter.\n"
             "Si passa con --dce, oppure si mette nella variabile d'ambiente DCE_PATH.\n"
             "Non è una dipendenza del repository e non vi entra: la procedura di "
             "installazione sta nel README del pacchetto community-sources.")


def elenco():
    per_tier = {}
    for t, srv, can, cid, track, perche in CANALI:
        per_tier.setdefault(t, []).append((srv, can, cid, track, perche))
    for t in sorted(per_tier):
        print("")
        print("=== Tier " + str(t) + ", " + str(len(per_tier[t])) + " canali")
        for srv, can, cid, track, perche in per_tier[t]:
            print("")
            print("  " + srv + " / " + can + "  [" + track + "]")
            print("  id " + cid)
            print("  " + perche)
    print("")
    print("=== Server esportati interi")
    for srv, gid, track, perche in GUILDS:
        print("")
        print("  " + srv + "  [" + track + "]")
        print("  id " + gid)
        print("  " + perche)
    print("")
    print("=== Server esclusi")
    for srv, motivo in ESCLUSI.items():
        print("  " + srv + ": " + motivo)


def interi(a):
    """Esporta interi i server di GUILDS, ciascuno in una cartella propria.

    Il percorso di destinazione è una cartella e non un file: DiscordChatExporter, quando
    riceve una cartella, nomina da sé i file dei singoli canali, ed è precisamente ciò che
    serve qui, perché i nomi dei canali non li conosciamo in anticipo.
    """
    scelti = [g for g in GUILDS if not a.server or g[0] in a.server]
    if not scelti:
        sys.exit("nessun server corrisponde ai criteri; provare --elenco")

    exe = eseguibile(a.dce) if not a.dry_run else (a.dce or "<percorso di DCE>")
    t = None if a.dry_run else token()

    fatti, falliti = 0, 0
    for i, (srv, gid, _track, _perche) in enumerate(scelti, 1):
        cartella = os.path.join(USCITA, srv)
        etichetta = "[" + str(i) + "/" + str(len(scelti)) + "] " + srv + " -> " + cartella
        if os.path.isdir(cartella) and os.listdir(cartella) and not a.forza:
            print(etichetta + ": la cartella esiste e non è vuota, salto; "
                  "con --forza si riesporta")
            continue
        comando = [exe, "exportguild", "-t", "<token>" if a.dry_run else t,
                   "-g", gid, "-f", "Json", "-o", cartella + os.sep]
        if a.after:
            comando += ["--after", a.after]
        if a.media:
            comando += ["--media"]
        print(etichetta)
        if a.dry_run:
            continue
        # La cartella si crea soltanto quando si esporta davvero, e non una riga prima: una
        # prova a vuoto che lasciasse dietro di sé le cartelle di destinazione non sarebbe una
        # prova a vuoto, ed è l'ordine che il percorso per canali tiene già in `main()`.
        os.makedirs(cartella, exist_ok=True)
        esito = subprocess.run(comando)
        if esito.returncode == 0:
            fatti += 1
        else:
            print("   non riuscito, codice " + str(esito.returncode) +
                  "; si prosegue con gli altri")
            falliti += 1

    if a.dry_run:
        print("")
        print("nulla eseguito: " + str(len(scelti)) + " server sarebbero stati esportati")
        return 0
    print("")
    print("server esportati " + str(fatti) + ", non riusciti " + str(falliti))
    return 1 if falliti else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--elenco", action="store_true",
                    help="stampa la scelta dei canali con la ragione di ciascuno")
    ap.add_argument("--guilds", action="store_true",
                    help="esporta interi i server della tabella GUILDS, invece dei canali")
    ap.add_argument("--tier", type=int, action="append",
                    help="quale gruppo esportare; ripetibile")
    ap.add_argument("--server", action="append", help="limita a questi server; ripetibile")
    ap.add_argument("--sigla", action="append",
                    help="limita ai canali che servono questa sigla di lavoro; ripetibile. "
                         "Serve perché i canali che servono una stessa domanda stanno su più "
                         "gruppi di priorità, e chiederli per gruppo significa chiedere anche il resto")
    ap.add_argument("--dce", help="percorso dell'eseguibile di DiscordChatExporter")
    ap.add_argument("--html", action="store_true",
                    help="esporta anche la resa leggibile, oltre al JSON")
    ap.add_argument("--media", action="store_true",
                    help="scarica anche gli allegati; moltiplica il volume")
    ap.add_argument("--after", help="ignora i messaggi anteriori a questa data")
    ap.add_argument("--forza", action="store_true",
                    help="riesporta anche i canali il cui file esiste già")
    ap.add_argument("--dry-run", action="store_true",
                    help="stampa che cosa farebbe, senza eseguire e senza chiedere il token")
    a = ap.parse_args()

    if a.elenco:
        elenco()
        return 0

    if a.guilds:
        return interi(a)

    # Il confronto sulla sigla è per appartenenza all'insieme e non per sottostringa, perché la
    # colonna ne porta più d'una separate da virgola: una ricerca per sottostringa farebbe
    # corrispondere una sigla contenuta in un'altra, che oggi magari non accade e domani sì.
    def serve(canale):
        sigle = set(x.strip() for x in canale[4].split(","))
        return bool(sigle & set(a.sigla))

    scelti = [c for c in CANALI
              if (not a.tier or c[0] in a.tier)
              and (not a.server or c[1] in a.server)
              and (not a.sigla or serve(c))]
    if not scelti:
        sys.exit("nessun canale corrisponde ai criteri; provare --elenco")

    os.makedirs(USCITA, exist_ok=True)
    exe = eseguibile(a.dce) if not a.dry_run else (a.dce or "<percorso di DCE>")
    t = None if a.dry_run else token()

    fatti, saltati, falliti = 0, 0, 0
    for i, (tier, srv, can, cid, track, _perche) in enumerate(scelti, 1):
        formati = [("Json", "json")] + ([("HtmlDark", "html")] if a.html else [])
        for formato, estensione in formati:
            nome = srv + "-" + can + "." + estensione
            destinazione = os.path.join(USCITA, nome)
            if os.path.exists(destinazione) and not a.forza:
                print("[" + str(i) + "/" + str(len(scelti)) + "] salto " + nome +
                      ", esiste già; con --forza si riesporta")
                saltati += 1
                continue
            comando = [exe, "export", "-t", "<token>" if a.dry_run else t,
                       "-c", cid, "-f", formato, "-o", destinazione]
            if a.after:
                comando += ["--after", a.after]
            if a.media:
                comando += ["--media"]
            if a.dry_run:
                print("[" + str(i) + "/" + str(len(scelti)) + "] " + srv + "/" + can +
                      " -> " + nome)
                continue
            print("[" + str(i) + "/" + str(len(scelti)) + "] " + srv + "/" + can +
                  " -> " + nome)
            esito = subprocess.run(comando)
            if esito.returncode == 0:
                fatti += 1
            else:
                # Un canale può fallire perché l'account non lo vede più, perché è stato
                # cancellato, o per un limite di frequenza persistente: si prosegue con gli
                # altri e si riferisce alla fine, invece di interrompere l'intera corsa.
                print("   non riuscito, codice " + str(esito.returncode) +
                      "; si prosegue con gli altri")
                falliti += 1

    if a.dry_run:
        print("")
        print("nulla eseguito: " + str(len(scelti)) + " canali sarebbero stati esportati")
        return 0
    print("")
    print("esportati " + str(fatti) + ", saltati " + str(saltati) +
          ", non riusciti " + str(falliti))
    print("il passo seguente è ridurre gli export a Markdown filtrato, e la catena "
          "completa è nel README del pacchetto community-sources")
    return 1 if falliti else 0


if __name__ == "__main__":
    sys.exit(main())
