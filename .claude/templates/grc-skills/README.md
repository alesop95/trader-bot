# grc-skills

<!-- readme-summary: le skill di conformità di Sushegaad per ISO 27001, NIS2, GDPR e altre sei norme, in copia bloccata a una release che il template ricopia ogni mese e l'allineamento porta nei progetti -->

> Pacchetto opzionale del sistema di progetto, settore «Sicurezza informatica e assessment», funzione *Govern* del filone `docs/filone-cybersecurity.md`. Porta nei progetti le skill di conformità della raccolta `Sushegaad/Claude-Skills-Governance-Risk-and-Compliance`, licenza MIT, come copia bloccata a una release che il template aggiorna una volta al mese e l'allineamento propaga. Entrato nel template il 2026-10-27 su richiesta del proprietario, che lo vuole come strumento di progetto per ogni sviluppo che tocchi la conformità.

## Che cosa è la raccolta

Trentasei skill, una per norma o quadro di riferimento: ISO/IEC 27001 nelle edizioni 2013 e 2022, ISO 27701, ISO 42001, SOC 2, NIST CSF, NIST SP 800-53, CIS Controls v8, GDPR, NIS2, DORA, EU AI Act, EU CRA, CSRD, PCI DSS, HIPAA, FedRAMP, CMMC, TPRM e altre di giurisdizioni extraeuropee. Ogni skill è un `SKILL.md` con un ruolo da consulente e auditor della norma, le forme d'uscita per tipo di lavoro (tabella di gap analysis, politica con blocco di controllo del documento, guida al controllo, registro dei rischi, dichiarazione di applicabilità) e una cartella `references/` con i testi di dettaglio, per esempio i 93 controlli dell'Annex A 2022 e la mappatura 2013-2022 nel caso di ISO 27001. Sono soltanto testo: nessuna skill della selezione porta programmi eseguibili, e la scansione del pacchetto lo controlla a ogni aggiornamento.

Il repository dichiara un benchmark dell'89 per cento di risposte corrette con le skill contro il 55 senza, misurato dall'autore sui propri casi in `grc-workspace/`. È un'affermazione della fonte e non una misura di questo sistema: qui non è stata ripetuta. Ogni skill chiude con l'avvertenza che fornisce informazione generale e non consulenza legale, e quell'avvertenza vale anche dentro i progetti.

La raccolta si aggiorna una volta al mese, con una release che riallinea le skill alle norme uscite nel frattempo, e ogni `SKILL.md` porta in testa la data dell'ultima verifica dell'autore. Le release lette il 2026-10-27 sono `v1.9.0` del 2026-09-05, `v2.0.0` del 2026-09-15 e `v2.1.0` del 2026-10-04.

## Che cosa contiene il pacchetto

```
grc-skills/
  README.md             questo documento
  PROVENIENZA.json      tag, commit, data della copia, selezione, data di verifica di ogni skill
  LICENSE-a-monte       la licenza MIT della raccolta, che la copia deve portare con sé
  skills/<nome>/        la copia verbatim di plugins/<nome>/skills/<nome>/ alla release bloccata
  tools/grc-skills.py   stato, aggiornamento, scansione, installazione e verifica
```

La selezione copiata è di nove skill su trentasei, scelte per un'organizzazione europea che lavora verso ISO 27001 e tratta dati personali e sistemi di intelligenza artificiale: `iso27001`, `nis2`, `gdpr-compliance`, `iso27701`, `tprm`, `nist-csf`, `cis-controls`, `iso42001` ed `eu-ai-act`. Pesano 451 KB misurati con `du --apparent-size` sulla cartella del pacchetto, ed è la ragione per cui non sono trentasei: tutto ciò che sta sotto `.claude/templates/` arriva in ogni progetto allineato, e le altre ventisette, quasi tutte di giurisdizioni extraeuropee, varrebbero altri 1,3 MB per progetto senza che nessuno le usi. Una skill si aggiunge alla selezione nel template con `aggiorna --skill`, mai prendendola a mano in un progetto, perché una copia presa a mano l'aggiornamento mensile non la raggiunge.

I file delle skill sono verbatim, con un'eccezione sola: `aggiorna` porta su `example.com` ogni indirizzo email che stia su un dominio reale, perché il template non propaga indirizzi reali e un modello d'informativa a monte ne usa uno come esempio; alla release `v2.1.0` è un indirizzo solo, e lo strumento stampa il conteggio a ogni copia. Per il resto non si correggono qui, neppure per la tipografia: sono in inglese, portano i trattini lunghi e le forme di chi li ha scritti, e una correzione locale verrebbe cancellata dalla copia del mese dopo. Ne discendono tre esclusioni, che lo strumento scrive da sé. `aggiorna` mette in ogni skill copiata il marcatore `.md-unwrap-ignore`, che `md-unwrap` rispetta e che l'allineamento porta con la skill nel progetto. Nel template, `tools/dashes-exclude.txt` e `tools/accents-exclude.txt` escludono l'intera cartella `.claude/templates/grc-skills/skills/` con una riga che finisce con la barra: la forma per cartella è entrata negli strumenti di `fix-typography` con questo pacchetto, perché una copia che si riscrive ogni mese non si può elencare file per file. Nel progetto, `installa` aggiunge la stessa riga per `.claude/skills/<nome>/` agli elenchi di esclusione che trova sotto `tools/`.

