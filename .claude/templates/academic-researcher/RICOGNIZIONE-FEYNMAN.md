# Feynman e strumenti aperti per la ricerca assistita

Ricognizione del 25 settembre 2026 per il pacchetto `academic-researcher`. È una fotografia delle interfacce pubbliche, non una prova locale di qualità. Il caso di metodo è `D:\intralino-benchmark`, in particolare `ingestione/VALUTAZIONE_FEYNMAN.md`, `ingestione/PROTOCOLLO_RICERCA.md` e `GUIDA-OPERATIVA-BENCHMARK-SCIENTIFICO.md`. Da quel progetto si trasferiscono protocollo, registro delle evidenze e gate dei claim; nessun dato, risultato o identificativo privato.

## Scelta architetturale

Il pacchetto aveva otto skill `academic-researcher`, una regola sulle citazioni, `research-vault/` e un catalogo di MCP. La nuova skill `senior-researcher` coordina queste capacità per un topic, accetta URL non accademici e aggiunge un protocollo di benchmark. Le fonti accademiche continuano a passare da `citation-tracker` e `bib-sync`; documentazione, repository, standard, dataset e benchmark hanno un registro di provenienza proprio. Il brief usa una matrice claim→fonte→passaggio/commit→limite, così che una citazione bibliografica verificata non venga scambiata per prova del contenuto.

Feynman è una CLI autonoma basata su Pi, non un MCP dichiarato dal progetto. Il README espone `lit`, `deepresearch`, `audit`, `replicate`, `compare`, `draft` e quattro agenti interni (Researcher, Reviewer, Writer, Verifier). Include ricerche su OpenAlex, Semantic Scholar, Crossref, PubMed e altre fonti, accesso web, parsing di documenti e ispezione di repository. I suoi risultati entrano nel flusso come candidati e bozze da verificare, non come certificazione del claim. Il progetto offre un installatore della sola libreria di skill per Codex e repository, ma dichiara che non installa terminale, autenticazione o pacchetti Pi: non equivale all'integrazione della CLI in Claude e Codex. Il pacchetto npm corrente è `@companion-ai/feynman`; il vecchio scope `@advaitpaliwal/feynman` riportato nella valutazione IntraLino del 23 settembre è superato. Il README indica licenza MIT, Node.js almeno 22.22.0 per l'opzione npm e telemetria PostHog attiva per default, disattivabile con `FEYNMAN_TELEMETRY=off`.

Le note di rilascio mostrano cambi di comandi fra versioni: i vecchi `rank`, `paper`, `watch` e `jobs` sono stati rimossi dopo 0.3.49. Perciò si fissano versione e hash prima di un pilota, e si verifica `feynman --help` nella versione installata invece di codificare comandi storici nel template. `deepresearch` ha un gate di approvazione del piano nel proprio runtime. I quattro agenti sono una scomposizione del lavoro, non quattro verifiche indipendenti della verità.

## Tool disponibili e ruolo

| Capacità | Opzione aperta | Impiego nel template | Limite da mantenere visibile |
|---|---|---|---|
| Ricerca trasversale | OpenAlex connector ufficiale, oppure `Academix` già nel catalogo | Candidati, identificatori, citazioni in avanti/indietro, query riproducibili | Metadati e indice non attestano che il testo sostenga un claim; il connector ufficiale richiede un account e usa il relativo budget API |
| Verifica bibliografica | OpenAlex `resolve_references`, Crossref, `refchecker-mcp` già nel catalogo | Titolo, autori, anno, DOI e stato della citazione | Match di record distinto dalla verifica di pagina, tabella e metodo |
| Paper e corpus locale | `PaperQA2`, GROBID e `arxiv-cli` già nel catalogo | Lettura del testo disponibile, estrazione e ricerca nel corpus | Copertura dipende dai PDF accessibili; OCR e parsing richiedono controllo sul documento |
| Libreria e BibTeX | Zotero MCP, Zotero e JabRef già nel catalogo | Gestione delle fonti verificate e validazione finale del `.bib` | La sincronizzazione non valuta la qualità metodologica |
| Indagine multiagente | Feynman CLI | Scoperta, confronto paper/codice, bozze con link | Provider, rete, versione, costi e accuratezza da misurare in un pilota; non è un MCP nativo |
| Fonte tecnica libera | Browser e repository ufficiale, con URL fornito dall'utente | Specifiche, release, codice, dataset, issue e documentazione | Registrare autore, data/versione, commit e passaggio; distinguere documentazione da prova sperimentale |

OpenAlex pubblica un connector MCP ufficiale e open source (MIT) per Claude e Claude Code con `search_works`, `get_work`, `resolve_references` e tracciamento della query. È il primo candidato quando serve un solo accesso bibliografico mantenuto dal fornitore. `Academix` e gli altri MCP comunitari restano alternative o complementi quando servono più indici o funzioni particolari; non collegarli tutti automaticamente. `PaperQA2` lavora su un corpus di documenti forniti o accessibili e non è un motore universale di scoperta dell'intera letteratura.

## Pilota Feynman prima dell'adozione operativa

Il gate propone già Feynman, OpenAlex MCP e PaperQA2 come scelte individuali per progetto. [INTEGRAZIONI-TOOL.md](INTEGRAZIONI-TOOL.md) indica come attivarli in Claude Code e Codex; il pilota qui sotto determina se Feynman diventa il percorso predefinito del progetto dopo l'attivazione.

La valutazione IntraLino ha già fissato un pilota ragionevole, ancora non eseguito: usare topic pubblici, una query di letteratura, un audit paper/codice e un'indagine ampia; conservare prompt, provider/modello, versione, data, durata, output e richieste di rete. Campionare almeno 20 claim fra gli output e, prima di eseguire la prova, fissare la soglia accettabile di citazioni corrette, copertura, tempo umano e traffico osservato. Per ogni claim controllare fonte primaria, passaggio esatto, DOI/URL, commit del codice quando pertinente, esito `supportato/parziale/non supportato` e tempo di verifica. Contare a parte fonti inventate, link rotti e claim senza fonte. Il test va svolto su materiale pubblico e in ambiente isolato con telemetria disabilitata. Solo un esito misurato consente di promuovere Feynman da opzione documentata a strumento predefinito del pacchetto.

## Fonti della ricognizione

[Repository e README Feynman](https://github.com/Companion-Inc/feynman), [package.json Feynman](https://github.com/Companion-Inc/feynman/blob/main/package.json), [release notes Feynman](https://github.com/Companion-Inc/feynman/blob/main/RELEASES.md), [connector OpenAlex ufficiale](https://help.openalex.org/access/connector/), [codice OpenAlex MCP](https://github.com/ourresearch/openalex-mcp-server), [PaperQA2 ufficiale](https://github.com/Future-House/paper-qa), [guida Anthropic a skill, subagent e MCP](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more).
