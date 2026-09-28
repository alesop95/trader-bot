#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trasforma una corsa del lettore di Reddit in un censimento di fonti, raggruppate per cluster.

Perché esiste
-------------
Il lettore di Reddit produce un grafo: nodi, archi e file su disco sotto `_notes/`, che git
ignora perché è materiale grezzo di terzi. Il registro delle fonti del progetto vuole invece
righe curate, ciascuna con ciò su cui la fonte si può citare e le sigle di lavoro che serve. Fra
le due cose manca un passo, ed è questo: prendere ottocento nodi e novecento archi e renderli un
elenco leggibile, ordinato per argomento, in cui ogni voce dice chi la cita e con che parole.

Il passo è deterministico e per questo sta in un programma invece che in una lettura. La regola
sull'economia del contesto lo prescrive: parsing, normalizzazione, deduplicazione e
raggruppamento sono lavoro da codice, e il salto semantico, cioè decidere il livello di
affidabilità di una fonte e su che cosa la si possa citare, è l'unico che richiede di capire.

Da dove viene il raggruppamento, e perché non lo inventiamo noi
---------------------------------------------------------------
Un post di raccolta ben scritto porta già la propria tassonomia, sotto forma di intestazioni. Il
programma la legge invece di imporne una: ogni collegamento eredita come cluster l'intestazione
numerata che lo contiene e la sotto-intestazione più vicina che lo precede. Il risultato è che i
cluster sono quelli che l'autore della fonte ha scelto, il che ha due vantaggi non ovvi. Il
primo è che restano confrontabili con la fonte, quindi chi verifica può risalire. Il secondo è
che una tassonomia scritta da chi conosce il dominio è quasi sempre migliore di una inventata da
chi lo sta imparando.

Ai collegamenti che compaiono nei commenti e non nel corpo si assegna un cluster proprio, perché
il commento non è il documento e la distinzione fra ciò che l'autore ha organizzato e ciò che i
lettori hanno aggiunto è essa stessa informazione.

La normalizzazione, e il difetto che evita
-------------------------------------------
Lo stesso indirizzo compare in forme diverse: con la coda del pulsante di condivisione, con i
parametri di provenienza, con o senza la barra finale, con o senza lo spezzone di titolo. Senza
normalizzazione la stessa fonte comparirebbe cinque volte nel censimento, e cinque righe che
sembrano cinque fonti sono peggio di una riga mancante, perché gonfiano un conteggio su cui poi
si ragiona.

Uso
---
    python tools/censimento-fonti.py --corsa _notes/fonti/reddit-<sub>-<id>-<data>
    python tools/censimento-fonti.py --corsa <cartella> --out docs/CENSIMENTO-FONTI.md
    python tools/censimento-fonti.py --corsa <cartella> --registro _notes/righe-registro.md
    python tools/censimento-fonti.py --self-test
