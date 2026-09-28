---
name: sync-readme
description: Allinea il README pubblico allo stato reale di un progetto, aggiornando prosa, navigazione, inventario e link quando cambiano codice o documentazione. Usare quando si chiede di aggiornare o verificare il README; non per una semplice modifica a un altro file Markdown.
---

# Sincronizzare il README

Leggi il README e le fonti che governano le affermazioni da aggiornare: codice, catalogo, documenti canonici e modifiche dall'ultima revisione del README. Correggi la prosa solo quando le fonti sostengono la nuova frase; se manca evidenza, segnala l'incertezza. Conserva un percorso breve per chi scopre il progetto, con indice navigabile e link locali utili.

Usa `tools/sync-readme.py --write` dopo gli interventi editoriali, poi `--check`. Nel repository del template il sorgente è `.claude/templates/readme-sync/tools/sync-readme.py` e richiede anche `--bundle` per l'indice dei pacchetti. Lo script aggiorna solo i blocchi marcati: non usarne l'esito come prova che tutta la prosa sia aggiornata.

Controlla il diff e applica la convenzione Markdown del progetto. Lascia `git add`, commit e push all'utente secondo le istruzioni del repository.
