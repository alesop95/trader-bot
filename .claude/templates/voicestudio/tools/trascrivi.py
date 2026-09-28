#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trascrive un file audio o video con il servizio locale di VoiceStudio.

Perché esiste
-------------
La norma `.claude/skills/fonti-non-recuperabili/RIFERIMENTO.md` dice che per un video la forma utile
non è il video ma la sua trascrizione, e prescrive due vie: i sottotitoli automatici dove
esistono, che si scaricano e si ripuliscono con `vtt-to-text.py` del pacchetto
`community-sources`, e il riconoscimento vocale dove non esistono. Fino a che la seconda via
costava una infrastruttura, quella frase restava una prescrizione senza strumento, e le fonti
video finivano catalogate come non lette. VoiceStudio la rende locale: un servizio che gira
sulla macchina, non manda nulla altrove e non richiede un account.

Questo programma è il ponte fra quella regola e quel servizio, e fa una cosa sola: prende un
file, ottiene il testo, e lo scrive dove la regola dice che vada, cioè in `_notes/fonti/` con
la data e il nome della fonte, con accanto da dove viene. L'ultima parte non è cosmesi: una
trascrizione senza la sua provenienza è una citazione senza fonte, e a distanza di un mese
nessuno saprà più se quel testo venga da un video, da un audio di una riunione o da altro.

Che cosa presuppone, e come si verifica prima di scoprirlo
----------------------------------------------------------
Presuppone che VoiceStudio sia in esecuzione sulla macchina. Il servizio espone un documento
di scoperta, e questo programma lo interroga con `--stato` invece di far fallire la prima
trascrizione con un errore di connessione che non nomina la causa. Se il servizio non
risponde, la risposta è che va aperto, non che il file sia sbagliato.

Il contratto che usa è quello compatibile con l'interfaccia OpenAI, cioè una richiesta
multipart verso `/v1/audio/transcriptions`, e la scelta è deliberata: è il contratto più
stabile fra quelli esposti, perché è quello che il servizio deve mantenere per far funzionare
gli SDK di terze parti. Gli altri due, il WebSocket per il testo parziale e il server MCP,
servono casi che questo programma non copre, cioè la dettatura dal vivo e l'uso come tool
dentro una sessione.

Che cosa non fa
---------------
Non clona voci e non sintetizza parlato: quelle capacità esistono nel servizio ma non
appartengono al recupero di una fonte, e metterle qui allargherebbe uno strumento di lettura a
uno strumento di produzione. Non converte i formati: passa il file così com'è, e se il servizio
non lo digerisce lo dice invece di tentare una conversione silenziosa. Non sovrascrive una
trascrizione già presente, perché una seconda corsa sullo stesso file di norma è una
distrazione e non una intenzione; per rifarla si passa `--forza`.

Uso
---
    python tools/trascrivi.py --stato
    python tools/trascrivi.py riunione.m4a --nome riunione-tecnica
    python tools/trascrivi.py video.mp4 --nome intervista --lingua it
    python tools/trascrivi.py audio.wav --nome fonte --out _notes/fonti/2026-09-16-fonte.txt
    python tools/trascrivi.py --self-test

La variabile d'ambiente VOICESTUDIO_URL cambia l'indirizzo del servizio, per chi lo fa girare
su un'altra porta o su un'altra macchina della propria rete. Oltre la rete di casa quel
trasferimento va su un canale cifrato, perché l'audio di una riunione è esattamente il genere
di materiale che non si manda in chiaro.
"""

import argparse
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVIZIO = os.environ.get("VOICESTUDIO_URL", "http://127.0.0.1:3900")
USCITA = os.path.join("_notes", "fonti")

# Il documento di scoperta che il servizio pubblica. Vive in una costante perché è la sola
# richiesta che questo programma fa senza voler trascrivere niente, e la sua risposta è il modo
# di distinguere "il servizio non c'è" da "il file non va bene", che altrimenti arrivano
# entrambe come un errore alla stessa chiamata.
SCOPERTA = "/.well-known/voicestudio-speech"
TRASCRIZIONE = "/v1/audio/transcriptions"

# Il limite di lettura della risposta. Una trascrizione lunga è comunque testo, quindi il tetto
# è alto; serve solo a non far crescere la memoria senza limite se il servizio risponde con
# qualcosa che non è quello che ci si aspetta.
LIMITE_BYTE = 64 * 1024 * 1024


class Errore(Exception):
    """Un guasto che l'utente deve leggere, non una traccia di stack."""


