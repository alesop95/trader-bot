#!/usr/bin/env python3
"""Prove dell'installatore di instradamento-modelli, cioe' della parte che
scrive su un file che non e' suo: il settings.json di un account.

Che cosa misurano. La mod ha le sue prove, eseguite con `claude plugin test`;
qui si prova l'altra meta', che e' quella capace di fare danno: una fusione che
perde una chiave preesistente di un settings.json costa all'utente la
configurazione del suo account, e il danno non si vede finche' qualcosa non
smette di funzionare per un'altra ragione apparente. Ogni caso ha quindi la
forma «dopo l'operazione, che cosa c'e' ancora che c'era prima».

Uso: python test-instradamento.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

RADICE = os.path.dirname(os.path.abspath(__file__))
FUSIONE = os.path.join(RADICE, "merge-instradamento-settings.js")
INSTALLATORE_PS = os.path.join(RADICE, "installa-instradamento.ps1")
INSTALLATORE_SH = os.path.join(RADICE, "installa-instradamento.sh")
SEPARATORE = ";" if sys.platform == "win32" else ":"

esiti = []
saltati = []


def verifica(nome, condizione, dettaglio=""):
    esiti.append((nome, bool(condizione), dettaglio))


# Un caso non eseguibile qui si dichiara, non si tace: un caso che sparisce in
# silenzio dal conto sposta la copertura senza che nessuno lo decida, e la riga
# finale direbbe comunque «0 falliti».
def salta(nome, motivo):
    saltati.append((nome, motivo))


def fondi(settings, mod, *extra):
    return subprocess.run(
        ["node", FUSIONE, settings, mod] + list(extra),
        capture_output=True, text=True,
    )


def stato(settings, mod):
    return subprocess.run(
        ["node", FUSIONE, settings, mod, "--stato"],
        capture_output=True, text=True,
    )


def verifica_installatore(radice, mod):
    """Esegue il -Verifica dell'installatore vero su una radice finta.

    Passa dallo script di installazione e non da merge --stato perche' il
    difetto che questi casi coprono stava li' dentro, nel modo in cui lo script
    poneva la domanda, e non nella risposta: una prova sul solo merge resterebbe
    verde anche se l'installatore tornasse a cercare il percorso nel testo.
    """
    if sys.platform == "win32":
        comando = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                   "-File", INSTALLATORE_PS, "-Verifica", "-Radice", radice, "-Mod", mod]
    else:
        comando = ["bash", INSTALLATORE_SH, "--verifica", "--radice", radice, "--mod", mod]
    return subprocess.run(comando, capture_output=True, text=True)


def mod_finta(base):
    cartella = os.path.join(base, "mod-finta")
    os.makedirs(os.path.join(cartella, ".claude-plugin"), exist_ok=True)
    with open(os.path.join(cartella, ".claude-plugin", "plugin.json"), "w", encoding="utf-8") as f:
        json.dump({"name": "mod-finta"}, f)
    return cartella


def leggi(percorso):
    with open(percorso, encoding="utf-8") as f:
        return json.load(f)


def main():
    if shutil.which("node") is None:
        print("SALTATO: Node.js non e' nel PATH, la fusione non e' provabile qui")
        return 0

    base = tempfile.mkdtemp(prefix="prova-instradamento-")
    try:
        mod = mod_finta(base)
        altra = os.path.join(base, "altra-mod")
        os.makedirs(altra, exist_ok=True)
        settings = os.path.join(base, "settings.json")

        # Un settings.json realistico: altre chiavi, un hook, e una cartella di
        # plugin gia' registrata da qualcun altro.
        iniziale = {
            "autoMemoryEnabled": False,
            "permissions": {"allow": ["Bash(ls)"]},
            "hooks": {"SessionEnd": [{"hooks": [{"type": "command", "command": "echo"}]}]},
            "env": {"ALTRA_VARIABILE": "1", "CLAUDE_CODE_PLUGIN_DIRS": altra},
        }
        with open(settings, "w", encoding="utf-8") as f:
            json.dump(iniziale, f, indent=2)

        # 1. Registrazione
        esito = fondi(settings, mod)
        dati = leggi(settings)
        cartelle = dati["env"]["CLAUDE_CODE_PLUGIN_DIRS"].split(SEPARATORE)
        verifica("la registrazione esce con zero", esito.returncode == 0, esito.stderr)
        verifica("la mod risulta registrata", os.path.abspath(mod) in [os.path.abspath(c) for c in cartelle])
        verifica("la cartella di plugin altrui resta", os.path.abspath(altra) in [os.path.abspath(c) for c in cartelle])
        verifica("le altre variabili d'ambiente restano", dati["env"].get("ALTRA_VARIABILE") == "1")
        verifica("le chiavi preesistenti restano", set(iniziale).issubset(set(dati)))
        verifica("l'hook preesistente resta", dati["hooks"]["SessionEnd"][0]["hooks"][0]["command"] == "echo")

        # 2. Idempotenza: una seconda corsa non duplica
        fondi(settings, mod)
        cartelle = leggi(settings)["env"]["CLAUDE_CODE_PLUGIN_DIRS"].split(SEPARATORE)
        quante = len([c for c in cartelle if os.path.abspath(c) == os.path.abspath(mod)])
        verifica("una seconda corsa non duplica la voce", quante == 1, "trovate %d" % quante)

        # 3. Rimozione
        esito = fondi(settings, mod, "--rimuovi")
        dati = leggi(settings)
        cartelle = dati.get("env", {}).get("CLAUDE_CODE_PLUGIN_DIRS", "").split(SEPARATORE)
        verifica("la rimozione esce con zero", esito.returncode == 0, esito.stderr)
        verifica("dopo la rimozione la mod non c'e'", os.path.abspath(mod) not in [os.path.abspath(c) for c in cartelle if c])
        verifica("dopo la rimozione la cartella altrui resta", os.path.abspath(altra) in [os.path.abspath(c) for c in cartelle if c])
        verifica("dopo la rimozione le chiavi restano", set(iniziale).issubset(set(dati)))

        # 4. Un settings.json illeggibile non si sovrascrive
        rotto = os.path.join(base, "rotto.json")
        with open(rotto, "w", encoding="utf-8") as f:
            f.write("{ questo non e JSON")
        esito = fondi(rotto, mod)
        with open(rotto, encoding="utf-8") as f:
            contenuto = f.read()
        verifica("un settings.json illeggibile fa fallire", esito.returncode != 0)
        verifica("un settings.json illeggibile resta intatto", contenuto == "{ questo non e JSON")

        # 5. Una cartella che non e' una mod viene rifiutata
        esito = fondi(settings, altra)
        verifica("una cartella senza plugin.json viene rifiutata", esito.returncode != 0)

        # 6. Un file che non esiste si crea con la sola chiave attesa
        nuovo = os.path.join(base, "nuovo", "settings.json")
        esito = fondi(nuovo, mod)
        dati = leggi(nuovo)
        verifica("su un file nuovo la registrazione riesce", esito.returncode == 0, esito.stderr)
        verifica("il file nuovo contiene solo env", list(dati) == ["env"])

        # 7. Il modo --stato risponde senza scrivere.
        #
        # Il percorso della mod contiene di proposito una barra rovesciata, che
        # su Windows c'e' sempre e altrove quasi mai: dentro il JSON diventa
        # doppia, quindi chi cerca il percorso nel testo grezzo del file non lo
        # trova e dichiara assente una mod registrata. E' il difetto osservato il
        # 2026-10-12, dove -Verifica diceva «NON registrata» su tre account su
        # tre mentre la mod era attiva e stava gia' contando.
        strana = os.path.join(base, "radice\\con-barra")
        os.makedirs(strana, exist_ok=True)
        mod_strana = mod_finta(strana)
        settings_strano = os.path.join(strana, "settings.json")
        with open(settings_strano, "w", encoding="utf-8") as f:
            json.dump({"env": {"CLAUDE_CODE_PLUGIN_DIRS": mod_strana}}, f, indent=2)
        grezzo = open(settings_strano, encoding="utf-8").read()
        verifica("il caso e' significativo: il percorso non compare tale e quale nel file",
                 ("\\" not in mod_strana) or (mod_strana not in grezzo))

        esito = stato(settings_strano, mod_strana)
        verifica("--stato riconosce una mod registrata", esito.returncode == 0, esito.stdout + esito.stderr)
        verifica("--stato lo dice anche a parole", "registrata" in esito.stdout and "non registrata" not in esito.stdout)
        verifica("--stato non scrive nulla",
                 open(settings_strano, encoding="utf-8").read() == grezzo)

        esito = stato(settings_strano, mod)
        verifica("--stato distingue una mod non registrata", esito.returncode == 3, esito.stdout + esito.stderr)

        # Lo stesso percorso scritto in un'altra forma resta lo stesso percorso:
        # la registrazione la puo' aver scritta una versione precedente dello
        # script, o una mano umana. Il confronto e' su percorsi risolti, e su
        # Windows anche indifferente alle maiuscole, non su stringhe.
        deviato = os.path.join(os.path.dirname(mod_strana), ".", os.path.basename(mod_strana)) + os.sep
        if sys.platform == "win32":
            deviato = deviato.upper()
        settings_deviato = os.path.join(strana, "settings-deviato.json")
        with open(settings_deviato, "w", encoding="utf-8") as f:
            json.dump({"env": {"CLAUDE_CODE_PLUGIN_DIRS": deviato}}, f, indent=2)
        verifica("il caso e' significativo: la forma registrata non e' quella cercata",
                 deviato != mod_strana)
        esito = stato(settings_deviato, mod_strana)
        verifica("--stato riconosce lo stesso percorso scritto in un'altra forma",
                 esito.returncode == 0, deviato + " -> " + esito.stdout + esito.stderr)

        esito = stato(os.path.join(base, "non-esiste", "settings.json"), mod)
        verifica("--stato su un file assente risponde non registrata", esito.returncode == 3)

        esito = stato(rotto, mod)
        verifica("--stato su un settings.json illeggibile fallisce", esito.returncode == 1)

        # 8. L'installatore vero, in -Verifica, dice la verita' sulla stessa radice.
        esito = verifica_installatore(strana, mod_strana)
        uscita = esito.stdout + esito.stderr
        verifica("l'installatore in verifica esce con zero", esito.returncode == 0, uscita)
        verifica("l'installatore dichiara registrata una mod registrata",
                 "mod registrata" in uscita, uscita.strip())
        verifica("l'installatore in verifica non scrive il settings.json",
                 open(settings_strano, encoding="utf-8").read() == grezzo)

        # La gemella POSIX non la esercita la piattaforma, la esercita la
        # presenza di bash: su Windows c'e' con Git Bash, e senza questo caso la
        # sua meta' di verifica non sarebbe provata da nessuna parte.
        # Bash su Windows mangia le barre rovesciate degli argomenti: i percorsi
        # gli si passano con le barre in avanti, che accetta.
        def perBash(p):
            return p.replace(chr(92), "/") if sys.platform == "win32" else p

        eseguibile = shutil.which("bash")
        vede = False
        if eseguibile:
            # Su Windows il bash trovato nel PATH puo' essere quello di WSL, che
            # vive in un altro filesystem e non vede i dischi di Windows per
            # questa via. Lo si chiede a lui invece di dedurlo dal nome, perche'
            # qui un caso saltato per errore sembrerebbe superato.
            vede = subprocess.run(
                [eseguibile, "-c", 'test -f "$1"', "_", perBash(INSTALLATORE_SH)],
            ).returncode == 0
        if vede:
            esito = subprocess.run(
                [eseguibile, perBash(INSTALLATORE_SH), "--verifica",
                 "--radice", perBash(strana), "--mod", perBash(mod_strana)],
                capture_output=True, text=True,
            )
            uscita = esito.stdout + esito.stderr
            verifica("la gemella sh dichiara registrata una mod registrata",
                     "mod registrata" in uscita, uscita.strip())
        else:
            salta("la gemella sh dichiara registrata una mod registrata",
                  "nessun bash che veda questo repository" if eseguibile else "bash non e' nel PATH")

        pulita = os.path.join(base, "radice-pulita")
        os.makedirs(pulita, exist_ok=True)
        with open(os.path.join(pulita, "settings.json"), "w", encoding="utf-8") as f:
            json.dump({"theme": "dark"}, f, indent=2)
        esito = verifica_installatore(pulita, mod_strana)
        uscita = esito.stdout + esito.stderr
        verifica("l'installatore dichiara NON registrata una radice pulita",
                 "mod NON registrata" in uscita, uscita.strip())
    finally:
        shutil.rmtree(base, ignore_errors=True)

    falliti = [e for e in esiti if not e[1]]
    for nome, ok, dettaglio in esiti:
        print(("  ok   " if ok else "  FALLITO ") + nome + ((" - " + dettaglio.strip()) if (not ok and dettaglio) else ""))
    for nome, motivo in saltati:
        print("  saltato " + nome + " - " + motivo)
    print("")
    print("%d casi, %d falliti, %d saltati" % (len(esiti), len(falliti), len(saltati)))
    return 1 if falliti else 0


if __name__ == "__main__":
    sys.exit(main())
