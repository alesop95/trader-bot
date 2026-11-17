#!/usr/bin/env python3
"""Dice quali modelli locali sono raggiungibili da questa macchina, e per quali compiti bastano.

Perche' esiste. Il rilevamento di `rileva.sh` guarda un solo caso: colibri compilato dentro la
macchina, su CPU. Ma un modello locale spesso non sta sulla macchina della sessione: sta in un
servizio Ollama, LM Studio o compatibile OpenAI su un'altra macchina della rete, magari con
una GPU. Il 2026-11-12 il proprietario ha chiesto che l'agente sappia, all'apertura, se un
modello cosi' c'e', e che lo usi come regola di decisione per i compiti a cui basta, invece
di spendere token del modello a pagamento.

Che cosa fa. Interroga in sola lettura gli indirizzi candidati, elenca i modelli che ciascuno
serve, e per ogni modello dice la fascia di compiti a cui e' ragionevole provarlo. Non manda
nessun dato del progetto: chiede soltanto l'elenco dei modelli.

Da dove prende gli indirizzi, in quest'ordine, sommandoli:
  --endpoint URL                 ripetibile
  LLM_LOCALI_ENDPOINT            variabile d'ambiente, indirizzi separati da virgola
  OLLAMA_HOST                    la variabile di Ollama
  ~/.config/llm-locali.txt       un indirizzo per riga, # per i commenti
  i tre indirizzi locali consueti: Ollama 11434, colibri 8000, LM Studio 1234

L'indirizzo di un servizio della propria rete e' un dato della macchina: sta nel file sotto
la cartella dell'utente o in una variabile, mai in un file tracciato del progetto.

La fascia e' una stima e non una misura. Si ricava dal numero di parametri che il servizio
dichiara, o dal nome del modello quando non lo dichiara, con tre soglie scelte a giudizio:
sotto 7 miliardi, fra 7 e 20, oltre 20. Dice da dove cominciare a provare, non che il modello
sia corretto: prima di affidargli un lotto vero si misura con `bench-correttezza.py` su un
lotto piccolo, come prescrive `docs/offload-modello-locale.md`. Nessuna fascia comprende il
lavoro che richiede giudizio: revisione del codice, sicurezza, progettazione.

Uso:
    python tools/rileva-endpoint.py                 elenco leggibile
    python tools/rileva-endpoint.py --json          lo stesso, per uno script
    python tools/rileva-endpoint.py --hook          una riga, esce sempre con zero
    python tools/rileva-endpoint.py --autotest

Esce con 0 se almeno un modello generativo e' raggiungibile, 1 se nessuno, 2 per un errore d'uso.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

CONSUETI = ["http://127.0.0.1:11434", "http://127.0.0.1:8000", "http://127.0.0.1:1234"]
FILE_UTENTE = Path.home() / ".config" / "llm-locali.txt"
FASCE = [
    (20.0, "grande", "bozze di riassunto, estrazione di campi da testi lunghi, classificazione con molte etichette, riscrittura meccanica"),
    (7.0, "medio", "classificazione su etichette chiuse, estrazione di campi da testi brevi, filtro di rilevanza, riassunti di poche righe"),
    (0.0, "piccolo", "filtro di rilevanza e classificazione su poche etichette, con verifica a valle"),
]


def normalizza(indirizzo: str) -> str:
    indirizzo = indirizzo.strip().rstrip("/")
    if not indirizzo:
        return ""
    if not re.match(r"^https?://", indirizzo):
        indirizzo = "http://" + indirizzo
    return re.sub(r"/v1$", "", indirizzo)


def candidati(espliciti: list, ambiente: dict, file_utente: Path, consueti: bool = True) -> list:
    grezzi = list(espliciti)
    grezzi += [x for x in ambiente.get("LLM_LOCALI_ENDPOINT", "").split(",")]
    grezzi.append(ambiente.get("OLLAMA_HOST", ""))
    try:
        for riga in file_utente.read_text(encoding="utf-8-sig").splitlines():
            grezzi.append(riga.split("#", 1)[0])
    except OSError:
        pass
    if consueti:
        grezzi += CONSUETI
    visti, esito = set(), []
    for g in grezzi:
        n = normalizza(g)
        if n and n not in visti:
            visti.add(n)
            esito.append(n)
    return esito


def leggi_json(url: str, attesa: float):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=attesa) as risposta:
        return json.loads(risposta.read(4_000_000).decode("utf-8", "replace"))


def miliardi(nome: str, dichiarato: str = "") -> float | None:
    """Parametri in miliardi, dal campo dichiarato (`7.6B`, `494M`) o dal nome (`qwen3:14b`)."""
    for testo in (dichiarato, nome):
        m = re.search(r"(?<![A-Za-z0-9.])(\d+(?:\.\d+)?)\s*([bBmM])(?![A-Za-z])", testo or "")
        if m:
            valore = float(m.group(1))
            return valore if m.group(2) in "bB" else valore / 1000.0
    return None


def fascia(nome: str, dichiarato: str = "") -> tuple:
    if re.search(r"embed|bge-|e5-|minilm|rerank", nome, re.I):
        return "embedding", "deduplicazione e somiglianza: non genera testo"
    b = miliardi(nome, dichiarato)
    if b is None:
        return "ignota", "dimensione non dichiarata: si misura prima di usarlo"
    for soglia, etichetta, compiti in FASCE:
        if b >= soglia:
            return etichetta, compiti


def interroga(indirizzo: str, attesa: float = 3.0) -> dict:
    """Prova prima l'elenco di Ollama, poi quello compatibile OpenAI."""
    esito = {"indirizzo": indirizzo, "tipo": None, "modelli": [], "errore": None}
    try:
        dati = leggi_json(indirizzo + "/api/tags", attesa)
        if isinstance(dati, dict) and isinstance(dati.get("models"), list):
            esito["tipo"] = "ollama"
            for m in dati["models"]:
                nome = str(m.get("name") or m.get("model") or "")
                dett = m.get("details") or {}
                f, compiti = fascia(nome, str(dett.get("parameter_size") or ""))
                esito["modelli"].append({"nome": nome, "parametri": dett.get("parameter_size"),
                                         "quantizzazione": dett.get("quantization_level"),
                                         "byte": m.get("size"), "fascia": f, "compiti": compiti})
            return esito
    except urllib.error.HTTPError as err:
        esito["errore"] = type(err).__name__
    except (urllib.error.URLError, OSError) as err:
        # Nessuno in ascolto: il secondo elenco costerebbe un'altra attesa per la stessa risposta.
        esito["errore"] = type(err).__name__
        return esito
    except ValueError as err:
        esito["errore"] = type(err).__name__
    try:
        dati = leggi_json(indirizzo + "/v1/models", attesa)
        if isinstance(dati, dict) and isinstance(dati.get("data"), list):
            esito["tipo"], esito["errore"] = "openai", None
            for m in dati["data"]:
                nome = str(m.get("id") or "")
                f, compiti = fascia(nome)
                esito["modelli"].append({"nome": nome, "parametri": None, "quantizzazione": None,
                                         "byte": None, "fascia": f, "compiti": compiti})
    except (urllib.error.URLError, OSError, ValueError) as err:
        esito["errore"] = esito["errore"] or type(err).__name__
    return esito


