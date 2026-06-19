# Identita git e bootstrap del repository

> Regola modulare. Definisce come scegliere l'identita git con cui si commetteranno e
> pusheranno le modifiche, come collegare il repository locale a GitHub tramite l'alias SSH
> corretto, e come proteggersi dal commit involontario con l'identita sbagliata su una macchina
> condivisa. Il commit e il push restano sempre operazioni manuali dell'utente: questa regola e
> la skill di inizializzazione preparano la configurazione, non committano e non pushano mai.

## Concetto

L'identita git, ovvero la coppia `user.name` e `user.email` con cui git firma i commit, e
indipendente dall'account Claude Code e dalla chiave SSH[^1] usata per autenticarsi a GitHub.
Su una stessa macchina possono convivere piu identita: tipicamente una di lavoro e una
personale. Il rischio concreto su un computer aziendale e committare un progetto personale con
l'email di lavoro per distrazione, o viceversa. La regola e impostare sempre l'identita a
livello locale di repository, cosi che ogni repo porti la firma giusta a prescindere dal
default globale.

## Profili disponibili su questa macchina

I profili si ricavano dagli alias host definiti in `C:\Users\Utente\.ssh\config`. Ogni alias
fissa quale chiave usare verso `github.com`, e va abbinato all'identita corrispondente.

Profilo di lavoro: alias SSH `github-corp`, chiave `id_ed25519_corp`, identita `user.name`
asopranzi e `user.email` asopranzi@intrawelt.com, organizzazione Intrawelt-SaaS. E il profilo
con cui questo repository e gia configurato.

Profilo personale: alias SSH `github-personal`, chiave `id_ed25519_personal`, identita
`user.name` alesop95 e `user.email` alessio.sopranzi.95@gmail.com, utente GitHub alesop95.

L'alias nudo `github.com` punta alla chiave di lavoro. La convenzione dei nomi degli alias,
`github-personal` per l'identita personale e `github-corp` per quella di lavoro, e generale e si
puo adottare identica su qualsiasi macchina, cosi che la stessa logica di selezione del profilo
valga ovunque. I valori concreti dietro ogni alias, cioe il percorso della chiave, lo `user.name`
e lo `user.email`, sono invece specifici della macchina e su un altro ambiente vanno riletti dal
relativo `~/.ssh/config` senza inventarli.

## Protezione globale dal commit con identita sbagliata

Una sola impostazione globale, da fare una volta per macchina, fa si che git rifiuti di
committare in un repository dove non e stata impostata l'identita locale.

```bash
git config --global user.useConfigOnly true
```

Con questa impostazione git non ripiega mai sull'email globale: se il repo non ha
`user.email` locale, il commit viene rifiutato finche non lo si imposta esplicitamente. Questo
elimina il commit accidentale con l'email di lavoro mentre si sviluppa con identita personale.
Essendo una modifica globale, va eseguita solo dopo conferma dell'utente.

## Bootstrap di un repository nuovo

Dalla cartella del progetto, l'inizializzazione di un repo nuovo e l'aggancio al remoto GitHub
seguono questa sequenza. La parte di identita e remoto e quella che la skill prepara; il primo
commit e il push li esegue l'utente.

```bash
cd "<path cartella>"

# Inizializza il repo e nomina main il branch di default
git init
git branch -M main

# Forza l'OpenSSH di sistema e l'identita SOLO per questo repo (Windows)
git config --local core.sshCommand "C:/Windows/System32/OpenSSH/ssh.exe"
git config --local user.name "alesop95"
git config --local user.email "alessio.sopranzi.95@gmail.com"

# Collega il remoto tramite l'alias SSH personale
git remote add origin git@github-personal:alesop95/<nome repo>.git
```

L'alias `github-personal` e definito in `C:\Users\Utente\.ssh\config` e usa la chiave personale
`id_ed25519_personal`, quindi il remoto `git@github-personal:alesop95/<nome repo>.git` punta a
`github.com/alesop95/<nome repo>` con quella chiave. Per il profilo di lavoro si sostituiscono
identita e alias con quelli `github-corp` e l'owner con l'organizzazione di destinazione.

Differenza per sistema operativo: su Windows si forza `core.sshCommand` all'eseguibile OpenSSH
indicato perche git per Windows porta un proprio `ssh` che potrebbe non leggere lo stesso
config; su Linux questo passaggio e di norma superfluo, perche `ssh` di sistema e gia sul PATH
e legge `~/.ssh/config`, quindi si omette `core.sshCommand` oppure lo si imposta a `ssh`.

## Verifica della configurazione

Dopo aver impostato identita e remoto, verificare che tutto sia coerente.

```powershell
# Windows PowerShell
git config --local --list | Select-String "user\.|remote\.|core\.ssh"
```

```bash
# Linux / bash
git config --local --list | grep -E "user\.|remote\.|core\.ssh"
```

Test opzionale della connessione SSH verso l'alias scelto.

```bash
ssh -T git@github-personal
```

## Primo commit, push e caso del repo con README

Le operazioni seguenti sono dell'utente, non dell'agente.

```bash
git add .
git commit -m "Initial commit: <note del primo commit>"
git push -u origin main
```

Subito dopo il primo commit conviene confermare con quale identita e stato firmato.

```bash
git log -1 --format="%an <%ae>"
```

Se il repository su GitHub e stato creato con un README o una licenza automatica, esiste gia un
commit remoto e il push diretto verrebbe rifiutato. Si allinea con un rebase prima di pushare.

```bash
git pull origin main --rebase
git push -u origin main
```

Il rebase prende il commit gia presente su GitHub, ad esempio il README generato alla creazione
del repo, e vi colloca sotto il commit iniziale locale, producendo una storia lineare senza
commit di merge e senza modificare alcun file di lavoro. Dalle volte successive il push e
semplicemente `git push`.

## Vincolo

L'identita locale, il `core.sshCommand` e il remoto si preparano automaticamente; la protezione
globale `user.useConfigOnly` si imposta solo su conferma. Commit e push restano sempre manuali.

[^1]: *SSH*, Secure Shell - protocollo con cui git si autentica a GitHub tramite una coppia di
chiavi; l'alias host nel file di configurazione SSH seleziona quale chiave usare.
