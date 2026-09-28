---
covers-paths: ["<percorso/del/file/toccato>", "<altro/percorso>"]
last-verified-commit: <hash del commit corrente>
---

# <Prefisso> <NN> - <titolo che nomina il principio, non il file toccato>

> Documento didattico, scritto per imparare rileggendo il codice reale. Traccia in dettaglio un intervento fatto il <YYYY-MM-DD>, con i riferimenti ai file toccati e il ragionamento dietro ogni scelta. Si affianca al work-log `.claude/memory/progress.md`, che registra il fatto in sintesi; qui si spiega il perché e il come.
>
> Questa scheda è autoconsistente: costruisce i presupposti che servono a capirla senza mandare il lettore a cercarli altrove, nemmeno per le cose semplici. La ripetizione delle basi comuni fra schede diverse non è un difetto da eliminare ma ridondanza voluta, perché chi apre una scheda sta studiando quell'argomento e non deve ricostruire un percorso di lettura.

## Le fondamenta

<che cosa bisogna sapere per capire il resto, costruito da zero e senza dare per scontato nemmeno il semplice. Gli acronimi si spiegano in nota a piè di pagina numerata, non fra parentesi, perché una parentesi interrompe il discorso e una nota no. Questa sezione esiste perché una scheda che presuppone tre concetti non spiegati è una scheda che si legge solo se si sa già.>

## Il problema, partendo da un caso vero

<il caso concreto da cui è nato l'intervento: un difetto osservato, un costo misurato, una modifica che si è rivelata più difficile del previsto. Partire dal caso vero e non dal principio, perché il principio senza il caso non si ricorda.>

Il codice di allora era, in sostanza, questo.

```
<estratto reale del prima, non pseudocodice, accorciato dove serve ma non inventato>
```

<perché quella forma produce la classe di difetti di cui il caso è un esempio. La distinzione da fare esplicitamente: è un difetto strutturale o un errore puntuale? Se è strutturale, dirlo, perché è la ragione per cui non basta correggere il caso.>

## Il principio della soluzione

<l'idea che ribalta la situazione, enunciata come principio generale prima che come modifica a questo codice. Poi la modifica.>

```
<estratto reale del dopo>
```

<perché il principio regge dove l'altro cedeva, e a quale costo: ogni scelta ne ha uno, e una scheda che non lo nomina insegna a scegliere male la prossima volta.>

## Le domande di dosaggio

<le decisioni che il principio non decide da solo: fino a dove applicarlo, che cosa lasciare fuori, quale caso limite si è scelto di non coprire e perché. È la sezione che distingue una spiegazione da una ricetta, e di solito è quella che serve di più a chi rilegge fra sei mesi.>

## Che cosa protegge questa scelta dal tornare indietro

<la prova che cade se qualcuno ripristina la forma vecchia, se esiste; il controllo automatico che la presidia, se esiste; oppure la dichiarazione esplicita che non c'è nulla che la protegga, che è un'informazione e non un'omissione. Vale la regola sulle prove che misurano: una prova che non cadrebbe reintroducendo il difetto non protegge niente.>

## Come si estende

<come applicare lo stesso principio al caso successivo, scritto per chi lo farà fra un anno senza aver partecipato a questa discussione.>

---

[^1]: <acronimo o termine denso spiegato qui, non nel corpo del testo>
