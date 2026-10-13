# -*- coding: utf-8 -*-
"""Verifica che ogni collegamento scritto nei documenti del progetto sia classificato.

Perché esiste
-------------

Il 2026-10-06, in un progetto istanziato da questo template, il proprietario ha osservato che il progetto dichiarava lette tutte le fonti mentre i collegamenti scritti dentro i suoi stessi documenti, cioè handoff, note, consegne, decisioni e studi, non erano mai stati confrontati con il registro delle fonti, e i collegamenti brevi di condivisione di Reddit, nella forma `/r/<sub>/s/<codice>`, non erano mai stati risolti. Il registro sapeva che cosa aveva letto, ma nessuno sapeva che cosa il progetto citava: un collegamento incollato in un handoff restava fuori da entrambi i conti senza produrre alcun errore. La dichiarazione di completezza era vera per il perimetro dello strumento che la misurava, cioè il registro, e falsa per il progetto.

Che cosa fa
-----------

Estrae ogni indirizzo dai file tracciati con le estensioni di testo e di codice e dalle cartelle non tracciate che la configurazione dichiara, con le sottocartelle da saltare (testi di terzi scaricati, lotti, cloni, output compilato). Esclude i registri stessi, i prefissi tracciati che la configurazione dichiara (tipicamente i modelli del template) e il proprio sorgente, le cui prove scrivono indirizzi apposta. Normalizza ogni indirizzo: toglie gli escape con la barra rovescia, la punteggiatura finale, il punto e virgola dei CSV, i parametri di tracciamento, i prefissi `www.`, `old.`, `np.` e `m.`, il frammento, e abbassa l'host. Riduce un post di Reddit al suo identificativo e un video di YouTube al suo, così che due forme dello stesso contenuto contino come una. Risolve i collegamenti brevi di Reddit seguendo il reindirizzamento, con l'archivio Arctic Shift come seconda via, e tiene i risultati nella cache dichiarata dalla configurazione per non chiederli due volte.

Non sono indirizzi, e non si contano, tre forme che uno strumento scrive senza che indichino una pagina: un modello di formato che lo strumento completa a runtime (un `%` che non introduce una codifica valida, una graffa, un parametro finale vuoto come `?url=`), un nome riservato alla documentazione dalla RFC 2606 e dalla RFC 6761 (`example.org`, `.example`, `.test`, `.invalid`), e un video di YouTube il cui identificativo non ha undici caratteri. Un collegamento breve di Reddit ha un codice di dieci caratteri: un codice di altra lunghezza è un segnaposto. La pagina d'ingresso di un sito, senza percorso, è classificata quando il registro ha già fonti di quel sito.

Poi confronta con le fonti conosciute, cioè i registri di testo e i registri JSON dichiarati dalla configurazione, e con l'elenco delle non fonti, ciascuna con il proprio motivo (endpoint di strumenti, pagine di scaricamento di programmi, il repository stesso, stringhe d'esempio). Una voce di quell'elenco può dichiarare `solo_in`, cioè i file in cui vale: gli indirizzi fittizi delle prove di uno strumento si escludono solo dentro quello strumento, e lo stesso indirizzo scritto in un documento resta non classificato. La chiave `file_dati` elenca i manifesti scaricati che enumerano il contenuto di una fonte già registrata. Un indirizzo che non sta in nessuno di questi è non classificato.

Il perimetro si stampa a ogni corsa, con il numero di file percorsi e i registri letti, perché una dichiarazione di completezza vale per il perimetro dello strumento che la misura e va scritta con quel perimetro.

Configurazione
--------------

Un file JSON, per difetto `tools/verifica-link-progetto.json` sotto la radice; l'esempio commentato sta nel pacchetto del template, `verifica-link-progetto.esempio.json`. Le chiavi che cominciano con un trattino basso sono commenti. Obbligatoria `registri_testo`; le altre hanno un valore di difetto vuoto, salvo `estensioni`.

Uso
---

    python tools/verifica-link-progetto.py                 riepilogo per host
    python tools/verifica-link-progetto.py --check         esce con 1 se c'è un indirizzo non classificato
    python tools/verifica-link-progetto.py --json FILE     scrive i non classificati con i file che li citano
    python tools/verifica-link-progetto.py --senza-rete    non risolve i collegamenti brevi nuovi
    python tools/verifica-link-progetto.py --config FILE   usa un'altra configurazione
    python tools/verifica-link-progetto.py --radice DIR    percorre un'altra radice
    python tools/verifica-link-progetto.py --prova         esegue le prove interne
"""

