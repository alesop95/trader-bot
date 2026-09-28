---
name: senior-researcher
description: >
  Conduce una ricerca tracciabile su un topic tecnico o scientifico e produce un brief con fonti,
  claim verificati, lacune e, se richiesto, un protocollo di benchmark. Accetta paper, repository,
  documentazione ufficiale e URL forniti dall'utente. Usare per stato dell'arte, confronto di
  metodi o progettazione di una prova R&D; non per una semplice domanda fattuale.
---

# Senior researcher

Attivazione: «usa senior-researcher su <topic>», eventualmente con un quesito, URL iniziali e il tipo di output desiderato. Riusa `research-scoping`, `literature-search`, `citation-tracker`, `deep-paper-reading` e `bib-sync` quando il pacchetto li ha istanziati; questa skill coordina il lavoro e amplia il registro alle fonti tecniche non bibliografiche, senza creare una seconda bibliografia.

## Perimetro e metodo

Scrivi nel progetto la domanda, le sotto-domande, il periodo e i tipi di fonte ammessi, le query esatte e la data delle ricerche. Se l'utente chiede uno *stato dell'arte*, chiarisci nel brief se il prodotto è esplorativo, una revisione narrativa strutturata o una revisione sistematica: quest'ultima richiede un protocollo e uno screening documentato, non il solo uso di un agente. Parti dagli URL dell'utente, poi cerca negli indici appropriati e nelle fonti primarie; cerca anche risultati contrari e implementazioni reali. La scelta dei canali è guidata dal topic: OpenAlex, Semantic Scholar, Crossref e archivi disciplinari per paper; repository e release ufficiali per codice; standard e documentazione dei manutentori per interfacce; dataset e schede di benchmark per le misure. Google Scholar può ampliare i candidati, ma non è un prerequisito.

Usa `research-vault/<slug-topic>/` come home persistente. Crea `scope.md` con domanda e protocollo, `sources.md` con una riga per fonte e `brief.md` con la sintesi. In `sources.md` registra almeno ID stabile, tipo, URL canonico, autore/progetto, titolo, data/versione, data di accesso, query o URL iniziale, stato (`candidata`, `metadati-verificati`, `contenuto-verificato`, `scartata`), passaggio/pagina o path/commit pertinente, motivo di inclusione/esclusione e limitazione. Per una fonte bibliografica, usa anche i tre stati di `citation-tracker` nel registro canonico del pacchetto: `metadati-verificati` significa soltanto che la citazione esiste, non che il claim sia provato. Una fonte web senza DOI può essere citata con URL, versione/data e autore identificabile; non inventare un DOI o inserirla nel `.bib` come paper.

Nel `brief.md` separa consenso, dissensi, evidenze deboli e domande aperte. Ogni claim sostanziale deve puntare a una riga di `sources.md` e al passaggio preciso che lo sostiene; segnala come inferenza ciò che combina più fonti. Per numeri e confronti, conserva unità, denominatore, popolazione, configurazione e incertezza dichiarata. Se controlli un paper contro il codice, annota URL e commit del repository, file/funzioni esaminati, versione del paper e ogni divergenza. Il controllo del link e dei metadati precede la lettura; la lettura del contenuto precede la qualifica «verificato» del claim. Non promuovere una sintesi generata da un altro agente a fonte primaria.

Se l'utente chiede una trattazione simil accademica, produci anche `review.md` nello stesso topic: abstract, domanda e metodo di ricerca, criteri di selezione, sintesi tematica, confronto dei risultati, limiti e riferimenti. Indica per ogni sezione se le fonti sono paper, preprint, codice o documentazione tecnica; non trasformare un issue o una pagina di prodotto in evidenza sperimentale. Il `.bib` contiene soltanto voci passate da `citation-tracker` e `bib-sync`; URL tecnici restano nelle note e nei riferimenti web con autore, versione e data. Non chiamare il testo revisione sistematica senza il protocollo e i conteggi di screening richiesti da quel disegno.

## Strumenti opzionali

Consulta la scelta registrata dal gate prima di usare strumenti esterni. Se OpenAlex MCP è connesso, usa `search_works` per la scoperta e conserva la query OQL canonica; `get_work` e `resolve_references` aiutano a controllare identificatori e riferimenti, mentre la prova del claim resta nel contenuto originale. Se PaperQA2 è attivo, interroga solo il corpus e la cache dichiarati per il topic; tratta i suoi passaggi come indizi da verificare nei file originali, annotando documento, pagina e versione. Entrambi alimentano `sources.md` e il registro di `citation-tracker`, senza sostituirli.

Se Feynman è installato e il progetto consente l'uso dei servizi esterni, `feynman lit <topic>`, `feynman deepresearch <topic>` e `feynman audit <paper>` possono produrre candidati, mappe e audit. Registra versione, provider/modello, comando, prompt, data e percorso degli artefatti; importa solo i risultati controllati contro le fonti primarie. `deepresearch` può avere un gate di approvazione proprio: rispettalo. Le sole skill Feynman non installano la CLI né i suoi tool. Non eseguire installatori remoti come parte implicita di questa skill. Per opzioni e compatibilità verifica la documentazione della versione installata.

Per una richiesta di benchmark o di validazione quantitativa, leggi [il protocollo R&D](references/benchmark.md) prima di proporre test, metriche o inferenze. Usa gli strumenti statistici disponibili nel progetto soltanto dopo aver fissato unità, contrasto e piano di analisi. Il brief finale distingue sempre risultati osservati, stime inferenziali e verifiche ancora aperte.
