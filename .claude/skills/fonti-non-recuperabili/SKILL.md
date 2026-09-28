---
name: fonti-non-recuperabili
description: >
  Che cosa fare quando una fonte web esiste ed è rilevante ma non si riesce a leggerla con
  gli strumenti di sessione. Si carica quando un recupero fallisce con 403, con un rinvio
  alla pagina di accesso o con una pagina di verifica anti-bot, quando la fonte sta su
  Reddit o su Discord, quando serve la trascrizione di un video, quando si deve chiedere
  all'utente di procurare un contenuto, e quando si annota nel registro delle fonti una
  voce che non è stata letta. Elenca le vie di recupero in ordine di costo crescente, fra
  cui archivi pubblici di terze parti e la Wayback Machine, distingue le vie legittime da
  quelle vietate, e stabilisce come si etichetta una fonte non letta perché non sembri
  consultata.
---

## Che cosa fa questa skill

La norma sta per intero in `RIFERIMENTO.md`, accanto a questo file, e va letta prima di operare: qui c'è solo la porta d'ingresso. Il principio che la governa è che una fonte che non si riesce a leggere resta una fonte non letta, e non diventa per questo inaffidabile: la distinzione va scritta ogni volta, perché altrimenti il registro delle fonti si riempie di voci che sembrano consultate e un'affermazione finisce per poggiare su un titolo invece che su un contenuto.

## Quando si carica

Si carica al primo recupero fallito, non dopo il quarto, perché la norma serve proprio a non arrendersi al primo errore e a non insistere sulla via sbagliata. I segnali sono un 403, un rinvio alla pagina di accesso, una pagina di verifica del browser restituita con codice di successo, un dominio che il crawler del modello rifiuta, una fonte su Reddit o su Discord, un video di cui serve il parlato, e il momento in cui si sta per scrivere una voce nel registro delle fonti senza averla letta.

## Procedura minima

Si legge `RIFERIMENTO.md` e si percorrono le vie nell'ordine di costo crescente che stabilisce, fermandosi alla prima che funziona: `curl` locale con uno user agent da browser, archivio pubblico di terze parti o Wayback Machine attraverso l'interfaccia CDX, automazione del browser reale dell'utente previo consenso, API ufficiale con credenziali, e come ultima via la richiesta all'utente di procurare il contenuto.

Un avvertimento che la norma documenta e che va applicato sempre: l'esito di un recupero si verifica sul corpo della risposta e non sul codice di stato, perché una pagina di verifica anti-bot arriva con codice di successo e un successo vuoto costa più di un rifiuto, dato che il rifiuto si nota e questo no.

Ciò che proviene da un archivio invece che dalla fonte viva si annota come tale, con la data di archiviazione accanto, perché un archivio ha latenza verso il presente e conserva ciò che l'originale ha cancellato.

## Vincoli

Non si percorrono le vie che la norma dichiara vietate, in particolare il token di un account personale su una piattaforma che lo proibisce. Non si aprono schede nel browser dell'utente senza chiedere prima. Le credenziali stanno in `.env`, che le regole di permesso di questo sistema negano all'agente: il file lo crea l'utente a mano, e la limitazione è voluta e non si aggira. Il materiale procurato dall'utente si salva sotto `_notes/fonti/`, che non è versionato.