import argparse
import base64
import collections
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

CONFIG_DIFETTO = os.path.join("tools", "verifica-link-progetto.json")
ESTENSIONI_DIFETTO = (".md", ".txt", ".url", ".py", ".ps1", ".sh", ".json", ".tex", ".bib", ".csv",
                      ".html", ".cs", ".yml", ".yaml", ".toml", ".js", ".cfg", ".ini")
TRACCIAMENTO = {"si", "share_id", "ref", "ref_source", "ref_src", "feature", "fbclid", "gclid",
                "igshid", "context", "rdt", "s", "t", "utm_name", "pp", "ab_channel", "is",
                "dl", "e", "usp", "ouid", "rtpof", "sd"}
# s e t sono parametri di tracciamento solo su questi host; altrove possono identificare la pagina.
TRACCIAMENTO_SOLO = {"s": ("twitter.com", "x.com"), "t": ("twitter.com", "x.com", "youtube.com", "youtu.be"),
                     "pp": ("youtube.com",), "ab_channel": ("youtube.com",), "context": ("reddit.com",),
                     "is": ("youtu.be",), "dl": ("dropbox.com",), "e": ("dropbox.com",),
                     "usp": ("google.com",), "ouid": ("google.com",), "rtpof": ("google.com",),
                     "sd": ("google.com",)}
PREFISSI_HOST = ("www.", "old.", "np.", "new.", "m.")

RE_URL = re.compile(r"https?://(?:\\[_*()\[\]#~.\-]|[^\s<>\"'`|;\]\}\\])+")
# Il codice di un collegamento breve di Reddit ha dieci caratteri: lo dicevano tutte le diciassette
# risoluzioni in cache nel progetto dove lo strumento è nato. Un codice di altra lunghezza è un
# segnaposto, non un breve.
RE_BREVE = re.compile(r"^https?://(?:[a-z0-9.-]*\.)?reddit\.com/(r|u|user)/([^/]+)/s/([A-Za-z0-9]{10})(?![A-Za-z0-9])", re.I)
# Un video di YouTube ha un identificativo di undici caratteri; un indirizzo di video con un
# identificativo di altra lunghezza, o vuoto, non porta a nessun video.
RE_YT_FORMA = re.compile(r"(?:youtube\.com/(?:watch\?(?:[^#]*&)?v=|shorts/|embed/|live/)|youtu\.be/)([^&?/#]*)")
# Un % che non introduce una codifica valida, o una graffa, è il segnaposto di un modello di formato
# (%s, %d, {id}) in uno strumento che costruisce l'indirizzo a runtime: non è una pagina.
RE_MODELLO = re.compile(r"%(?![0-9A-Fa-f]{2})|[{}]")
RE_POST = re.compile(r"/comments/([a-z0-9]{3,10})(?:/|$)", re.I)
RE_REDD_IT = re.compile(r"^https?://(?:www\.)?redd\.it/([a-z0-9]{3,10})/?$", re.I)
RE_YT = re.compile(r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/)|youtu\.be/)([A-Za-z0-9_-]{11})")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


class ErroreConfig(Exception):
    pass


def pulisci(url):
    url = url.replace("\\", "").split("&quot")[0]
    while True:
        prima = url
        url = url.rstrip(".,;:!?*_'\">]}(")
        # Una parentesi chiusa finale appartiene all'indirizzo solo se ne apre una (Wikipedia).
        if url.endswith(")") and url.count(")") > url.count("("):
            url = url[:-1]
        if url == prima:
            return url


