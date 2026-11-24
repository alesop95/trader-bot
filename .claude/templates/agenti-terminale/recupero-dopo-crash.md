# Recupero delle sessioni dopo un crash dei terminali

> Procedura del pacchetto `agenti-terminale`, nata dall'incidente del 2026-11-24 (lezione L-018 di un progetto istanziato) e scritta perché la prossima volta esista prima di servire. Copre il caso in cui il terminale che ospita più sessioni di Claude Code e di Codex si chiude da solo, tutte insieme, e il caso più piccolo di una sola finestra uccisa.

## Che cosa succede, e che cosa resta

Quando una finestra di Windows Terminal si chiude con le sue schede, ogni sessione di Claude Code ancora aperta scatta il proprio hook di fine sessione con il motivo `other`, e i processi di Codex muoiono insieme al loro lanciatore. Fino al 2026-11-24 il wipe trattava quella chiusura come una qualunque e cancellava le trascrizioni in pochi minuti, senza cestino. Nel caso che ha prodotto questa procedura una scorciatoia di sistema che apriva un terminale elevato, premuta più volte, ha fatto chiudere a Windows Terminal tutte le schede: quattro sessioni Claude, una Codex e due servizi in background. Il meccanismo interno del terminale non compare nei registri di Windows ed è rimasto un'inferenza dalla sequenza temporale.

Da allora gli strumenti del pacchetto si comportano così. `session-end-wipe.ps1` cancella soltanto dopo una chiusura voluta, cioè i motivi `clear`, `logout` e `prompt_input_exit`; ogni altro motivo, compreso uno assente, sposta ciò che avrebbe tolto dalla home dell'account in `%USERPROFILE%\quarantena-sessioni\<data>\<ora>-<account>\`, con i percorsi relativi conservati. Se l'hook di una sessione non è partito affatto, il suo `sessions\<pid>.json` resta con il processo morto, e la prima chiusura successiva di un'altra sessione dello stesso account mette in quarantena le sue tracce invece di cancellarle. `Avvia-Codex.ps1` scrive `<radice>\avvii-in-corso\<pid>.json` all'avvio e lo toglie solo all'uscita ordinata; `Pulisci-Codex.ps1` copia in quarantena le sessioni scritte dopo un avvio rimasto orfano, e lo stesso fa quando Codex esce con un codice diverso da zero. Le cartelle di data della quarantena più vecchie di quattordici giorni le toglie la prima chiusura canonica successiva.

Ciò che nessuno strumento recupera sono i minuti fra l'ultima scrittura su disco e il crash, e per una trascrizione presa da una copia shadow anche quelli fra la copia e il crash. Li copre soltanto il file di ripresa del progetto aggiornato a ogni giro, come chiede la regola `chat-non-e-memoria.md`: nell'incidente, i progetti che lo avevano aggiornato da pochi minuti non hanno perso niente, quelli fermi alla mattina sì.

## 1. Subito dopo il crash, prima di chiudere qualunque altra sessione

Si guarda che cosa c'è in quarantena, in sola lettura:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<template>/.claude/templates/agenti-terminale/tools/Riapri-Sessione.ps1" -Origine "$env:USERPROFILE/quarantena-sessioni/<data>"
```

Lo strumento elenca per ogni sessione l'identificativo, l'account, l'ora dell'ultima scrittura, la dimensione e la cartella del progetto letta dalla trascrizione. Se le sessioni attese ci sono, si passa al punto 3. Se mancano, perché il crash è avvenuto su una home in cui il wipe non era ancora aggiornato o perché qualcuno ha lanciato una pulizia forzata, si passa al punto 2 senza chiudere altre sessioni e senza lanciare `Pulisci-Codex.ps1 -Tutto`, che toglierebbe le sessioni Codex da riprendere.

## 2. Recupero dalla copia shadow, se la quarantena non basta

Serve una copia shadow del volume del profilo creata prima del crash: la fa un backup a livello di volume, ed è montata finché il backup è in corso, oppure resta fra le copie di Ripristino configurazione di sistema. Da un PowerShell amministratore aperto da Start, non da una scorciatoia appena modificata:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<template>/.claude/templates/agenti-terminale/tools/Recupera-DaShadow.ps1" -Prima "2026-11-24 13:56" -Elenco
powershell -NoProfile -ExecutionPolicy Bypass -File "<template>/.claude/templates/agenti-terminale/tools/Recupera-DaShadow.ps1" -Prima "2026-11-24 13:56" -Destinazione "D:/recupero-sessioni-<data>"
```