"""

import argparse
import collections
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# I parametri di coda che non identificano una risorsa ma la provenienza di chi ci arriva. Sono
# gli stessi che il lettore di Reddit toglie, e la ragione per cui vanno tolti anche qui e' che
# questo programma normalizza anche gli indirizzi esterni, che quello classifica soltanto.
PARAMETRI_DI_PROVENIENZA = frozenset([
    "share_id", "si", "feature", "ref", "ref_source", "ref_campaign", "context", "rdt",
    "utm_source", "utm_medium", "utm_name", "utm_term", "utm_content", "utm_campaign",
    "pp", "pli", "usp", "sfnsn", "mibextid",
])

# L'intestazione numerata di primo livello, nella forma che i post di raccolta usano piu' spesso,
# cioe' una riga interamente in grassetto che apre con un numero e una parentesi. Non e' l'unica
# forma possibile e non va trattata come tale: dove l'autore abbia usato intestazioni Markdown
# vere, le si legge con SEZIONE_ATX. Accettarle entrambe costa due righe e evita il difetto
# silenzioso per cui su un post scritto con i cancelletti tutti i collegamenti finiscono nel
# preambolo, cioe' in un cluster solo, e il censimento sembra funzionare mentre non raggruppa.
SEZIONE = re.compile(r"^\*\*(\d+)\)\s*(.+?)\*\*\s*$")
SEZIONE_ATX = re.compile(r"^#{1,3}\s+(.+?)\s*#*\s*$")
# Una sotto-intestazione qualunque, cioe' una riga interamente in grassetto che non e' numerata.
SOTTOSEZIONE = re.compile(r"^\*\*(.+?)\*\*\s*$")
# Un collegamento in forma Markdown, con la sua ancora.
COLLEGAMENTO = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
# Un indirizzo nudo, per i casi in cui l'autore non ha usato la forma con l'ancora.
NUDO = re.compile(r"(?<![(\[])\bhttps?://[^\s)\]<>\"']+")

CLUSTER_COMMENTI = "Commenti al post"
CLUSTER_PREAMBOLO = "Preambolo"


def normalizza(indirizzo):
    """La chiave con cui due indirizzi si confrontano, e sotto cui una fonte compare una volta.

    Toglie i parametri di provenienza, la barra finale e il frammento, e riduce l'host alla
    forma minuscola senza il prefisso delle tre doppie vu. Non tocca il resto del percorso,
    perche' su molti siti due percorsi diversi sono due documenti diversi anche quando si
    somigliano.
    """
    indirizzo = indirizzo.strip().rstrip(".,;:!?")
    indirizzo = indirizzo.split("#", 1)[0]
    if "?" in indirizzo:
        base, coda = indirizzo.split("?", 1)
        tenuti = []
        for pezzo in coda.split("&"):
            if not pezzo:
                continue
            nome = pezzo.split("=", 1)[0]
            if nome in PARAMETRI_DI_PROVENIENZA or nome.startswith("utm_"):
                continue
            tenuti.append(pezzo)
        indirizzo = base + ("?" + "&".join(tenuti) if tenuti else "")
    schema, resto = indirizzo.split("://", 1)
    if "/" in resto:
        host, percorso = resto.split("/", 1)
        percorso = "/" + percorso
    else:
        host, percorso = resto, ""
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    percorso = percorso.rstrip("/")
    return schema.lower() + "://" + host + percorso


def host_di(indirizzo):
    resto = indirizzo.split("://", 1)[1] if "://" in indirizzo else indirizzo
    host = resto.split("/", 1)[0].lower()
    return host[4:] if host.startswith("www.") else host


def corpo_del_post(testo):
    """Il solo corpo del post, cioe' cio' che sta fra l'intestazione e i commenti.

    Il taglio conta: senza di esso i collegamenti dei commenti erediterebbero come cluster
    l'ultima intestazione del corpo, che e' un'attribuzione falsa e non un'approssimazione.
    """
    i = testo.find("\n## Corpo\n")
    if i < 0:
        return ""
    j = testo.find("\n## Commenti", i)
    return testo[i + len("\n## Corpo\n"):(j if j > 0 else len(testo))]


def parte_commenti(testo):
    j = testo.find("\n## Commenti")
    return testo[j:] if j > 0 else ""


def raccogli(testo, cluster_iniziale):
    """I collegamenti di un testo, ciascuno con il cluster in cui cade e la sua ancora.

    Il cluster e' una coppia, cioe' la sezione numerata e la sotto-intestazione piu' vicina, e
    si porta dietro entrambe perche' la sola sotto-intestazione non basta: nel corpo che questo
    programma legge la parola Reddit compare come sotto-intestazione dentro sezioni diverse.
    """
    sezione = cluster_iniziale
    sotto = ""
    fuori = []
    visti_nella_riga = None
    for riga in testo.splitlines():
        m = SEZIONE.match(riga.strip())
        if m:
            sezione = "%s) %s" % (m.group(1), m.group(2).strip())
            sotto = ""
            continue
        m = SEZIONE_ATX.match(riga.strip())
        if m:
            sezione = m.group(1).strip()
            sotto = ""
            continue
        m = SOTTOSEZIONE.match(riga.strip())
        if m and not COLLEGAMENTO.search(riga):
            sotto = m.group(1).strip()
            continue
        visti_nella_riga = set()
        for ancora, url in COLLEGAMENTO.findall(riga):
            visti_nella_riga.add(url)
            fuori.append((sezione, sotto, ancora.strip(), url))
        for url in NUDO.findall(riga):
            if url in visti_nella_riga:
                continue
            # Un indirizzo gia' catturato dalla forma con l'ancora comparirebbe due volte,
            # perche' l'espressione dell'indirizzo nudo non sa di stare dentro una parentesi.
            if any(url in u for _, u in COLLEGAMENTO.findall(riga)):
                continue
            fuori.append((sezione, sotto, "", url))
    return fuori


def censisci(cartella):
    stato = json.loads(io.open(os.path.join(cartella, "mappa.json"), encoding="utf-8").read())
    nodi = {n["chiave"]: n for n in stato["nodi"]}
    seme = stato["seme"]
    percorso_seme = nodi[seme].get("file")
    if not percorso_seme:
        sys.exit("il nodo di partenza non e' stato scaricato: non c'e' un corpo da spogliare")
    testo = io.open(os.path.join(cartella, percorso_seme), encoding="utf-8").read()

    voci = raccogli(corpo_del_post(testo), CLUSTER_PREAMBOLO)
    voci += [(CLUSTER_COMMENTI, s, a, u)
             for _sez, s, a, u in raccogli(parte_commenti(testo), CLUSTER_COMMENTI)]

    # L'esito di ciascun indirizzo, letto dal grafo invece che indovinato. Un nodo di Reddit si
    # ritrova per identificativo, uno esterno per indirizzo normalizzato.
    esito_per_chiave = {}
    for chiave, n in nodi.items():
        if chiave.startswith("web:"):
            esito_per_chiave[normalizza(chiave[4:])] = n
        elif n.get("permalink"):
            esito_per_chiave[normalizza(n["permalink"])] = n

    raggruppate = collections.OrderedDict()
    per_chiave = {}
    for sezione, sotto, ancora, url in voci:
        chiave = normalizza(url)
        gruppo = (sezione, sotto)
        if chiave in per_chiave:
            v = per_chiave[chiave]
            if ancora and ancora not in v["ancore"]:
                v["ancore"].append(ancora)
            if gruppo not in v["gruppi"]:
                v["gruppi"].append(gruppo)
            continue
        nodo = esito_per_chiave.get(chiave)
        # Un identificativo di post si ritrova anche quando il permalink differisce, perche' la
        # forma con lo spezzone di titolo e quella senza sono lo stesso post.
        if nodo is None and "reddit.com/r/" in chiave and "/comments/" in chiave:
            pezzi = chiave.split("/comments/", 1)[1].split("/")
            if pezzi:
                nodo = nodi.get("reddit:" + pezzi[0])
        v = {"url": url, "chiave": chiave, "host": host_di(chiave),
             "ancore": [ancora] if ancora else [], "gruppi": [gruppo],
             "esito": (nodo or {}).get("esito", "non nel grafo"),
             "titolo": (nodo or {}).get("titolo", ""),
             "autore": (nodo or {}).get("autore", ""),
             "file": (nodo or {}).get("file", "")}
        per_chiave[chiave] = v
        raggruppate.setdefault(gruppo, []).append(v)
    return {"seme": seme, "seme_url": stato.get("seme_url", ""), "nodi": len(nodi),
            "archi": len(stato.get("archi", [])), "gruppi": raggruppate,
            "distinte": per_chiave}


# Il livello di affidabilita' per host, secondo la gerarchia che il progetto ospite dichiara nel
# proprio registro delle fonti. Sta qui
# e non nella testa di chi legge per due ragioni. La prima e' che una classificazione fatta a
# mano su centosettantuno voci e' incoerente per costruzione, perche' la stessa fonte ricevera'
# livelli diversi a distanza di venti righe. La seconda e' che scritta qui la si puo' contestare:
# una riga sbagliata si corregge in un posto solo e il censimento si rigenera.
#
# Il livello e' una proprieta' della fonte e non del suo contenuto, quindi vale per host e non per
# indirizzo. Dove un host ospita cose di natura diversa, come un servizio di pagine personali, si
# assegna il livello piu' prudente fra quelli plausibili e la voce va poi guardata a mano.
LIVELLO_PER_HOST = {
    # ATTENZIONE: da sostituire all'istanziazione. Queste voci sono la forma della tabella e non
    # una classificazione di partenza: sono i soli host il cui livello non dipende dal dominio di
    # cui il progetto si occupa. Il resto lo scrive chi conosce il proprio campo, e lo scrive qui.
    #
    # Livello 1: fonte primaria, cioe' chi produce la cosa di cui si parla.
    # Livello 2: riferimenti di dominio. Accurati, non infallibili, e sul dettaglio vanno confermati.
    "en.wikipedia.org": 2, "wikipedia.org": 2,
    # Livello 3: implementazioni, calcolatori, basi di dati e tracciatori. Codice o dati che
    # funzionano sul campo, con dentro anche scelte arbitrarie che non sono specifiche.
    "github.com": 3, "gist.github.com": 3, "gitlab.com": 3,
    # Livello 4: articoli e guide redazionali. Buoni per il perche', non per il come.
    # Livello 5: community. E' il livello predefinito di cio' che questa tabella non nomina.
    "reddit.com": 5, "stackoverflow.com": 5,
}

# Gli host che non ricevono un livello perche' non sono fonti testuali: vanno in una sezione
# propria del registro, e la ragione e' scritta accanto invece di essere sottintesa.
FUORI_LIVELLO = {
    "youtube.com": "canale o video: la fonte citabile e' la trascrizione, non la pagina",
    "youtu.be": "canale o video: la fonte citabile e' la trascrizione, non la pagina",
    "docs.google.com": "foglio di calcolo: va esportato e conservato in locale per essere letto",
    "imgur.com": "immagine o galleria, non testo",
    "x.com": "richiede autenticazione: non recuperabile dagli strumenti di sessione",
}


def livello_di(host):
    if host in FUORI_LIVELLO:
        return None
    return LIVELLO_PER_HOST.get(host, 5)


def righe_per_registro(c):
    """Le righe pronte per il registro delle fonti, una per fonte distinta e ordinate per cluster.

    La descrizione parte dall'ancora che l'autore ha scritto e, quando la corsa ha recuperato il
    titolo vero, li unisce: l'ancora dice a che cosa serve secondo chi la cita, il titolo dice che
    cosa la fonte e'. Le due informazioni non si sostituiscono a vicenda.
    """
    r = []
    for (sezione, sotto), voci in c["gruppi"].items():
        for v in voci:
            liv = livello_di(v["host"])
            ancora = v["ancore"][0] if v["ancore"] else ""
            titolo = v["titolo"] or ""
            if ancora and titolo and ancora.lower() not in titolo.lower():
                desc = "%s. Titolo della fonte: %s" % (ancora, titolo)
            else:
                desc = titolo or ancora or "senza descrizione"
            if v["autore"]:
                desc += ", di %s" % v["autore"]
            r.append({"cluster": sezione + (" / " + sotto if sotto else ""),
                      "livello": liv, "motivo_fuori": FUORI_LIVELLO.get(v["host"], ""),
                      "url": v["url"], "host": v["host"], "descrizione": desc,
                      "esito": v["esito"]})
    return r


def markdown_registro(c):
    """La sezione da incollare nel registro delle fonti, gia' nella sua forma di tabella."""
    righe = righe_per_registro(c)
    fuori = [x for x in righe if x["livello"] is None]
    dentro = [x for x in righe if x["livello"] is not None]
    r = []
    r.append("| Cluster | Liv | Che cosa documenta | URL |")
    r.append("|---|---|---|---|")
    for x in dentro:
        r.append("| %s | %d | %s | %s |" % (x["cluster"].replace("|", "/"), x["livello"],
                                            x["descrizione"].replace("|", "/"),
                                            x["url"].replace("|", "%7C")))
    r.append("")
    r.append("| Cluster | Perché non ha un livello | Che cosa documenta | URL |")
    r.append("|---|---|---|---|")
    for x in fuori:
        r.append("| %s | %s | %s | %s |" % (x["cluster"].replace("|", "/"), x["motivo_fuori"],
                                            x["descrizione"].replace("|", "/"),
                                            x["url"].replace("|", "%7C")))
    return "\n".join(r) + "\n"