def modello(url):
    """Vero se l'indirizzo è un modello che uno strumento completa a runtime, non una pagina.

    Due forme: un segnaposto di formato (un % che non è una codifica valida, o una graffa), e una
    interrogazione che finisce con un parametro senza valore (`?url=`, `?v=`), a cui lo strumento
    accoda l'indirizzo o l'identificativo vero.
    """
    if RE_MODELLO.search(url):
        return True
    if "?" not in url:
        return False
    ultimo = url.split("?", 1)[1].split("#")[0].split("&")[-1]
    # "id=abc==" è un valore con il riempimento base64, non un parametro vuoto.
    return ultimo.endswith("=") and ultimo.count("=") == 1


# Nomi riservati alla documentazione e alle prove dalla RFC 2606 e dalla RFC 6761: non indicano
# nessuna pagina reale, ed è la forma in cui le prove degli strumenti dovrebbero scrivere i loro esempi.
RISERVATI_TLD = (".example", ".test", ".invalid", ".localhost")
RISERVATI_HOST = ("example.com", "example.org", "example.net", "localhost")


def riservato(host):
    return host.endswith(RISERVATI_TLD) or host in RISERVATI_HOST or host.endswith(
        tuple("." + h for h in RISERVATI_HOST))


def host_breve(host):
    host = host.lower().split("@")[-1].split(":")[0]
    for p in PREFISSI_HOST:
        if host.startswith(p) and host.count(".") >= 2:
            host = host[len(p):]
    return host


def chiave(url):
    """La chiave di confronto: post di Reddit e video di YouTube per identificativo, il resto normalizzato."""
    url = pulisci(url)
    if modello(url):
        return None
    m = RE_REDD_IT.match(url)
    if m:
        return "reddit:" + m.group(1).lower()
    m = RE_YT.search(url)
    if m:
        return "youtube:" + m.group(1)
    m = RE_YT_FORMA.search(url)
    if m and len(m.group(1)) != 11:
        return None
    try:
        p = urllib.parse.urlsplit(url)
    except ValueError:
        return None
    host = host_breve(p.netloc)
    if not host or "." not in host or riservato(host):
        return None
    if host == "onedrive.live.com":
        # Un collegamento di condivisione aperto nel browser porta in `redeem` il collegamento breve
        # 1drv.ms da cui è nato, codificato in base64: sono lo stesso documento, e la chiave è quella.
        r = dict(urllib.parse.parse_qsl(p.query)).get("redeem")
        if r:
            try:
                dec = base64.urlsafe_b64decode(r + "=" * (-len(r) % 4)).decode("ascii")
                if dec.startswith("https://1drv.ms/"):
                    return chiave(dec)
            except (ValueError, UnicodeDecodeError):
                pass
    percorso = urllib.parse.unquote(p.path)
    if host.endswith("reddit.com"):
        m = RE_POST.search(percorso)
        if m:
            return "reddit:" + m.group(1).lower()
        percorso = percorso.lower()
    tenuti = []
    for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True):
        kl = k.lower()
        if kl.startswith("utm_"):
            continue
        if kl in TRACCIAMENTO:
            solo = TRACCIAMENTO_SOLO.get(kl)
            if solo is None or any(host.endswith(h) for h in solo):
                continue
        tenuti.append((k, v))
    percorso = percorso.rstrip("/")
    if host == "github.com" and percorso.endswith(".git"):
        percorso = percorso[:-4]
    q = urllib.parse.urlencode(tenuti)
    return host + percorso + ("?" + q if q else "")


def estrai(testo):
    for u in RE_URL.findall(testo):
        yield pulisci(u)


def leggi(radice, percorso):
    try:
        with io.open(os.path.join(radice, percorso), "rb") as f:
            dati = f.read()
    except OSError:
        return ""
    try:
        return dati.decode("utf-8")
    except UnicodeDecodeError:
        # I file .url e le note salvate da Windows sono spesso in cp1252.
        return dati.decode("cp1252", errors="replace")


