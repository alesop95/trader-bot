# Esercizi del laboratorio, per funzione del NIST CSF 2.0

> Un esercizio per funzione, nell'ordine del percorso di studio (`docs/filone-cybersecurity-percorso.md` del template). Ogni esercizio gira solo dentro la rete isolata del laboratorio e produce un rapporto che separa ciò che lo strumento dichiara da ciò che è stato verificato a mano. I rapporti descrivono debolezze di macchine reali: restano locali, non entrano nel repository, e si anonimizzano con `anonymization` se vanno citati.

## Identify, inventario e vulnerabilità

Obiettivo: sapere che cosa c'è nella rete del laboratorio e che cosa è noto come vulnerabile. Si fa l'inventario dei servizi del bersaglio con Nmap dal contenitore `scanner`, poi una scansione con Greenbone dalla console, e si leggono i risultati in priorità con gli elenchi KEV, EPSS e CVSS. Rapporto: elenco dei servizi trovati, vulnerabilità per gravità, e le tre più urgenti con la ragione.

## Protect, hardening misurato

Obiettivo: misurare quanto è indurito il bersaglio prima e dopo un intervento. Su un bersaglio Windows si usa HardeningKitty in sola verifica contro una baseline; su Linux, Lynis e OpenSCAP. Si applica una categoria di controlli, si rimisura, si registra il delta. Rapporto: punteggio prima, intervento, punteggio dopo, e che cosa non si è toccato e perché.

## Detect, accorgersi di un evento

Obiettivo: vedere nei log un'azione fatta nel laboratorio. Si abilita la raccolta degli eventi sul bersaglio, si compie un'azione oсservabile, e si legge il risultato con Hayabusa o Chainsaw e le regole Sigma. Rapporto: l'azione, la regola che l'ha segnalata, il tempo fra azione e rilevamento.

## Respond, raccogliere le prove

Obiettivo: raccogliere in modo ordinato le prove di un evento sul bersaglio. Si usano gli artefatti di Velociraptor per una raccolta mirata. Rapporto: che cosa si è raccolto, con quale ordine di volatilità, e che cosa serve conservare.

## Recover, rimettere in piedi

Obiettivo: ripristinare il bersaglio da un backup e verificarne l'integrità. Si appoggia ai pacchetti di continuità operativa del template. Rapporto: tempo di ripristino, verifica dell'integrità, differenze rispetto allo stato prima.