def markdown(c, cartella):
    r = []
    r.append("# Censimento delle fonti del post di raccolta sulle collezioni")
    r.append("")
    r.append("> Documento generato da `tools/censimento-fonti.py` a partire dalla corsa "
             "di `tools/fetch-reddit.py` in `%s`, che non entra in git perché è materiale "
             "grezzo di terzi. Si rigenera invece di modificarlo a mano." % cartella.replace("\\", "/"))
    r.append("")
    r.append("Il post di partenza è %s, e il grafo che ne discende ha %d nodi e %d archi. Questo "
             "censimento non è il grafo: è l'elenco dei collegamenti che il post cita "
             "direttamente, deduplicati e raggruppati secondo le intestazioni che l'autore ha "
             "scelto. I cluster sono quindi suoi e non nostri, il che li rende confrontabili con "
             "la fonte." % (c["seme_url"], c["nodi"], c["archi"]))
    r.append("")
    r.append("La colonna dell'esito dice se quella fonte sia stata scaricata dalla corsa, "
             "catalogata con un motivo, oppure non raggiunta perché oltre un tetto. Le tre cose "
             "non si equivalgono e contarle insieme darebbe una copertura apparente più alta di "
             "quella reale.")
    r.append("")
    r.append("| Cluster | Voci |")
    r.append("|---|---|")
    for (sezione, sotto), voci in c["gruppi"].items():
        nome = sezione + (" / " + sotto if sotto else "")
        r.append("| %s | %d |" % (nome.replace("|", "/"), len(voci)))
    r.append("| **totale distinte** | **%d** |" % len(c["distinte"]))
    r.append("")
    for (sezione, sotto), voci in c["gruppi"].items():
        nome = sezione + (" / " + sotto if sotto else "")
        r.append("## " + nome)
        r.append("")
        r.append("| Che cosa è | Indirizzo | Host | Esito nella corsa |")
        r.append("|---|---|---|---|")
        for v in voci:
            desc = v["titolo"] or (v["ancore"][0] if v["ancore"] else "")
            if v["ancore"] and v["titolo"] and v["ancore"][0].lower() not in v["titolo"].lower():
                desc = "%s - %s" % (v["ancore"][0], v["titolo"])
            if v["autore"]:
                desc += " (di %s)" % v["autore"]
            esito = v["esito"]
            if esito.startswith("catalogato"):
                esito = "catalogato"
            r.append("| %s | %s | %s | %s |"
                     % ((desc or "senza descrizione").replace("|", "/"),
                        v["url"].replace("|", "%7C"), v["host"], esito))
        r.append("")
    return "\n".join(r).rstrip("\n") + "\n"