def carica_json(radice, percorso, difetto):
    if not percorso:
        return difetto
    try:
        with io.open(os.path.join(radice, percorso), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return difetto


def normalizza_config(grezza):
    """Valida la configurazione e la completa con i valori di difetto. Le chiavi `_...` sono commenti."""
    if not isinstance(grezza, dict):
        raise ErroreConfig("la configurazione deve essere un oggetto JSON")
    note = {"registri_testo", "registri_json", "esclusi_tracciati", "estensioni",
            "cartelle_non_tracciate", "non_fonti", "cache_brevi"}
    ignote = sorted(k for k in grezza if not k.startswith("_") and k not in note)
    if ignote:
        raise ErroreConfig("chiavi sconosciute: %s" % ", ".join(ignote))
    if not grezza.get("registri_testo"):
        raise ErroreConfig("manca registri_testo: senza un registro delle fonti non c'è niente con cui confrontare")
    conf = {
        "registri_testo": list(grezza["registri_testo"]),
        "registri_json": list(grezza.get("registri_json") or []),
        "esclusi_tracciati": tuple(grezza.get("esclusi_tracciati") or ()),
        "estensioni": tuple(grezza.get("estensioni") or ESTENSIONI_DIFETTO),
        "cartelle_non_tracciate": [],
        "non_fonti": grezza.get("non_fonti"),
        "cache_brevi": grezza.get("cache_brevi"),
    }
    for c in grezza.get("cartelle_non_tracciate") or []:
        if not isinstance(c, dict) or not c.get("percorso"):
            raise ErroreConfig("ogni voce di cartelle_non_tracciate vuole un percorso")
        conf["cartelle_non_tracciate"].append({
            "percorso": c["percorso"].replace("\\", "/").rstrip("/"),
            "saltate_in_radice": set(c.get("saltate_in_radice") or ()),
            "saltate": set(c.get("saltate") or ()),
            "estensioni": tuple(c.get("estensioni") or conf["estensioni"]),
        })
    return conf


def file_tracciati(radice, usa_git=True):
    """I file tracciati da git; senza git, o fuori da un repository, tutti i file sotto la radice."""
    if usa_git:
        try:
            r = subprocess.run(["git", "ls-files"], cwd=radice, capture_output=True, text=True,
                               encoding="utf-8")
            if r.returncode == 0:
                return [f for f in r.stdout.split("\n") if f]
        except OSError:
            pass
    out = []
    for d, cartelle, nomi in os.walk(radice):
        cartelle[:] = [c for c in cartelle if c != ".git"]
        rel = os.path.relpath(d, radice).replace("\\", "/")
        for n in nomi:
            out.append(n if rel == "." else rel + "/" + n)
    return out


def file_da_scandire(radice, conf, usa_git=True, se_stesso=None):
    radici_nt = [c["percorso"] + "/" for c in conf["cartelle_non_tracciate"]]
    esclusi = set(conf["registri_testo"])
    if se_stesso:
        esclusi.add(se_stesso)
    files = [f for f in file_tracciati(radice, usa_git) if f.endswith(conf["estensioni"])
             and f not in esclusi and not f.startswith(conf["esclusi_tracciati"])
             and not f.startswith(tuple(radici_nt))]
    tracciati = len(files)
    for c in conf["cartelle_non_tracciate"]:
        base = os.path.join(radice, c["percorso"])
        for d, cartelle, nomi in os.walk(base):
            rel = os.path.relpath(d, radice).replace("\\", "/")
            salta = c["saltate"] | (c["saltate_in_radice"] if rel == c["percorso"] else set())
            cartelle[:] = [x for x in cartelle if x not in salta]
            for n in nomi:
                if n.endswith(c["estensioni"]):
                    files.append(rel + "/" + n)
    files = sorted(set(files) - esclusi)
    return files, tracciati


def risolvi_breve(url, senza_rete):
    """Segue il reindirizzamento di un collegamento breve; seconda via Arctic Shift."""
    if senza_rete:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as r:
            finale = r.geturl()
        if RE_POST.search(urllib.parse.urlsplit(finale).path):
            return finale
    except Exception as e:  # un 403 sulla pagina finale porta comunque l'indirizzo
        finale = getattr(e, "url", None) or (e.geturl() if hasattr(e, "geturl") else None)
        if finale and RE_POST.search(urllib.parse.urlsplit(finale).path):
            return finale
    m = RE_BREVE.match(url)
    if m:
        percorso = "/%s/%s/s/%s" % m.groups()
        try:
            q = urllib.parse.urlencode({"paths": percorso})
            req = urllib.request.Request("https://arctic-shift.photon-reddit.com/api/short_links?" + q,
                                         headers={"User-Agent": "verifica-link-progetto"})
            with urllib.request.urlopen(req, timeout=30) as r:
                dati = json.load(r)
            for rec in dati.get("data") or []:
                dest = rec.get("resolved_path")
                if dest:
                    return "https://www.reddit.com" + dest if dest.startswith("/") else dest
        except Exception:
            pass
    return None


def chiave_breve(url):
    m = RE_BREVE.match(pulisci(url))
    return ("breve:/%s/%s/s/%s" % (m.group(1).lower(), m.group(2).lower(), m.group(3))) if m else None


def radice_di_sito_noto(k, host_noti):
    """La pagina d'ingresso di un sito, senza percorso né interrogazione, cita il sito e non una pagina:
    è classificata quando il registro ha già fonti di quel sito."""
    return "/" not in k and "?" not in k and ":" not in k and k.lower() in host_noti


class NonFonti:
    """Gli indirizzi che non sono fonti, dall'elenco dichiarato in configurazione, ciascuno con il motivo.

    Una voce è un indirizzo esatto (`voci`) o un prefisso di chiave (`prefissi`); il valore è il motivo,
    oppure un oggetto con `motivo` e `solo_in`, l'elenco dei file in cui la voce vale. `solo_in` serve
    agli indirizzi fittizi delle prove degli strumenti: lo stesso indirizzo scritto in un documento
    resta non classificato, così che un'esclusione pensata per un file non nasconda un collegamento
    vero altrove.
    """

    def __init__(self, nf, chiavi_di):
        self.voci = []
        for u, v in (nf.get("voci") or {}).items():
            self.voci.append((chiavi_di(u) or {u}, None, self._ambito(v)))
        for p, v in (nf.get("prefissi") or {}).items():
            self.voci.append((None, p.lower(), self._ambito(v)))

    @staticmethod
    def _ambito(v):
        if isinstance(v, dict) and v.get("solo_in"):
            return set(v["solo_in"])
        return None

    def copre(self, ks, f):
        for chiavi, prefisso, ambito in self.voci:
            if ambito is not None and f is not None and f not in ambito:
                continue
            for k in ks:
                if chiavi is not None and k in chiavi:
                    return True
                if prefisso is not None and k.lower().startswith(prefisso):
                    return True
        return False


def analizza(radice, conf, senza_rete, usa_git=True, se_stesso=None):
    """Percorre il perimetro e restituisce i non classificati, i brevi irrisolti e il perimetro stesso."""
    cache = conf["cache_brevi"]
    brevi = carica_json(radice, cache, {})
    # Una voce che non ha più la forma di un breve, per esempio un segnaposto entrato in cache
    # prima che il codice di dieci caratteri fosse richiesto, non è più un breve da risolvere.
    validi = {k: v for k, v in brevi.items() if chiave_breve("https://www.reddit.com" + k[len("breve:"):])}
    stato = {"cambiati": len(validi) != len(brevi)}
    brevi = validi

    def chiavi_di(url):
        ks = set()
        kb = chiave_breve(url)
        if kb:
            ks.add(kb)
            if kb not in brevi:
                ris = risolvi_breve(pulisci(url), senza_rete)
                if ris or not senza_rete:
                    brevi[kb] = ris
                    stato["cambiati"] = True
            if brevi.get(kb):
                ks.add(chiave(brevi[kb]))
            return {k for k in ks if k}
        k = chiave(url)
        return {k} if k else set()

    noti = set()
    for p in conf["registri_testo"]:
        for u in estrai(leggi(radice, p)):
            noti |= chiavi_di(u)
    for p in conf["registri_json"]:
        d = carica_json(radice, p, [])
        for u in (d.keys() if isinstance(d, dict) else d):
            if isinstance(u, str):
                noti |= chiavi_di(u)
    nf = carica_json(radice, conf["non_fonti"], {})
    non_fonti = NonFonti(nf, chiavi_di)
    noti_min = {k.lower() for k in noti}
    host_noti = {k.split("/")[0].split("?")[0] for k in noti_min if ":" not in k.split("/")[0]}
    file_dati = set(nf.get("file_dati") or {})

    files, tracciati = file_da_scandire(radice, conf, usa_git, se_stesso)
    citati = collections.defaultdict(set)
    for f in files:
        if f in file_dati:
            continue
        for u in estrai(leggi(radice, f)):
            ks = chiavi_di(u)
            if not ks:
                continue
            if any(k in noti or k.lower() in noti_min for k in ks):
                continue
            if any(radice_di_sito_noto(k, host_noti) for k in ks):
                continue
            if non_fonti.copre(ks, f):
                continue
            k0 = sorted(ks)[-1]
            citati[(k0, u)].add(f)

    if stato["cambiati"] and cache:
        os.makedirs(os.path.join(radice, os.path.dirname(cache)) or radice, exist_ok=True)
        with io.open(os.path.join(radice, cache), "w", encoding="utf-8") as f:
            json.dump(dict(sorted(brevi.items())), f, ensure_ascii=False, indent=1)
            f.write("\n")

    per_chiave = collections.defaultdict(lambda: [None, set()])
    for (k, u), fs in citati.items():
        per_chiave[k][0] = per_chiave[k][0] or u
        per_chiave[k][1] |= fs
    irrisolti = sorted(k for k, v in brevi.items() if not v and not non_fonti.copre({k}, None))
    perimetro = {"file": len(files), "tracciati": tracciati, "non_tracciati": len(files) - tracciati,
                 "registri": conf["registri_testo"] + conf["registri_json"], "noti": len(noti)}
    return dict(per_chiave), irrisolti, perimetro


def riga_perimetro(per):
    return ("Perimetro: %d file (%d tracciati, %d da cartelle non tracciate), %d indirizzi noti da %d registri."
            % (per["file"], per["tracciati"], per["non_tracciati"], per["noti"], len(per["registri"])))


def prova():
    """Prove interne. Le prime venticinque falliscono sulla versione dello strumento precedente la correzione
    del 2026-10-06 nel progetto d'origine; le ultime provano la configurazione e il perimetro."""
    esiti = []

    def p(nome, cond):
        esiti.append(bool(cond))
        print("%s %s" % ("ok  " if cond else "FALL", nome))

    YT1, YT2, YT3 = "Abcdefghij0", "Bcdefghij_1", "Cdefghij-k2"  # identificativi fittizi a undici caratteri
    p("un segnaposto %s è un modello, non un indirizzo", chiave("https://web.archive.org/web/%sid_/%s") is None)
    p("un segnaposto %d è un modello", chiave("https://a.it/%d") is None)
    p("una graffa è un modello", chiave("https://api.example.org/v1/{id}/x") is None)
    p("un parametro finale vuoto è un modello", chiave("https://archive.org/wayback/available?url=") is None)
    p("una codifica valida non è un modello", not modello("https://example.org/5599-pok%C3%A9mon"))
    p("un dominio riservato alla documentazione non è una pagina", chiave("https://pokemon.example/a") is None
      and chiave("https://example.org/a") is None and chiave("https://sito.test/a") is None)
    p("il riempimento base64 non è un parametro vuoto", not modello("https://example.org/p?id=abc=="))
    p("youtu.be con identificativo corto non è un video", chiave("https://youtu.be/xyz") is None)
    p("watch?v= vuoto non è un video", chiave("https://www.youtube.com/watch?v=") is None)
    p("watch?v=x non è un video", chiave("https://www.youtube.com/watch?v=x") is None)
    p("?si= di condivisione si toglie", chiave("https://youtu.be/%s?si=AbCdEfGh12345678" % YT1) == "youtube:" + YT1)
    p("?is= di condivisione si toglie", chiave("https://youtu.be/%s?is=AbCdEfGh12345678" % YT2) == "youtube:" + YT2)
    BREVE_OD = "/x/c/0/ABC"  # separato dall'host perché la scansione non lo legga come un indirizzo
    p("il redeem di OneDrive si riduce al collegamento 1drv.ms",
      chiave("https://onedrive.live.com/:x:/g/personal/0/X?rtime=1&redeem=" +
             base64.urlsafe_b64encode(("https://1drv.ms" + BREVE_OD).encode()).decode().rstrip("="))
      == chiave("https://1drv.ms" + BREVE_OD))
    p("watch e youtu.be danno la stessa chiave",
      chiave("https://www.youtube.com/watch?v=%s&t=30" % YT3) == chiave("https://youtu.be/" + YT3))
    p("un breve ha un codice di dieci caratteri", chiave_breve("https://www.reddit.com/r/s/s/CODICE1") is None)
    p("un breve vero si riconosce",
      chiave_breve("https://www.reddit.com/r/Sub/s/AbCdE12345") == "breve:/r/sub/s/AbCdE12345")
    p("un post di Reddit si riduce al suo identificativo",
      chiave("https://old.reddit.com/r/X/comments/AbC123/titolo/?utm_source=share") == "reddit:abc123")
    p("la punteggiatura finale si toglie", list(estrai("vedi [x](https://example.org/p).")) == ["https://example.org/p"])
    p("la parentesi di Wikipedia resta", pulisci("https://example.org/wiki/A_(b)") == "https://example.org/wiki/A_(b)")
    nf = NonFonti({"prefissi": {"esempio.it": {"motivo": "prova", "solo_in": ["tools/a.py"]}},
                   "voci": {"https://example.com/o/r": "il repository stesso"}}, lambda u: {u.split("://")[1]})
    p("una voce con ambito vale nel suo file", nf.copre({"esempio.it/x"}, "tools/a.py"))
    p("una voce con ambito non vale in un documento", not nf.copre({"esempio.it/x"}, "docs/b.md"))
    p("una voce senza ambito vale ovunque", nf.copre({"example.com/o/r"}, "docs/b.md"))
    p("la radice di un sito registrato è classificata", radice_di_sito_noto("smogon.com", {"smogon.com"}))
    p("una pagina di un sito registrato no", not radice_di_sito_noto("smogon.com/forums", {"smogon.com"}))
    p("la radice di un sito non registrato no", not radice_di_sito_noto("rotomlabs.net", {"smogon.com"}))

    # Configurazione.
    def rifiuta(grezza):
        try:
            normalizza_config(grezza)
        except ErroreConfig:
            return True
        return False

    p("una configurazione senza registri si rifiuta", rifiuta({"cartelle_non_tracciate": []}))
    p("una chiave sconosciuta si rifiuta, perché un refuso non diventi un perimetro più stretto",
      rifiuta({"registri_testo": ["R.md"], "registri_jsno": ["x.json"]}))
    p("le chiavi con il trattino basso sono commenti", not rifiuta({"_leggimi": "x", "registri_testo": ["R.md"]}))

    # Perimetro, su un progetto costruito in una cartella temporanea e percorso senza git.
    tmp = tempfile.mkdtemp(prefix="verifica-link-")
    try:
        def scrivi(rel, testo):
            pth = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(pth), exist_ok=True)
            with io.open(pth, "w", encoding="utf-8") as f:
                f.write(testo)
        sito = "https://" + "fonte-registrata.org"
        altro = "https://" + "fonte-mai-registrata.org"
        scrivi("SOURCES.md", "- %s/pagina\n- https://www.youtube.com/watch?v=%s\n" % (sito, YT1))
        scrivi("docs/a.md", "Vedi https://youtu.be/%s e %s/pagina/ e %s/articolo.\n" % (YT1, sito, altro))
        scrivi("docs/b.md", "Prova: https://esempio.it/x\n")
        scrivi("_notes/mie/c.md", "Nota con %s/nota\n" % altro)
        scrivi("_notes/scaricati/d.md", "Testo di terzi con %s/terzi\n" % altro)
        scrivi("modelli/e.md", "%s/modello\n" % altro)
        scrivi("tools/strumento.py", "# %s/autoprova\n" % altro)
        scrivi("_notes/non-fonti.json", json.dumps(
            {"prefissi": {"esempio.it": {"motivo": "fittizio", "solo_in": ["tools/altro.py"]}}}))
        conf = normalizza_config({
            "registri_testo": ["SOURCES.md"], "esclusi_tracciati": ["modelli/"],
            "cartelle_non_tracciate": [{"percorso": "_notes", "saltate_in_radice": ["scaricati"]}],
            "non_fonti": "_notes/non-fonti.json"})
        per_chiave, irrisolti, per = analizza(tmp, conf, True, usa_git=False, se_stesso="tools/strumento.py")
        trovati = {v[0] for v in per_chiave.values()}
        p("due forme di un indirizzo registrato contano come registrate",
          not any("fonte-registrata" in u or "youtu" in u for u in trovati))
        p("un indirizzo mai registrato in un documento si trova", altro + "/articolo" in trovati)
        p("un indirizzo in una cartella non tracciata dichiarata si trova", altro + "/nota" in trovati)
        p("una sottocartella saltata non si percorre", altro + "/terzi" not in trovati)
        p("un prefisso escluso non si percorre", altro + "/modello" not in trovati)
        p("lo strumento non legge il proprio sorgente", altro + "/autoprova" not in trovati)
        p("una non fonte con ambito altrove resta non classificata nel documento", "https://esempio.it/x" in trovati)
        p("il perimetro dichiara i file percorsi, registro escluso",
          per["file"] == 4 and per["non_tracciati"] == 2 and per["registri"] == ["SOURCES.md"])
        p("nessun breve senza rete, nessuna cache scritta", not irrisolti and not os.path.exists(
            os.path.join(tmp, "_notes", "link-brevi.json")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("%d prove, %d fallite" % (len(esiti), esiti.count(False)))
    return 0 if all(esiti) else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--senza-rete", action="store_true")
    ap.add_argument("--radice", help="radice del progetto (difetto: la cartella sopra quella dello strumento)")
    ap.add_argument("--config", help="file di configurazione (difetto: %s sotto la radice)" % CONFIG_DIFETTO)
    ap.add_argument("--prova", action="store_true", help="esegue le prove interne e termina")
    a = ap.parse_args()

    if a.prova:
        return prova()
    qui = os.path.dirname(os.path.abspath(__file__))
    radice = os.path.abspath(a.radice or os.path.dirname(qui))
    percorso_conf = a.config or os.path.join(radice, CONFIG_DIFETTO)
    try:
        with io.open(percorso_conf, encoding="utf-8") as f:
            conf = normalizza_config(json.load(f))
    except OSError:
        print("Configurazione non trovata: %s. Si istanzia dall'esempio del pacchetto verifica-link." % percorso_conf)
        return 2
    except (ValueError, ErroreConfig) as e:
        print("Configurazione non valida (%s): %s" % (percorso_conf, e))
        return 2
    se_stesso = os.path.relpath(os.path.abspath(__file__), radice).replace("\\", "/")

    per_chiave, irrisolti, per = analizza(radice, conf, a.senza_rete, se_stesso=se_stesso)
    if a.json:
        with io.open(a.json, "w", encoding="utf-8") as f:
            json.dump({k: {"url": v[0], "file": sorted(v[1])} for k, v in sorted(per_chiave.items())},
                      f, ensure_ascii=False, indent=1)
    if a.check:
        for k, (u, fs) in sorted(per_chiave.items()):
            print("%s\n    citato in: %s" % (u, ", ".join(sorted(fs))))
        for k in irrisolti:
            print("collegamento breve non risolto: %s" % k)
        print(riga_perimetro(per))
        if per_chiave or irrisolti:
            print("%d indirizzi non classificati, %d brevi non risolti." % (len(per_chiave), len(irrisolti)))
            return 1
        print("Tutti gli indirizzi citati sono classificati.")
        return 0
    host = collections.Counter(k.split("/")[0] for k in per_chiave)
    print(riga_perimetro(per))
    print("%d indirizzi non classificati, %d brevi non risolti" % (len(per_chiave), len(irrisolti)))
    for h, c in host.most_common():
        print("%5d %s" % (c, h))
    return 0


if __name__ == "__main__":
    sys.exit(main())