def generativi(esiti: list) -> list:
    return [(e, m) for e in esiti for m in e["modelli"] if m["fascia"] != "embedding"]


def ospite(indirizzo: str) -> str:
    """Per l'uscita breve: si dice se e' locale o di rete, non l'indirizzo."""
    return "questa macchina" if re.search(r"//(127\.|localhost|\[::1\])", indirizzo) else "un servizio di rete"


def stampa(esiti: list) -> None:
    vivi = [e for e in esiti if e["tipo"]]
    if not vivi:
        print("Nessun servizio di modelli locali risponde fra i %d indirizzi provati." % len(esiti))
        print("Per aggiungerne uno: una riga in %s, oppure LLM_LOCALI_ENDPOINT." % FILE_UTENTE)
        return
    for e in vivi:
        print("%s  (%s, %d modelli)" % (e["indirizzo"], e["tipo"], len(e["modelli"])))
        for m in sorted(e["modelli"], key=lambda x: x["nome"]):
            extra = ", ".join(str(x) for x in (m["parametri"], m["quantizzazione"]) if x)
            print("   %-38s %-9s %s" % (m["nome"][:38], m["fascia"], ("[" + extra + "] ") if extra else "") + m["compiti"])
    print("")
    print("La fascia e' una stima dalla dimensione, non una misura: prima di un lotto vero si prova il")
    print("modello con bench-correttezza.py su un lotto piccolo. Il lotto si manda con offload-lotto.py,")
    print("--base-url <indirizzo>/v1. Revisione del codice, sicurezza e progettazione non si spostano.")