def inventario_completo(cartella):
    """Ogni nodo che il grafo ha visto, a qualunque profondita', con chi lo cita.

    Il censimento per cluster copre i soli collegamenti che il post di partenza cita
    direttamente, perche' quelli sono i soli che ereditano una tassonomia. Il grafo pero' ne
    contiene molti di piu', trovati dentro i post che il primo rinvia, e perderli significherebbe
    che una fonte esiste nella cartella grezza e in nessun file tracciato. Questo inventario e'
    il presidio contro quella perdita: non classifica e non giudica, elenca.
    """
    stato = json.loads(io.open(os.path.join(cartella, "mappa.json"), encoding="utf-8").read())
    archi = collections.defaultdict(list)
    for a in stato.get("archi", []):
        archi[a["a"]].append(a)
    righe = []
    for n in stato["nodi"]:
        chiave = n["chiave"]
        prof = n.get("profondità", n.get("profondita"))
        entranti = archi.get(chiave, [])
        ancore = [a.get("ancora") for a in entranti if a.get("ancora")]
        righe.append({
            "chiave": chiave,
            "tipo": n.get("tipo", ""),
            "profondita": prof if prof is not None else "",
            "esito": n.get("esito", ""),
            "titolo": n.get("titolo") or "",
            "autore": n.get("autore") or "",
            "url": n.get("permalink") or (chiave[4:] if chiave.startswith("web:") else ""),
            "host": host_di(n.get("permalink") or chiave[4:]) if (
                n.get("permalink") or chiave.startswith("web:")) else "reddit.com",
            "citato_da": len(entranti),
            "ancora": ancore[0] if ancore else "",
        })
    righe.sort(key=lambda r: (str(r["profondita"]), r["host"], r["chiave"]))
    return righe