def multipart(campi, nome_file, contenuto):
    """Costruisce il corpo di una richiesta multipart, e ritorna (tipo, corpo).

    Sta qui invece che in una libreria perché la libreria standard non lo fa e perché l'unica
    dipendenza di questo pacchetto deve restare il servizio, non un pacchetto Python. Il
    confine fra le parti è una stringa che non può comparire nel contenuto: si costruisce dal
    momento corrente e non da un numero casuale, così che una richiesta sia riproducibile in
    una prova.
    """
    confine = "----trascrivi-" + str(int(time.time() * 1000))
    pezzi = []
    for chiave, valore in campi:
        if valore is None:
            continue
        pezzi.append(("--" + confine).encode("utf-8"))
        pezzi.append(('Content-Disposition: form-data; name="%s"' % chiave).encode("utf-8"))
        pezzi.append(b"")
        pezzi.append(str(valore).encode("utf-8"))
    pezzi.append(("--" + confine).encode("utf-8"))
    pezzi.append(('Content-Disposition: form-data; name="file"; filename="%s"'
                  % os.path.basename(nome_file)).encode("utf-8"))
    pezzi.append(b"Content-Type: application/octet-stream")
    pezzi.append(b"")
    pezzi.append(contenuto)
    pezzi.append(("--" + confine + "--").encode("utf-8"))
    pezzi.append(b"")
    return "multipart/form-data; boundary=" + confine, b"\r\n".join(pezzi)