def autotest() -> int:
    import http.server
    import tempfile
    import threading

    esiti = []

    def caso(nome, ok, dettaglio=""):
        esiti.append(ok)
        print(("ok    " if ok else "ROSSO ") + nome + ("" if ok else "  " + str(dettaglio)))

    risposte = {}

    class Finto(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            corpo = risposte.get((self.server.server_port, self.path))
            if corpo is None:
                self.send_response(404)
                self.end_headers()
                return
            dati = json.dumps(corpo).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(dati)

        def log_message(self, *a):
            pass

    server = [http.server.ThreadingHTTPServer(("127.0.0.1", 0), Finto) for _ in range(3)]
    for s in server:
        threading.Thread(target=s.serve_forever, daemon=True).start()
    porte = [s.server_port for s in server]
    risposte[(porte[0], "/api/tags")] = {"models": [
        {"name": "qwen3-coder:30b", "size": 1, "details": {"parameter_size": "30.5B", "quantization_level": "Q4_K_M"}},
        {"name": "llama3.2:3b", "details": {"parameter_size": "3.2B"}},
        {"name": "nomic-embed-text:latest", "details": {"parameter_size": "137M"}},
        {"name": "misterioso", "details": {}}]}
    risposte[(porte[1], "/v1/models")] = {"data": [{"id": "gemma-12b-it"}]}
    try:
        a = interroga("http://127.0.0.1:%d" % porte[0], 2)
        per = {m["nome"]: m["fascia"] for m in a["modelli"]}
        caso("un servizio Ollama si riconosce e si elencano i modelli", a["tipo"] == "ollama" and len(per) == 4, a)
        caso("30 miliardi di parametri: fascia grande", per.get("qwen3-coder:30b") == "grande", per)
        caso("3 miliardi: fascia piccola", per.get("llama3.2:3b") == "piccolo", per)
        caso("un modello di embedding non conta fra i generativi", per.get("nomic-embed-text:latest") == "embedding" and len(generativi([a])) == 3, per)
        caso("senza dimensione dichiarata la fascia e' ignota, non inventata", per.get("misterioso") == "ignota", per)
        b = interroga("http://127.0.0.1:%d" % porte[1], 2)
        caso("un servizio compatibile OpenAI si riconosce dal secondo elenco", b["tipo"] == "openai" and b["modelli"][0]["fascia"] == "medio", b)
        c = interroga("http://127.0.0.1:%d" % porte[2], 2)
        caso("negativo: un servizio che non e' di modelli non produce modelli", c["tipo"] is None and c["modelli"] == [], c)
        server[2].shutdown()
        server[2].server_close()
        d = interroga("http://127.0.0.1:%d" % porte[2], 1)
        caso("negativo: una porta chiusa dichiara l'errore e non modelli", d["tipo"] is None and d["errore"], d)
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "llm.txt"
            f.write_text("# commento\n10.0.0.9:11500   # gpu\nhttp://altro:1234/v1/\n\n", encoding="utf-8")
            c2 = candidati(["http://x:1/"], {"OLLAMA_HOST": "10.0.0.9:11500", "LLM_LOCALI_ENDPOINT": "a:1, b:2"}, f, consueti=False)
            caso("gli indirizzi si sommano, si normalizzano e non si ripetono",
                 c2 == ["http://x:1", "http://a:1", "http://b:2", "http://10.0.0.9:11500", "http://altro:1234"], c2)
            caso("senza file dell'utente restano i tre consueti", candidati([], {}, Path(tmp) / "assente") == CONSUETI)
        caso("parametri dal nome quando il servizio non li dichiara", miliardi("qwen3:14b") == 14.0 and miliardi("phi-3.5-mini") is None, miliardi("qwen3:14b"))
        caso("l'uscita breve non mostra l'indirizzo di rete", ospite("http://10.0.0.9:11500") == "un servizio di rete" and ospite("http://127.0.0.1:8000") == "questa macchina")
    finally:
        for s in server[:2]:
            s.shutdown()
            s.server_close()
    print("%d prove, %d fallite" % (len(esiti), esiti.count(False)))
    return 1 if False in esiti else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--endpoint", action="append", default=[])
    ap.add_argument("--attesa", type=float, default=3.0, help="secondi per indirizzo")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--hook", action="store_true")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()
    if a.autotest:
        return autotest()
    # In parallelo: su Windows una porta locale chiusa non rifiuta subito, e tre attese in fila
    # rendevano l'hook di avvio lungo 12 secondi (misurato il 2026-11-12).
    from concurrent.futures import ThreadPoolExecutor
    indirizzi = candidati(a.endpoint, os.environ, FILE_UTENTE)
    with ThreadPoolExecutor(max_workers=max(1, len(indirizzi))) as gruppo:
        esiti = list(gruppo.map(lambda i: interroga(i, a.attesa), indirizzi))
    gen = generativi(esiti)
    if a.json:
        print(json.dumps(esiti, ensure_ascii=False, indent=2))
    elif a.hook:
        if gen:
            dove = sorted({ospite(e["indirizzo"]) for e, _ in gen})
            fasce = sorted({m["fascia"] for _, m in gen})
            print("modelli locali: %d generativi raggiungibili su %s (fasce: %s). Per il lavoro meccanico a lotti "
                  "si valuta l'offload prima di spendere token: llm-local/tools/rileva-endpoint.py per l'elenco."
                  % (len(gen), " e ".join(dove), ", ".join(fasce)))
        return 0
    else:
        stampa(esiti)
    return 0 if gen else 1


if __name__ == "__main__":
    sys.exit(main())