def markdown_inventario(righe):
    r = []
    r.append("## Inventario completo del grafo")
    r.append("")
    r.append("Il censimento per cluster qui sopra copre i soli collegamenti che il post di "
             "partenza cita direttamente, perché quelli sono i soli che ereditano una "
             "tassonomia dall'autore. Il grafo ne contiene molti di più, trovati dentro i post "
             "che il primo rinvia. Questa tabella li elenca tutti senza classificarli, e il suo "
             "scopo è che nessun indirizzo esista nella cartella grezza e in nessun file "
             "tracciato: la cartella grezza non entra in git e sparisce, questo file resta.")
    r.append("")
    per_prof = collections.Counter(str(x["profondita"]) for x in righe)
    per_esito = collections.Counter(
        x["esito"].split(":")[0] for x in righe)
    r.append("Nodi per profondità: " + ", ".join(
        "%s con %d" % (k, v) for k, v in sorted(per_prof.items())) + ".")
    r.append("")
    r.append("Nodi per esito: " + ", ".join(
        "%s con %d" % (k, v) for k, v in sorted(per_esito.items(), key=lambda x: -x[1])) + ".")
    r.append("")
    r.append("| Prof | Tipo | Titolo o ancora | Host | Esito | Citato da | Indirizzo |")
    r.append("|---|---|---|---|---|---|---|")
    for x in righe:
        desc = x["titolo"] or x["ancora"] or ""
        if x["autore"]:
            desc = (desc + ", di " + x["autore"]) if desc else ("di " + x["autore"])
        esito = x["esito"].split(":")[0]
        r.append("| %s | %s | %s | %s | %s | %d | %s |" % (
            x["profondita"], x["tipo"], (desc or "-").replace("|", "/")[:160], x["host"],
            esito, x["citato_da"], (x["url"] or x["chiave"]).replace("|", "%7C")))
    return "\n".join(r) + "\n"


def _sicuro(nome):
    """Un nome di file che Obsidian e il filesystem accettano, ricavato da un titolo di cluster."""
    fuori = []
    for ch in nome:
        fuori.append(ch if (ch.isalnum() or ch in " -_") else "-")
    return re.sub(r"-{2,}", "-", "".join(fuori)).strip(" -")[:80] or "senza-nome"


