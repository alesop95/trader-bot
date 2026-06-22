# Formato dei comandi git per esecuzione manuale

> Regola modulare. Definisce come l'agente deve presentare i comandi git (add, commit,
> push) che l'utente esegue manualmente, per garantire la massima copiabilita' su
> qualsiasi sistema operativo e terminale. Vale ogni volta che l'agente fornisce comandi
> git da eseguire a mano.

## Principio

I comandi git restano sempre manuali dell'utente. Quando l'agente li presenta, li scrive
in un formato immediatamente copiabile senza modifiche ne' su Windows PowerShell ne'
su bash Linux: una riga per comando, nessuna sintassi specifica di un solo terminale,
nessun heredoc multi-riga.

## Formato richiesto

Ogni sessione di comandi git si presenta come due blocchi separati: uno per PowerShell
(Windows) e uno per bash (Linux). I blocchi contengono le stesse operazioni nella stessa
sequenza, adattate solo per le differenze di sintassi minime (che nella pratica di
`git add`, `git commit -m` e `git push` sono quasi nessuna).

```powershell
git add "percorso/file-uno" "percorso/file-due" "percorso/file-tre"
git commit -m "Messaggio sintetico del commit"
git push
```

```bash
git add "percorso/file-uno" "percorso/file-due" "percorso/file-tre"
git commit -m "Messaggio sintetico del commit"
git push
```

Se i file da aggiungere sono molti, si usa `git add` con tutti i percorsi sulla stessa
riga, separati da spazio, ciascuno tra doppi apici.

## Messaggio di commit

Il messaggio di commit e' una sola stringa tra doppi apici, al massimo 72 caratteri,
che descrive le modifiche in italiano nella forma "Aggiunte X, Y" oppure "Nuova regola X:
descrizione" oppure "Aggiornato Y: cosa cambia". Se il contesto richiede piu' dettaglio,
lo si scrive nella risposta testuale prima dei comandi, non nel messaggio di commit.

La clausola `Co-Authored-By` si omette quando si usa `-m` su riga singola: il commit
header e' sufficiente.

## Identita' da verificare

Prima di fornire i comandi, l'agente verifica che la configurazione locale del repository
sia corretta (user.name, user.email, remote origin) secondo la regola
`git-identity-and-repo.md`. Se l'identita' locale non e' impostata, propone i comandi di
configurazione prima di quelli di commit.
