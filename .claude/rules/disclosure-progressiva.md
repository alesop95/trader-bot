---
paths:
  - "**/*.{pdf,docx,pptx,xlsx,epub}"
  - "**/_INDEX.md"
---

# Disclosure progressiva su documenti voluminosi

> Regola condizionale: si carica quando l'agente tocca un PDF, un documento d'ufficio o l'indice di una cache documentale, secondo il front matter `paths`. È la sezione omonima di `token-economy.md`, spostata qui il 2026-11-12 per togliere dal carico di avvio un testo che serve solo davanti a un corpus; là resta la prescrizione in breve.

Un corpus documentale è troppo grande per entrare in contesto: cento documenti possono valere oltre un milione di token, e l'ottanta per cento serve come riferimento ricercabile, non come materiale di ragionamento attivo. Invece di caricare tutto, si accede ai documenti per livelli crescenti di dettaglio, scendendo solo dove serve.

Livello 1, scheletro: solo titolo, gerarchia delle intestazioni e conteggi per sezione, una manciata di token per documento. Permette di vedere un'intera cartella in poche decine di migliaia di token e decidere dove guardare.

Livello 2, preview di sezione: per i soli documenti su cui si vuole ragionare, si aggiungono l'incipit e la chiusura di ogni sezione più le entità rilevate, qualche centinaio di token per documento.

Livello 3, sezione completa: lettura puntuale di una sola sezione di un solo documento, attivata solo per rispondere a una domanda precisa.

Operativamente si parte sempre dal Livello 1 sull'intera cartella, si sale al Livello 2 solo sui documenti pertinenti al task, e al Livello 3 solo su richiesta esplicita. Vale per qualsiasi corpus, non solo per i `.docx`.

Il pacchetto opzionale `doc-ingest` ne è l'implementazione di riferimento: converte `.pdf`, `.docx`, `.pptx`, `.xlsx` e `.html` in una cache Markdown con manifest a content-hash e rigenera a ogni corsa lo scheletro di Livello 1 in `_INDEX.md`; i Livelli 2 e 3 restano disciplina di lettura.

Una variante dello stesso principio sposta il corpus non su una cache locale ma su un motore di recupero esterno ancorato alle fonti. Il pacchetto opzionale `notebooklm-bridge` (vedi `templates/notebooklm-bridge/`) tiene il corpus dentro NotebookLM, nel piano gratuito accessibile solo da browser, e in conversazione fa entrare solo una sintesi densa e citata invece del testo grezzo: è un Livello 1 prodotto da un motore che risponde anche a domande mirate senza mai versare le fonti in contesto. Il risparmio è lo stesso della disclosure progressiva, con in più l'ancoraggio alle fonti che riduce le allucinazioni; il costo è che l'accesso resta manuale nel browser, mai un'API a pagamento. Ne discende un dovere in ogni progetto: quando un'analisi deve ragionare su più di una ventina di documenti dell'utente, o oltre la soglia del degrado, con risposte citate, l'agente chiede all'utente se convenga passare per un momento a NotebookLM, e dove il pacchetto manca lo propone con `cerca-pacchetto`. Claude non lo pilota: l'utente lo usa in una finestra privata, senza login né sessioni salvati, e ciò che ne torna resta nel progetto.