def scrivi_vault(c, cartella_note, sorgente):
    """Le note collegate per il vault, una per cluster piu' un indice con il grafo.

    Il registro dice che una fonte esiste e su che cosa la si puo' citare; questo dice come le
    fonti si tengono, ed e' il taglio che una tabella non produce. La forma e' quella che il
    progetto usa gia' sotto `docs/fonti/`, cioe' note che si rimandano con i collegamenti a
    doppia quadra, cosicche' aprendo la radice come vault il grafo si navighi invece di leggerlo.

    Il grafo che si disegna non e' quello dei rinvii fra i post, che ha migliaia di archi ed e'
    illeggibile: e' quello fra i cluster e gli host, che ha una lettura sola e la dice subito,
    cioe' quali argomenti poggino su quali sorgenti. Il grafo completo resta in `mappa.json`.
    """
    if not os.path.isdir(cartella_note):
        os.makedirs(cartella_note)
    righe = righe_per_registro(c)
    per_cluster = collections.OrderedDict()
    for x in righe:
        per_cluster.setdefault(x["cluster"], []).append(x)

    scritti = []
    for cluster, voci in per_cluster.items():
        nome = _sicuro(cluster)
        scritti.append((nome, cluster, len(voci)))
        r = ["# " + cluster, ""]
        r.append("> Nota generata da `tools/censimento-fonti.py`. Il cluster non è nostro: "
                 "è l'intestazione che l'autore del post di raccolta ha scelto, e conservarla "
                 "tiene la nota confrontabile con la fonte.")
        r.append("")
        r.append("Torna all'indice: [[indice-fonti]]. Il registro con i livelli è quello "
                 "che il progetto tiene per le proprie fonti.")
        r.append("")
        per_host = collections.Counter(x["host"] for x in voci)
        r.append("Questo cluster ha %d fonti su %d host: %s."
                 % (len(voci), len(per_host),
                    ", ".join("%s con %d" % (h, n) for h, n in per_host.most_common())))
        r.append("")
        r.append("| Liv | Che cosa documenta | Host | URL |")
        r.append("|---|---|---|---|")
        for x in voci:
            liv = str(x["livello"]) if x["livello"] is not None else "-"
            r.append("| %s | %s | %s | %s |"
                     % (liv, x["descrizione"].replace("|", "/"), x["host"],
                        x["url"].replace("|", "%7C")))
        io.open(os.path.join(cartella_note, nome + ".md"), "w",
                encoding="utf-8", newline="\n").write("\n".join(r) + "\n")

    # L'indice, con il grafo fra cluster e host.
    coppie = collections.Counter()
    for x in righe:
        coppie[(x["cluster"], x["host"])] += 1
    host_totali = collections.Counter(x["host"] for x in righe)
    principali = {h for h, _ in host_totali.most_common(12)}

    r = ["# Il corpus delle fonti, come mappa", ""]
    r.append("> Nota generata. È il taglio relazionale del censimento: là c'è l'elenco, qui c'è "
             "come le fonti si tengono. Aprendo la radice del repository come vault Obsidian, i "
             "collegamenti qui sotto diventano un grafo navigabile.")
    r.append("")
    r.append("La sorgente è la corsa in `%s`, e il post di partenza è %s."
             % (sorgente.replace("\\", "/"), c.get("seme_url", "")))
    r.append("")
    r.append("Il grafo disegnato qui non è quello dei rinvii fra i post, che ha oltre millecinque"
             "cento archi ed è illeggibile a occhio: è quello fra i cluster e gli host più "
             "citati, che ha una lettura sola e la dice subito, cioè quali argomenti poggino su "
             "quali sorgenti. Il grafo completo resta in `mappa.json` accanto alla corsa.")
    r.append("")
    r.append("```mermaid")
    r.append("graph LR")
    id_cluster, id_host = {}, {}
    for i, cl in enumerate(per_cluster):
        id_cluster[cl] = "C%d" % i
        r.append('  C%d["%s"]' % (i, cl.replace('"', "'")[:44]))
    for i, h in enumerate(sorted(principali)):
        id_host[h] = "H%d" % i
        r.append('  H%d(("%s"))' % (i, h))
    for (cl, h), n in sorted(coppie.items(), key=lambda x: -x[1]):
        if h in id_host and cl in id_cluster:
            r.append("  %s -->|%d| %s" % (id_cluster[cl], n, id_host[h]))
    r.append("```")
    r.append("")
    r.append("## I cluster")
    r.append("")
    r.append("| Cluster | Fonti | Nota |")
    r.append("|---|---|---|")
    for nome, cluster, n in scritti:
        r.append("| %s | %d | [[%s]] |" % (cluster.replace("|", "/"), n, nome))
    r.append("")
    r.append("## Gli host, e che cosa ciascuno porta")
    r.append("")
    r.append("| Host | Fonti | Cluster in cui compare |")
    r.append("|---|---|---|")
    for h, n in host_totali.most_common():
        cl = sorted({c2 for (c2, h2) in coppie if h2 == h})
        r.append("| %s | %d | %d |" % (h, n, len(cl)))
    io.open(os.path.join(cartella_note, "indice-fonti.md"), "w",
            encoding="utf-8", newline="\n").write("\n".join(r) + "\n")
    return len(scritti) + 1