class Trasporto:
    """Le richieste vere. Si sostituisce nelle prove, che è la ragione per cui è una classe."""

    def __init__(self, base=SERVIZIO):
        self.base = base.rstrip("/")

    def leggi(self, percorso):
        req = urllib.request.Request(self.base + percorso, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status, r.read(LIMITE_BYTE)
        except urllib.error.HTTPError as e:
            return e.code, e.read(LIMITE_BYTE)
        except Exception as e:
            raise Errore("il servizio non risponde su " + self.base + ": " + str(e))

    def invia(self, percorso, tipo, corpo, attesa):
        req = urllib.request.Request(self.base + percorso, data=corpo,
                                     headers={"Content-Type": tipo, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=attesa) as r:
                return r.status, r.read(LIMITE_BYTE)
        except urllib.error.HTTPError as e:
            return e.code, e.read(LIMITE_BYTE)
        except Exception as e:
            raise Errore("il servizio non risponde su " + self.base + ": " + str(e))


def stato(trasporto):
    """Dice se il servizio c'è e che cosa dichiara, senza trascrivere nulla."""
    codice, corpo = trasporto.leggi(SCOPERTA)
    if codice != 200:
        raise Errore("il servizio risponde %d sul documento di scoperta: e' raggiungibile ma "
                     "non e' VoiceStudio, oppure e' una versione che non lo pubblica" % codice)
    try:
        d = json.loads(corpo.decode("utf-8", "replace"))
    except ValueError:
        raise Errore("il documento di scoperta non e' JSON: all'indirizzo configurato risponde "
                     "qualcosa che non e' questo servizio")
    return d


def estrai_testo(corpo):
    """Il testo dalla risposta, con la diagnosi esplicita quando la risposta e' un errore.

    Il caso che questa funzione esiste per coprire e' quello di un errore consegnato con un
    codice di successo, che e' il modo peggiore di fallire perche' chi guarda il solo codice
    conclude di avere il risultato. La lezione viene dal lettore di Reddit del pacchetto
    `community-sources`, dove la stessa forma di guasto era costata una diagnosi sbagliata.
    """
    testo = corpo.decode("utf-8", "replace")
    try:
        d = json.loads(testo)
    except ValueError:
        # Alcune configurazioni rispondono con il testo nudo. E' un esito valido, purche' non
        # sia vuoto: una risposta vuota non e' una trascrizione riuscita di un silenzio, e
        # trattarla come tale scriverebbe su disco un file che sembra una fonte e non lo e'.
        if testo.strip():
            return testo.strip()
        raise Errore("il servizio ha risposto con un corpo vuoto")
    if isinstance(d, dict) and d.get("error"):
        e = d["error"]
        messaggio = e.get("message") if isinstance(e, dict) else str(e)
        raise Errore("il servizio ha risposto con un errore: " + str(messaggio))
    if isinstance(d, dict) and isinstance(d.get("text"), str) and d["text"].strip():
        return d["text"].strip()
    raise Errore("la risposta non contiene il campo con il testo: " + testo[:200])


def nome_uscita(nome, quando=None):
    """Il percorso della trascrizione, nella convenzione che la regola sulle fonti prescrive."""
    giorno = quando or time.strftime("%Y-%m-%d")
    grezzo = "".join(c if (c.isalnum() or c in "-_") else "-" for c in nome)
    # Le corse di trattini si riducono a uno: un titolo con due segni di punteggiatura
    # adiacenti produrrebbe altrimenti un nome con due trattini, che sembra un refuso.
    pulito = re.sub(r"-{2,}", "-", grezzo).strip("-").lower()
    return os.path.join(USCITA, giorno + "-" + (pulito or "fonte") + ".txt")


def intestazione(sorgente, servizio, modello, lingua):
    """Le righe di provenienza che precedono il testo.

    Esistono perche' una trascrizione da sola non dice da dove viene, e la regola sulle fonti lo
    prescrive esplicitamente per i video. Il modello e' fra i dati perche' due modelli diversi
    danno due trascrizioni diverse dello stesso audio, e senza saperlo un confronto fra due
    trascrizioni misura il modello invece del contenuto.
    """
    return [
        "# Trascrizione automatica",
        "",
        "Sorgente: " + sorgente,
        "Servizio: " + servizio + " (VoiceStudio, riconoscimento vocale locale)",
        "Modello: " + (modello or "predefinito del servizio"),
        "Lingua dichiarata: " + (lingua or "rilevata dal servizio"),
        "Trascritta il: " + time.strftime("%Y-%m-%d %H:%M"),
        "",
        "Testo prodotto da riconoscimento vocale e non riletto: va verificato prima di citarlo "
        "parola per parola.",
        "",
        "---",
        "",
    ]


def trascrivi(trasporto, percorso, nome, lingua=None, modello=None, attesa=1800,
              out=None, forza=False, radice=None):
    """Il flusso completo: legge il file, chiede il testo, lo scrive con la sua provenienza."""
    if not os.path.isfile(percorso):
        raise Errore("non esiste il file da trascrivere: " + percorso)
    base = radice if radice is not None else os.getcwd()
    destinazione = out or os.path.join(base, nome_uscita(nome or
                                                         os.path.splitext(os.path.basename(percorso))[0]))
    if os.path.exists(destinazione) and not forza:
        raise Errore("esiste gia' " + destinazione + ": per rifarla si passa --forza")

    with io.open(percorso, "rb") as fh:
        contenuto = fh.read()
    campi = [("model", modello), ("language", lingua), ("response_format", "json")]
    tipo, corpo = multipart(campi, percorso, contenuto)
    codice, risposta = trasporto.invia(TRASCRIZIONE, tipo, corpo, attesa)
    if codice >= 400:
        raise Errore("il servizio ha rifiutato la richiesta con codice %d: %s"
                     % (codice, risposta.decode("utf-8", "replace")[:300]))
    testo = estrai_testo(risposta)

    cartella = os.path.dirname(destinazione)
    if cartella and not os.path.isdir(cartella):
        os.makedirs(cartella)
    righe = intestazione(percorso.replace("\\", "/"), trasporto.base, modello, lingua)
    with io.open(destinazione, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(righe) + testo + "\n")
    return destinazione, len(testo)


# ------------------------------------------------------------------------------------------
# Le prove. Girano contro un trasporto finto e senza rete, quindi dicono che questo programma
# costruisce bene la richiesta e interpreta bene la risposta; non dicono che il servizio
# funzioni, che e' una proprieta' del servizio e si verifica con --stato su una macchina dove
# gira davvero.
# ------------------------------------------------------------------------------------------

class TrasportoFinto:
    def __init__(self, risposte):
        self.risposte = risposte
        self.base = "http://finto"
        self.viste = []

    def leggi(self, percorso):
        self.viste.append(("GET", percorso, None))
        return self.risposte.get(percorso, (404, b""))

    def invia(self, percorso, tipo, corpo, attesa):
        self.viste.append(("POST", percorso, (tipo, corpo)))
        return self.risposte.get(percorso, (404, b""))


def self_test():
    esiti = []

    def prova(nome, condizione, dettaglio=""):
        esiti.append((nome, bool(condizione), dettaglio))

    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="trascrivi-")
    try:
        audio = os.path.join(tmp, "fonte.wav")
        io.open(audio, "wb").write(b"RIFF....WAVEfmt ")

        # La richiesta: il file c'e', i campi dichiarati ci sono, quelli non dati non ci sono.
        t = TrasportoFinto({TRASCRIZIONE: (200, json.dumps({"text": "ciao mondo"}).encode())})
        dest, n = trascrivi(t, audio, "prova", lingua="it", radice=tmp)
        tipo, corpo = t.viste[0][2]
        prova("la richiesta e' multipart con il suo confine", "boundary=" in tipo, tipo)
        prova("il file viaggia con il proprio nome", b'filename="fonte.wav"' in corpo, "")
        prova("la lingua dichiarata entra nella richiesta", b"\r\nit" in corpo, "")
        prova("negativo: un campo non dato non entra nella richiesta",
              b'name="model"' not in corpo, "")

        # L'uscita: dove la regola dice, con la provenienza davanti al testo.
        prova("la trascrizione finisce sotto _notes/fonti",
              os.path.join("_notes", "fonti") in dest, dest)
        prova("il nome porta la data e la fonte",
              os.path.basename(dest).endswith("-prova.txt"), dest)
        scritto = io.open(dest, encoding="utf-8").read()
        prova("il testo c'e'", "ciao mondo" in scritto, "")
        prova("la provenienza precede il testo",
              scritto.index("Sorgente:") < scritto.index("ciao mondo"), "")
        prova("la provenienza dice che il testo non e' riletto",
              "non riletto" in scritto, "")

        # La seconda corsa non sovrascrive, e con --forza sovrascrive.
        try:
            trascrivi(t, audio, "prova", radice=tmp)
            prova("negativo: la seconda corsa si rifiuta", False, "non ha sollevato")
        except Errore as e:
            prova("negativo: la seconda corsa si rifiuta", "--forza" in str(e), str(e))
        t2 = TrasportoFinto({TRASCRIZIONE: (200, json.dumps({"text": "seconda"}).encode())})
        trascrivi(t2, audio, "prova", radice=tmp, forza=True)
        prova("con --forza la trascrizione si rifa'",
              "seconda" in io.open(dest, encoding="utf-8").read(), "")

        # Gli errori, che sono la meta' del valore di uno strumento come questo.
        t3 = TrasportoFinto({TRASCRIZIONE: (413, b"file troppo grande")})
        try:
            trascrivi(t3, audio, "grande", radice=tmp)
            prova("un rifiuto del servizio si legge come tale", False, "non ha sollevato")
        except Errore as e:
            prova("un rifiuto del servizio si legge come tale", "413" in str(e), str(e))

        prova("un errore consegnato con codice 200 non passa per una trascrizione",
              _solleva(lambda: estrai_testo(json.dumps({"error": {"message": "modello assente"}})
                                            .encode()), "modello assente"))
        prova("negativo: una risposta vuota non e' una trascrizione di un silenzio",
              _solleva(lambda: estrai_testo(b"   "), "vuoto"))
        prova("una risposta di solo testo si accetta",
              estrai_testo(b"testo nudo") == "testo nudo")

        # Lo stato, che distingue il servizio assente dal file sbagliato.
        t4 = TrasportoFinto({SCOPERTA: (200, json.dumps({"protocol": "voicestudio.speech.v1"})
                                        .encode())})
        prova("lo stato legge il documento di scoperta",
              stato(t4).get("protocol") == "voicestudio.speech.v1", "")
        t5 = TrasportoFinto({})
        prova("negativo: senza documento di scoperta lo stato lo dice invece di tacere",
              _solleva(lambda: stato(t5), "404"))
        t6 = TrasportoFinto({SCOPERTA: (200, b"<html>una pagina qualunque</html>")})
        prova("negativo: un altro servizio sulla stessa porta non passa per questo",
              _solleva(lambda: stato(t6), "non e' JSON"))

        # La convenzione di nome regge i caratteri che un titolo porta con se'.
        prova("il nome si ripulisce senza perdere leggibilita'",
              nome_uscita("Intervista: parte 2!", "2026-09-16")
              .endswith("2026-09-16-intervista-parte-2.txt"),
              nome_uscita("Intervista: parte 2!", "2026-09-16"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    larghezza = max(len(n) for n, _, _ in esiti)
    falliti = 0
    for nome, ok, dettaglio in esiti:
        if not ok:
            falliti += 1
        print("  %s  %s%s" % (nome.ljust(larghezza), "ok" if ok else "FALLITO",
                              ("  " + dettaglio) if (dettaglio and not ok) else ""))
    print("")
    print("%d prove, %d fallite." % (len(esiti), falliti))
    return 1 if falliti else 0


def _solleva(f, atteso):
    """Vero se la chiamata solleva un Errore il cui messaggio contiene la stringa attesa."""
    try:
        f()
    except Errore as e:
        return atteso in str(e)
    return False


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("file", nargs="?", help="file audio o video da trascrivere")
    p.add_argument("--nome", help="nome della fonte, che finisce nel nome del file prodotto")
    p.add_argument("--lingua", help="codice della lingua, per esempio it; senza, la rileva il servizio")
    p.add_argument("--modello", help="modello di riconoscimento; senza, usa quello predefinito")
    p.add_argument("--out", help="percorso esatto del file da scrivere")
    p.add_argument("--forza", action="store_true", help="rifa' una trascrizione gia' presente")
    p.add_argument("--attesa", type=int, default=1800,
                   help="secondi di attesa della risposta; un'ora di audio ne chiede parecchi")
    p.add_argument("--stato", action="store_true", help="dice se il servizio risponde")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()

    if a.self_test:
        return self_test()

    trasporto = Trasporto()
    try:
        if a.stato:
            d = stato(trasporto)
            print("il servizio risponde su " + trasporto.base)
            print("protocollo: " + str(d.get("protocol", "non dichiarato")))
            return 0
        if not a.file:
            p.error("serve il file da trascrivere, oppure --stato")
        dest, n = trascrivi(trasporto, a.file, a.nome, lingua=a.lingua, modello=a.modello,
                            attesa=a.attesa, out=a.out, forza=a.forza)
        print("%d caratteri scritti in %s" % (n, dest))
        return 0
    except Errore as e:
        sys.stderr.write(str(e) + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
