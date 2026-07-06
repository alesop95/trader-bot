# Profilo di stack: n8n (workflow automation)

> Regola modulare istanziata dal pacchetto `stack-profiles` come `stack-profile.md`. Prescrive le convenzioni con cui si lavora su questo stack; la descrizione dello stack reale del progetto resta nella scheda `context/STACK.md`.

## Workflow come artefatti versionati

I workflow n8n sono JSON e si trattano come artefatti versionati: si esportano nel repository, si rivedono nei diff come qualsiasi codice, e le modifiche fatte nell'editor visuale si riportano nel repository prima di considerarle concluse. Un workflow che esiste solo nell'istanza n8n e non nel repository non e' recuperabile da un clone e viola il principio di recuperabilita' totale del sistema.

## Credenziali

Le credenziali non entrano mai nel JSON del workflow: vivono nel credential store di n8n, e nel repository restano solo i riferimenti per nome. Vale la stessa igiene dei segreti della sezione 6 di `PROJECT-SYSTEM.md`: prima di committare un workflow esportato si verifica che l'export non contenga token o password in chiaro.

## Nodi custom

I nodi custom seguono la struttura di pacchetto di n8n, con le cartelle `nodes/` e `credentials/`, e si testano con il runner di n8n prima di pubblicarli sull'istanza.

## Documentazione dei flussi

Ogni workflow con effetti verso l'esterno documenta nel `CLAUDE.md`, o nella scheda di contesto pertinente, il trigger che lo avvia, i nodi critici e i side-effect esterni: webhook esposti, chiamate API, scritture su sistemi terzi. Un workflow di automazione e' codice che gira da solo, e cio' che fa da solo dev'essere leggibile senza aprire l'editor.