## Il ciclo mensile, nel template

Il segnale che esiste una release nuova lo dà `fonti-a-monte.py controlla` all'apertura di ogni sessione del template, dove la raccolta è registrata con il ruolo delle skill e il controllo per release. Da lì il giro è questo.

```
python .claude/templates/grc-skills/tools/grc-skills.py stato
python .claude/templates/grc-skills/tools/grc-skills.py aggiorna --tag <release nuova>
git diff --stat -- .claude/templates/grc-skills
python .claude/templates/tools/fonti-a-monte.py segna github:Sushegaad/Claude-Skills-Governance-Risk-and-Compliance
```

`aggiorna` scarica la release con un clone superficiale in una cartella temporanea, ricopia le skill della selezione, toglie quelle uscite dalla selezione, riscrive `PROVENIENZA.json` con il commit e le date di verifica, ed elenca i file aggiunti, tolti e modificati. Poi passa la scansione sul testo nuovo ed esce con codice diverso da zero se trova un segnale alto: un'istruzione rivolta all'agente invece che al lettore, un comando che scarica ed esegue, una cancellazione ricorsiva, un invio di credenziali, un commento HTML che parla all'assistente, o un file che non sia Markdown. Gli URL e i blocchi di comandi si elencano senza fermare, perché in una skill di conformità un link a una fonte ufficiale è normale ma va visto.

La scansione non sostituisce la lettura. Una skill cambia il comportamento dell'agente in ogni progetto che la usa, quindi il diff dei `SKILL.md` modificati si legge prima di `segna`, e i numeri di questo README, cioè release, date e peso, si ricontano nello stesso giro. Dopo il commit nel template, `allinea-tutti.ps1 -Applica` aggiorna ogni progetto che ha istanziato almeno una skill: è il passo 4 di `allinea-dal-template.py`, che aggiorna le skill opzionali già istanziate e non installa quelle che il progetto non ha scelto.

## Nel progetto

Il gate dei pacchetti lo propone quando il progetto produce, verifica o mantiene documentazione di conformità: un sistema di gestione della sicurezza delle informazioni, una dichiarazione di applicabilità, un registro dei rischi, una valutazione d'impatto privacy, gli obblighi NIS2 o AI Act. Si istanziano solo le skill che servono, perché ogni skill istanziata aggiunge la propria descrizione al carico di ogni sessione.

```
python .claude/templates/grc-skills/tools/grc-skills.py installa iso27001 nis2
python .claude/templates/grc-skills/tools/grc-skills.py verifica
```

`installa` copia la skill da `.claude/templates/grc-skills/skills/<nome>` a `.claude/skills/<nome>`; dove il progetto ha gli adapter per Codex sotto `.agents/skills/`, si rigenerano con lo strumento del progetto. `verifica` dice se le copie istanziate coincidono con quella del template, cioè se l'ultimo allineamento le ha raggiunte, ed esce con codice diverso da zero se una diverge. Una skill istanziata non si modifica nel progetto: le correzioni di dominio, come il perimetro dell'organizzazione o le esclusioni della dichiarazione di applicabilità, stanno nei documenti del progetto che la skill legge, non nella skill.

Dove il progetto usa il pacchetto `anonymization`, le skill istanziate fanno scattare i riscontri bloccanti sugli importi e sulle caselle personali, perché citano sanzioni di legge e indirizzi d'esempio: si dichiarano in `percorsi_esclusi_per_decisione` del file dei pattern privato, un prefisso `.claude/skills/<nome>/` per skill con le sole categorie `IMPORTO` ed `EMAIL PERSONALE` e il motivo, come mostra `patterns.example.json` di quel pacchetto. Nel primo progetto che l'ha adottato i riscontri erano 49, tutti nel testo copiato.

Va aggiunta una voce di permesso, come per gli altri pacchetti che portano strumenti.

```
Bash(python .claude/templates/grc-skills/tools/grc-skills.py:*)
```

## Che cosa costa e come si toglie

La licenza è MIT e la copia porta il file di licenza della raccolta. Non ci sono dipendenze oltre a Python 3 e a git, e nessun dato esce dalla macchina: la rete serve solo a `stato` e ad `aggiorna`, che leggono un repository pubblico. Il costo di contesto è la descrizione di ogni skill istanziata, che entra nel carico di avvio, e il testo della skill e dei suoi riferimenti quando si attiva; la skill `iso27001` con i suoi tre riferimenti misura 33.672 byte.

Si toglie cancellando `.claude/skills/<nome>` per ogni skill istanziata e il suo adapter Codex. La cartella del pacchetto sotto `.claude/templates/` resta, perché appartiene al template e l'allineamento la riscriverebbe.

## Fonti

La raccolta: https://github.com/Sushegaad/Claude-Skills-Governance-Risk-and-Compliance, licenza MIT letta dall'API di GitHub il 2026-10-27, non archiviata, ultimo push del 2026-10-10. Il sito della raccolta: https://sushegaad.github.io/Claude-Skills-Governance-Risk-and-Compliance/. Le skill copiate sono state lette attraverso la scansione del pacchetto, e per intero solo `iso27001/SKILL.md`; i riferimenti delle altre otto non sono stati letti riga per riga, e lo si dichiara invece di lasciarlo supporre.
