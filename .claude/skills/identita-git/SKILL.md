---
name: identita-git
description: >
  Governa i quattro assi con cui si firma e si pubblica il lavoro: identità git locale
  (user.name e user.email), alias SSH e chiave che il remoto seleziona, account Claude Code
  legato a una directory di configurazione, autenticazione di GitHub CLI. Si carica quando si
  imposta o si verifica l'identità git di un repository, quando si collega, si cambia o si
  verifica il remoto o l'alias SSH, al bootstrap di un repository nuovo, quando un account
  Claude Code risulta cambiato dopo un riavvio o va rifatto il login, quando si autentica o si
  usa `gh`, e prima di consegnare i comandi di un commit se l'identità locale non è stata
  verificata in sessione.
---

## Che cosa fa questa skill

La norma sta per intero in `RIFERIMENTO.md`, accanto a questo file, e va letta prima di operare. Il suo oggetto è la distinzione fra quattro identità che su una stessa macchina convivono e non coincidono: chi firma i commit, quale chiave autentica il push, quale account Claude Code è attivo e quale account usa `gh`. Ciascuna si verifica con un comando proprio, e nessuna risposta implica le altre.

## Quando si carica

Si carica al Passo 0 e al Passo 0.5 dell'inizializzazione e dell'allineamento, al bootstrap di un repository, quando si tocca la configurazione locale o il remoto, quando un push fallisce per permessi, quando `/status` mostra un account diverso da quello atteso, e quando si adotta o si usa GitHub CLI. Prima di consegnare comandi di commit, `git-commands-format.md` chiede di verificare identità locale e remoto: se la verifica non è già stata fatta in sessione, si carica qui.

## Procedura minima

L'identità si imposta sempre a livello locale del repository, mai affidandosi al default globale. Alias, chiave, nome, email e owner non si deducono: si rilevano con `templates/tools/detect-ssh-profiles.py --repo .` e si confermano con l'utente prima di scriverli. La verifica rapida è `git config --local --list` filtrato su `user.`, `remote.` e `core.ssh`, e per l'account Claude `/status`.

## Vincoli

La skill prepara identità locale, `core.sshCommand` e remoto; non esegue `git add`, commit o push, che restano manuali dell'utente. Le impostazioni globali, come `user.useConfigOnly`, si applicano solo su conferma. `gh` non si usa mai per fondere una pull request.