Il primo elenca le copie e dice quale userebbe, cioè la più recente anteriore all'ora data. Il secondo copia le home di Claude e i rollout e gli indici di Codex nella destinazione, che deve stare fuori dalle home degli account e fuori dalla radice degli scratchpad: lo strumento rifiuta una destinazione dentro una di esse. Se non c'è nessuna copia anteriore, resta il ripristino di file dal backup al punto più recente prima del crash. Nella cartella di destinazione conviene scrivere subito, a mano, la tabella dei progetti con l'ora a cui si ferma ogni conversazione e lo stato su disco dopo, perché è da lì che si scrivono i messaggi di ripresa.

## 3. Riavvio, se serve

Se il crash è venuto da una modifica al terminale o alla shell, la si toglie prima di riavviare, e la si riprova dopo con la regola sulle modifiche al terminale di `rules/chiusura-delle-sessioni.md`: una scheda fittizia aperta accanto e nessuna sessione di lavoro attiva. Prima di un riavvio si chiude con `chiudi` ogni progetto che ha un commit pronto, e un backup in corso si lascia finire se la copia shadow serve ancora.

## 4. Ripresa delle sessioni, una alla volta

Ogni sessione si rimette nel suo account e si riapre nello stesso gesto, in una finestra PowerShell normale nuova per ciascuna, perché il wipe conserva soltanto le sessioni aperte: una trascrizione rimessa e lasciata lì sparisce alla prima chiusura di un'altra sessione dello stesso account.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<template>/.claude/templates/agenti-terminale/tools/Riapri-Sessione.ps1" -Origine "<quarantena o destinazione>" -Id <primi otto caratteri>
```

Lo strumento non sovrascrive un file già presente nell'account, rimette anche la cartella dei sottoagenti, legge la cartella del progetto dalla trascrizione e riapre con `Avvia-Claude.ps1` o `Avvia-Codex.ps1`, cioè con la stessa radice, la cassetta e le pulizie di un avvio normale. Con `-SoloRimetti` stampa il comando invece di lanciarlo. L'ordine conta poco, tranne in un caso: le sessioni Codex si riaprono prima di qualunque altra sessione Codex dello stesso account, perché l'uscita di quella le pulirebbe.

Dopo la riapertura si controlla che la conversazione sia davvero quella vecchia, cioè che la sessione mostri i messaggi di prima del crash e non si apra vuota. Il 2026-11-24 quattro riaperture sono partite come sessioni nuove senza che niente lo segnalasse, perché il lanciatore legava `--resume` a un suo parametro invece di passarlo all'agente; il difetto è corretto, ma il controllo costa uno sguardo e chiude anche quelli che non si conoscono.

## 5. Il messaggio di ripresa

A ogni sessione riaperta si dà un messaggio che dice tre cose: che la chiusura è stata un crash e non una chiusura canonica, fino a che ora arriva la conversazione recuperata, e che cosa c'è su disco dopo quell'ora. La sessione non lo sa da sé: la conversazione si ferma all'ultimo scambio salvato, e tutto ciò che è successo dopo, compreso ciò che altre sessioni hanno scritto nel frattempo, sta solo nei file. La forma che ha funzionato:

> Sei stata riaperta dopo un crash dei terminali delle `<ora del crash>`, non dopo una chiusura canonica. La conversazione recuperata si ferma alle `<ora>`. Dopo hai scritto `<file di ripresa e work-log, con le ore>`, e ci sono `<n>` file non committati, fra cui `<i più significativi>`. Rileggili, dimmi che cosa è successo fra le `<ora>` e le `<ora del crash>` e che cosa non risulta da nessuna parte, poi riprendi.

Tre varianti si presentano spesso. Se mentre la sessione era chiusa un'altra ha scritto nella sua memoria, lo si dice con i file e le voci: «mentre eri chiusa ho aggiornato `<file>`: leggilo prima di proseguire». Se la sessione non aveva lavoro in corso il giorno del crash, lo si dice, così non cerca un buco che non c'è. Se la sessione non si può riaprire, se ne apre una nuova nello stesso progetto con lo stesso messaggio senza la prima frase: tutto ciò che serve per riprendere deve stare nei file del progetto, ed è la prova che ci stava davvero.

## 6. Dopo

Quando ogni sessione ha ricostruito il suo buco, la cartella di recupero dalla copia shadow si tiene come archivio dell'incidente o si cancella, dopo aver verificato che nessuna trascrizione rimasta lì sia ancora fuori dall'account. La quarantena si svuota da sé. Nel progetto in cui il crash è nato si registra la lezione, e se la causa è una modifica al terminale la si tratta come una prova fallita: la si toglie e la si riprova secondo la regola.