def markdown_registro_esteso(c, righe_inv):
    """Le righe del registro per le fonti che il post non cita direttamente.

    Esiste perche' il registro delle fonti deve contenere tutte le fonti, non le sole curate. Il censimento e la mappa restano dove sono e
    servono a navigare; qui il registro diventa completo, che e' cio' che rende vera la frase
    scritta in testa a quel file, cioe' che nessuna informazione su una fonte viva soltanto
    altrove.

    Il raggruppamento e' per host e non per cluster, e la ragione e' che queste fonti un cluster
    non ce l'hanno: nessuna intestazione le governa, perche' compaiono dentro il corpo di un post
    che il primo rinviava. L'host e' allora l'unico raggruppamento che non sia inventato.
    """
    citate = set(v["chiave"] for v in c["distinte"].values())
    fuori = [x for x in righe_inv
             if (x["url"] or "").startswith("http") and normalizza(x["url"]) not in citate]
    per_host = collections.OrderedDict()
    for x in sorted(fuori, key=lambda r: (r["host"], str(r["profondita"]), r["url"])):
        per_host.setdefault(x["host"], []).append(x)
    r = []
    for host, voci in sorted(per_host.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        r.append("### " + host + " (%d)" % len(voci))
        r.append("")
        r.append("| Prof | Che cosa documenta | Esito nella corsa | URL |")
        r.append("|---|---|---|---|")
        for x in voci:
            desc = x["titolo"] or x["ancora"] or "senza descrizione"
            if x["autore"]:
                desc += ", di " + x["autore"]
            r.append("| %s | %s | %s | %s |"
                     % (x["profondita"], desc.replace("|", "/")[:200],
                        x["esito"].split(":")[0], x["url"].replace("|", "%7C")))
        r.append("")
    return "\n".join(r) + "\n", len(fuori), len(per_host)


def csv_righe(c):
    r = ["cluster;sottocluster;ancora;indirizzo;host;esito;titolo;autore"]
    for (sezione, sotto), voci in c["gruppi"].items():
        for v in voci:
            r.append(";".join((x or "").replace(";", ",").replace("\n", " ") for x in [
                sezione, sotto, (v["ancore"][0] if v["ancore"] else ""), v["url"],
                v["host"], v["esito"], v["titolo"], v["autore"]]))
    return "\n".join(r) + "\n"


def self_test():
    esiti = []

    def prova(nome, cond, det=""):
        esiti.append((nome, bool(cond), det))

    a = normalizza("https://www.reddit.com/r/X/comments/abc/titolo/?utm_source=share&si=1")
    b = normalizza("https://reddit.com/r/X/comments/abc/titolo")
    prova("le code di provenienza non fanno due fonti di una", a == b, a + " vs " + b)
    prova("il frammento non fa due fonti di una",
          normalizza("https://a.b/c#x") == normalizza("https://a.b/c"), "")
    prova("un parametro che identifica la risorsa si conserva",
          "gid=17" in normalizza("https://docs.google.com/x/edit?gid=17&usp=sharing"),
          normalizza("https://docs.google.com/x/edit?gid=17&usp=sharing"))
    prova("negativo: due percorsi diversi restano due fonti",
          normalizza("https://a.b/c") != normalizza("https://a.b/d"), "")

    corpo = ("**1) Prima**\n\n* [uno](https://a.b/1)\n\n**Sotto**\n\n* [due](https://a.b/2)\n"
             "\n**2) Seconda**\n\n* [tre](https://a.b/3)\n")
    v = raccogli(corpo, "P")
    prova("la sezione numerata apre un cluster", v[0][0] == "1) Prima", str(v[0]))
    prova("la sotto-intestazione si annida nella sezione",
          v[1][0] == "1) Prima" and v[1][1] == "Sotto", str(v[1]))
    prova("una sezione nuova azzera la sotto-intestazione",
          v[2][0] == "2) Seconda" and v[2][1] == "", str(v[2]))
    prova("l'ancora si conserva", v[0][2] == "uno", str(v[0]))

    # L'intestazione Markdown vera, che e' l'altra forma in cui un post di raccolta si organizza.
    # La prova esiste perche' il difetto che copre e' silenzioso: senza il riconoscimento di
    # questa forma il programma non sbaglia un cluster, li perde tutti, e un censimento con un
    # cluster solo sembra il censimento di un post non organizzato invece di un difetto del
    # lettore. Il testo di prova si compone unendo righe invece di scriverlo con le sequenze di
    # escape, perche' un a capo scritto male dentro una prova la fa passare per la ragione
    # sbagliata.
    atx = chr(10).join(["## Prima", "", "* [uno](https://a.b/1)", "",
                        "### Seconda", "", "* [due](https://a.b/2)"])
    w = raccogli(atx, "P")
    prova("l'intestazione Markdown apre un cluster", w[0][0] == "Prima", str(w[0]))
    prova("una intestazione Markdown nuova sostituisce la precedente",
          w[1][0] == "Seconda", str(w[1]))
    prova("negativo: senza intestazioni il cluster resta quello che il chiamante ha passato",
          raccogli("* [z](https://a.b/9)", "P")[0][0] == "P", "")

    # Il controllo negativo che rende utile il taglio fra corpo e commenti: senza di esso i
    # collegamenti dei commenti erediterebbero l'ultima intestazione del corpo.
    testo = "x\n## Corpo\n**1) A**\n* [u](https://a.b/1)\n## Commenti (2)\n* [v](https://a.b/2)\n"
    prova("il corpo si ferma prima dei commenti",
          "a.b/2" not in corpo_del_post(testo), corpo_del_post(testo))
    prova("i commenti si leggono a parte", "a.b/2" in parte_commenti(testo), "")

    # Una riga interamente in grassetto che contiene un collegamento non e' un'intestazione.
    v2 = raccogli("**1) A**\n**[titolo](https://a.b/9)**\n", "P")
    prova("negativo: un collegamento in grassetto non diventa un'intestazione",
          len(v2) == 1 and v2[0][1] == "", str(v2))

    larghezza = max(len(n) for n, _, _ in esiti)
    for nome, ok, det in esiti:
        print("  %-*s  %s%s" % (larghezza, nome, "ok" if ok else "FALLITO",
                                ("  " + det) if (det and not ok) else ""))
    caduti = [n for n, ok, _ in esiti if not ok]
    print("")
    print("%d prove, %d fallite." % (len(esiti), len(caduti)))
    return 1 if caduti else 0


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--corsa")
    p.add_argument("--out", default="CENSIMENTO-FONTI.md",
                   help="dove scrivere il censimento; il progetto decide se tracciarlo")
    p.add_argument("--csv")
    p.add_argument("--registro", help="scrive le righe pronte per il registro delle fonti")
    p.add_argument("--vault", help="cartella delle note collegate per Obsidian")
    p.add_argument("--registro-esteso", help="righe di registro per le fonti non citate dal post")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()

    if a.self_test:
        return self_test()
    if not a.corsa:
        p.error("serve --corsa con la cartella di una corsa del lettore di Reddit")

    c = censisci(a.corsa)
    inventario = inventario_completo(a.corsa)
    testo = markdown(c, a.corsa) + "\n" + markdown_inventario(inventario)
    io.open(a.out, "w", encoding="utf-8", newline="\n").write(testo)
    print("%d fonti distinte in %d cluster, scritte in %s"
          % (len(c["distinte"]), len(c["gruppi"]), a.out))
    if a.csv:
        io.open(a.csv, "w", encoding="utf-8", newline="\n").write(csv_righe(c))
        print("tabella in " + a.csv)
    if a.registro:
        io.open(a.registro, "w", encoding="utf-8", newline="\n").write(markdown_registro(c))
        print("righe per il registro in " + a.registro)
    if a.vault:
        n = scrivi_vault(c, a.vault, a.corsa)
        print("%d note collegate in %s" % (n, a.vault))
    if a.registro_esteso:
        testo2, quante, host = markdown_registro_esteso(c, inventario)
        io.open(a.registro_esteso, "w", encoding="utf-8", newline="\n").write(testo2)
        print("%d fonti su %d host, righe estese in %s" % (quante, host, a.registro_esteso))
    per_host = collections.Counter(v["host"] for v in c["distinte"].values())
    print("")
    print("I dieci host piu' citati:")
    for h, n in per_host.most_common(10):
        print("  %-32s %d" % (h, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
