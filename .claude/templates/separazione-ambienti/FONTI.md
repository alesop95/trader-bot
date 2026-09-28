# Registro delle fonti: separazione fra test e produzione

> Registro delle fonti su cui poggiano la norma `.claude/skills/separazione-ambienti/RIFERIMENTO.md`, la guida `GUIDA.md` di questo pacchetto e la skill `separazione-ambienti`. Ogni affermazione della guida che non viene da un caso osservato rimanda a una voce di questo registro con la sua sigla fra parentesi quadre, per esempio [F13]. Le voci `C` sono i casi osservati nei progetti, descritti senza nomi propri; le voci `F` sono fonti pubblicate.

## Metodo, e che cosa questo registro garantisce

Le fonti pubblicate sono state lette il 2026-09-23 da tre ricerche delegate, ciascuna con il mandato di non scrivere nulla a memoria e di riportare solo ciò che risultava dal corpo della pagina effettivamente recuperata. La via ordinaria è stata il recupero diretto della pagina; dove il recupero restituiva solo la navigazione del sito, la pagina è stata scaricata dal terminale e il corpo verificato prima di estrarne le citazioni, secondo la norma `.claude/skills/fonti-non-recuperabili/RIFERIMENTO.md`. Le pagine che hanno richiesto la seconda via sono dichiarate nella loro voce. Nessuna delle trentasette pagine previste è risultata irraggiungibile.

Le citazioni sono letterali, in lingua originale e brevi, e servono a chi rilegge per ritrovare il punto nella fonte, non a sostituirla. Tre avvertenze valgono per tutto il registro. La prima è che una data di aggiornamento dichiarata dalla pagina è un dato della pagina, mentre l'assenza di data non dice che il contenuto sia vecchio, e va scritta come assenza. La seconda è che la licenza del contenuto è riportata solo dove la pagina la dichiara, e "non dichiarata" non significa libera. La terza è che una documentazione di prodotto descrive il comportamento del prodotto alla data di consultazione: le voci `F24`-`F37` vanno riverificate quando il prodotto cambia versione, e la data di consultazione accanto a ciascuna è ciò che permette di sapere quando.

Formato di ogni voce: titolo, autore o organizzazione, indirizzo letto, data dichiarata, licenza dichiarata, data di consultazione e stato, su che cosa la fonte è autorevole, affermazioni con citazione, limiti che la fonte stessa dichiara, dove è usata nel template.

## Casi osservati

I casi sono nove progetti reali, istanziati da questo template o affiancati a esso, esaminati in sola lettura il 2026-09-23 sul codice, sulla configurazione e sulla documentazione di progetto. I nomi, gli indirizzi e i domini sono tolti secondo il criterio della sezione 16 di `PROJECT-SYSTEM.md`; la corrispondenza con i progetti reali è conservata fuori dal repository, nel livello privato di chi mantiene il template.

| Sigla | Archetipo | Combinazione | Fatto che lo rende istruttivo |
|---|---|---|---|
| C1 | SPA con backend gestito, una persona, rilascio unico e rischioso | R4, P1, D1, L1 | anteprime per richiesta di modifica sul progetto di sviluppo; declassamento della fatturazione del progetto di sviluppo che ha fermato l'accesso per ore |
| C2 | Portale su VPS, piccolo gruppo, integrazione con un ERP | R1, P2, D0, L1 | fusione annullata sulla branch di staging scoperta dopo due settimane; ambiente di staging citato ma non documentato |
| C3 | Portale con dati sensibili, identità propria, su macchina virtuale | R2 sempre acceso, P2, D0, L3 | composizione parametrizzata dal nome del progetto; staging progettato ma non ancora creato |
| C4 | Assistente conversazionale con modelli locali, macchina da otto gigabyte | R2 a richiesta, P1, D0 o D3, L1 | sovrapposizione del solo frontend abbandonata perché l'accesso autenticato atterrava in produzione; identità applicativa separata per ambiente |
| C5 | Sito con CMS destinato a una macchina pubblica | R3, P1, D0 | produzione che esegue solo immagini costruite altrove; pannello di staging raggiungibile da tutta la rete interna |
| C6 | ERP di terze parti con moduli propri | R2, P3, D2 | una branch per ambiente con configurazione divergente; modulo che neutralizza la copia della base dati |
| C7 | Servizio Python interno | R1 | configurazione del proxy duplicata con la stessa lista di indirizzi ammessi |
| C8 | Applicazione di gestione progetti di terze parti | R0 | nessun ambiente di prova; progetto di prova creato nell'istanza di produzione; backup della base dati non ancora pianificato |
| C9 | Migrazione di un gestionale | R1 con due basi dati | ambiente di prova esposto alla rete accanto alla produzione |

## Principi di consegna e configurazione

### F01 - The Twelve-Factor App

Autore: Adam Wiggins, originariamente per Heroku, oggi mantenuto sotto Salesforce, Inc. Indirizzi letti: https://12factor.net/ e le pagine dei fattori https://12factor.net/codebase, https://12factor.net/config, https://12factor.net/backing-services, https://12factor.net/build-release-run, https://12factor.net/dev-prod-parity, https://12factor.net/admin-processes. Data dichiarata: 2017 su ogni pagina di fattore. Licenza: non dichiarata sulle pagine; il repository sorgente del sito, https://github.com/heroku/12factor, dichiara MIT. Consultata il 2026-09-23, letta.

Autorevole su: la definizione originale dei dodici fattori per applicazioni portabili fra ambienti.

Affermazioni. Codice: "One codebase tracked in revision control, many deploys" (I). Configurazione: "Store config in the environment", con il criterio "Whether the codebase could be made open source at any moment, without compromising any credentials" (III). Servizi di appoggio: "A deploy should be able to swap out a local MySQL database with one managed by a third party without any changes to the app's code" (IV). Fasi: "strict separation between the build, release, and run stages" e "Releases are an append-only ledger and a release cannot be mutated once it is created" (V). Parità: "Keep development, staging, and production as similar as possible", con i tre divari di tempo, persone e strumenti, e "resists the urge to use different backing services between development and production" (X). Processi di amministrazione: "One-off admin processes should be run in an identical environment as the regular long-running processes of the app" (XII).

Limiti. La pagina non dichiara limiti metodologici. Un'affermazione circolante, cioè che il testo sia stato aperto a revisioni nel 2024, non trova riscontro nelle pagine lette e resta non verificata.

Usata in: guida, sezioni sulla configurazione separata dal codice, sulla parità fra ambienti e sul costruire una volta sola.

### F02 - Continuous Delivery (bliki)

Autore: Martin Fowler. Indirizzo: https://martinfowler.com/bliki/ContinuousDelivery.html. Data dichiarata: 30 maggio 2013, aggiornata il 12 agosto 2014. Licenza: non dichiarata. Consultata il 2026-09-23, letta.

Autorevole su: la definizione del termine e la sua distinzione dal rilascio continuo automatico.

Affermazioni. "Continuous Delivery is a software development discipline where you build software in such a way that the software can be released to production at any time"; "Continuous Deployment means that every change goes through the pipeline and automatically gets put into production".

Usata in: guida, sezione sulla pipeline e sul rilascio manuale come scelta.

### F03 - Deployment Pipeline (bliki)

Autore: Martin Fowler. Indirizzo: https://martinfowler.com/bliki/DeploymentPipeline.html. Data dichiarata: 30 maggio 2013. Licenza: non dichiarata. Consultata il 2026-09-23, letta.

Autorevole su: la pipeline come sequenza di stadi di fiducia crescente.

Affermazioni. "A deployment pipeline is a way to deal with this by breaking up your build into stages"; "Each stage provides increasing confidence, usually at the cost of extra time"; "Usually the first stage of a deployment pipeline will do any compilation and provide binaries for later stages".

Usata in: guida, sezione sul costruire una volta sola e promuovere lo stesso artefatto.

### F04 - Continuous Delivery, principi

Autore: Jez Humble. Indirizzo: https://continuousdelivery.com/principles/. Data: non dichiarata; copyright 2010-2026. Licenza: non dichiarata. Consultata il 2026-09-23, letta.

Autorevole su: i principi della consegna continua.

Affermazioni. "Get every change in version control as far towards release as we can, getting comprehensive feedback as rapidly as possible" (lavorare a piccoli lotti); "Developers are responsible for the quality and stability of the software they build".

Usata in: guida, introduzione ai paradigmi di promozione.

### F05 - Continuous Delivery, pattern

Autore: Jez Humble, con contributi attribuiti a Dan North e Chris Read. Indirizzo: https://continuousdelivery.com/implementing/patterns/. Data: non dichiarata; la pagina richiama un intervento del 2006. Licenza: non dichiarata. Consultata il 2026-09-23, letta.

Autorevole su: il pattern del pacchetto costruito una sola volta e del rilascio identico in ogni ambiente.

Affermazioni. "Only build packages once. We want to be sure the thing we're deploying is the same thing we've tested throughout the deployment pipeline"; "Deploy the same way to every environment", sviluppo compreso, come la frase prosegue nell'originale dopo un trattino lungo che qui non si riproduce; "We wanted to be able to configure testing and production environments purely from configuration files stored in version control".

Limiti. La pagina stessa dichiara di derivare da un intervento del 2006, anteriore alla formalizzazione successiva della disciplina.

Usata in: guida, sezione sul costruire una volta sola; regola, rischio della configurazione fissata alla costruzione.

### F06 - Infrastructure as Code (bliki)

Autore: Martin Fowler. Indirizzo: https://martinfowler.com/bliki/InfrastructureAsCode.html. Data dichiarata: 1 marzo 2016. Licenza: non dichiarata. Consultata il 2026-09-23, letta.

Autorevole su: la definizione dell'infrastruttura come codice versionato.

Affermazioni. "Infrastructure as code is the approach to defining computing and network infrastructure through source code that can then be treated just like any software system"; "Using code to define the server configuration means that there is greater consistency between servers"; "Keep all this code in source control. That way every configuration and every change is recorded for audit".

Usata in: guida, sezione sull'infrastruttura dichiarata; regola, rischio dell'ambiente previsto e non creato.

### F07 - OpenGitOps, principi

Organizzazione: GitOps Working Group, sotto la CNCF[^1]. Indirizzo: https://opengitops.dev/. Versione dichiarata: GitOps Principles v1.0.0. Licenza: non verificata. Consultata il 2026-09-23, letta.

Autorevole su: la definizione dei quattro principi GitOps sotto governance CNCF.

Affermazioni. "A system managed by GitOps must have its desired state expressed declaratively"; gli altri tre principi sono lo stato desiderato versionato e immutabile, recuperato automaticamente da agenti, e riconciliato di continuo con lo stato reale.

Usata in: guida, sezione sull'infrastruttura dichiarata, come estremo del paradigma.

### F08 - OWASP Secrets Management Cheat Sheet

Organizzazione: OWASP[^2] Cheat Sheet Series Team. Indirizzo: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html. Data di aggiornamento: non visibile nel testo estratto. Licenza: Creative Commons Attribution-ShareAlike 4.0 International. Consultata il 2026-09-23, letta.

Autorevole su: la gestione dei segreti applicativi, compresa la separazione per carico e sensibilità e la rotazione.

Affermazioni. "Many organizations have them hardcoded within the source code in plaintext, littered throughout configuration files" (sezione 1); "secrets for separate workloads and separate sensitivity levels should be in separated Key Vaults accordingly" (4.1.3); "regularly rotate secrets so that any stolen credentials will only work for a short time" (2.7.2); "Ensure that these mounts are mounted in by the orchestrator and never built-in, as this will leak the secret" (5.1).

Usata in: guida, sezione sui segreti per ambiente; regola, rischio dell'identità condivisa.

### F09 - DORA, trunk-based development

Organizzazione: DORA[^3], programma di Google Cloud. Indirizzo: https://dora.dev/capabilities/trunk-based-development/. Data: non dichiarata. Licenza: non verificata. Consultata il 2026-09-23, letta.

Autorevole su: la correlazione, misurata dalla ricerca DORA, fra pratiche di branching e prestazioni di consegna.

Affermazioni. "Each developer divides their own work into small batches and merges that work into trunk at least once... a day"; "Teams achieve higher levels of software delivery and operational performance if they have three or fewer active branches"; "Trunk-based development is a required practice for continuous integration".

Usata in: guida, sezione sul trunk-based development.

### F10 - DORA, test data management

Organizzazione: DORA. Indirizzo: https://dora.dev/capabilities/test-data-management/. Data: non dichiarata. Consultata il 2026-09-23, letta.

Autorevole su: la gestione dei dati di prova come capacità misurata.

Affermazioni. "Adequate test data is available to run full automated test suites"; "Isolate your test data. Run your tests in well-defined environments with controlled inputs and expected outputs".

Usata in: guida, asse D.

### F11 - DORA, deployment automation

Organizzazione: DORA. Indirizzo: https://dora.dev/capabilities/deployment-automation/. Data: non dichiarata. Consultata il 2026-09-23, letta.

Affermazioni. "Use the same deployment process for every environment, including production, to ensure thorough testing before production deployment".

Limiti. Una pagina vicina, all'indirizzo https://dora.dev/capabilities/loosely-coupled-architecture/, restituisce un contenuto intitolato "Loosely coupled teams" aggiornato al 20 ottobre 2025: il nome nell'indirizzo e il titolo divergono, e quella pagina non è usata nel template.

Usata in: guida, sezione sul rilascio identico in ogni ambiente.

### F12 - DORA, continuous delivery

Organizzazione: DORA. Indirizzo: https://dora.dev/capabilities/continuous-delivery/. Data: non dichiarata. Consultata il 2026-09-23, letta.

Affermazioni. "Continuous delivery is the ability to release changes of all kinds on demand quickly, safely, and sustainably".

Usata in: guida, introduzione all'asse P.

## Modelli di branching e promozione

### F13 - Patterns for Managing Source Code Branches

Autore: Martin Fowler. Indirizzo: https://martinfowler.com/articles/branching-patterns.html. Data dichiarata: 28 maggio 2020, con le date di pubblicazione progressiva delle sezioni fra aprile e maggio 2020. Licenza: non dichiarata. Consultata il 2026-09-23, letta; le sezioni sui modelli concreti sono state lette sulla pagina scaricata dal terminale, perché il primo recupero le restituiva troncate.

Autorevole su: la tassonomia dei pattern di branching e la loro composizione nei modelli noti.

Affermazioni. Sul ramo sano: "On each commit, perform automated checks, usually building and running tests, to ensure there are no defects on the branch". Sulla branch per ambiente: "It is, however, the classic example of an Anti Pattern - something that looks appealing when you start, but soon leads to a world of misery, dragons, and coronaviruses", "Keep any environmental changes minimal, and don't use source branching to apply them", e "If configuration changes are required they must be isolated through mechanisms such as explicit configuration files or environment variables". Su git-flow: "git-flow was designed for the kinds of projects where there were multiple versions released in production". Su GitHub Flow: "GitHub Flow assumes a single version in production with high-frequency integration onto a Release-Ready Mainline". Sul trunk-based: "doing all work on Mainline [...] and thus avoiding any kind of long-lived branches".

Limiti. "Like most software patterns, few of them are gold standards that all teams should follow"; "My aim as a writer isn't to convince you to follow a particular path, but instead to inform you about the factors that you should consider".

Usata in: regola, forma P3 dichiarata sconsigliata; guida, asse P per intero.

### F14 - A successful Git branching model

Autore: Vincent Driessen. Indirizzo: https://nvie.com/posts/a-successful-git-branching-model/. Data dichiarata: 5 gennaio 2010, con una nota di riflessione aggiunta nel 2020. Licenza: Creative Commons BY-SA. Consultata il 2026-09-23, letta.

Autorevole su: il modello git-flow originale.

Affermazioni. "We consider origin/master to be the main branch where the source code of HEAD always reflects a production-ready state"; "origin/develop [...] always reflects a state with the latest delivered development changes for the next release"; "Hotfix branches are very much like release branches in that they are also meant to prepare for a new production release, albeit unplanned". Nella nota del 2020: "If your team is doing continuous delivery of software, I would suggest to adopt a much simpler workflow [...] instead of trying to shoehorn git-flow into your team".

Limiti. L'autore stesso, nella nota del 2020, restringe il modello al software con più versioni in produzione supportate insieme.

Usata in: guida, forma P2 e confronto con P1.

### F15 - trunkbaseddevelopment.com

Autore: Paul Hammant, con contributi della comunità. Indirizzi: https://trunkbaseddevelopment.com/, https://trunkbaseddevelopment.com/short-lived-feature-branches/, https://trunkbaseddevelopment.com/feature-flags/, https://trunkbaseddevelopment.com/branch-for-release/, https://trunkbaseddevelopment.com/styles/. Data: copyright 2017-2020. Licenza: non dichiarata. Consultate il 2026-09-23, lette.

Autorevole su: il trunk-based development e i pattern che lo accompagnano.

Affermazioni. "A source-control branching model, where developers collaborate on code in a single branch called 'trunk' and resist any pressure to create other long-lived development branches"; sui rami brevi, "Any longer than two days, and there is a risk of the branch becoming a long-lived feature branch"; sul ramo di rilascio, tagliato "on a just in time basis - say a few days before the release" e che "should not receive continued development work", con il principio attribuito a Wingerd e Seiwald: "Branch: only when necessary, on incompatible policy, late, and instead of freeze".

Limiti. La soglia fra gruppi piccoli e grandi è dichiarata "subject to practitioner debate".

Usata in: guida, sezione sul trunk-based development.

### F16 - GitHub flow

Organizzazione: GitHub. Indirizzo: https://docs.github.com/en/get-started/using-github/github-flow. Data: non dichiarata. Consultata il 2026-09-23, letta.

Autorevole su: la procedura ufficiale del flusso ramo, richiesta, revisione, fusione.

Affermazioni. "Create a branch in your repository"; "Create a pull request to ask collaborators for feedback on your changes"; "After you merge your pull request, delete your branch".

Limiti. La pagina non fissa vincoli di durata dei rami né di dimensione delle richieste.

Usata in: guida, forma P1.

### F17 - Feature Toggles (aka Feature Flags)

Autore: Pete Hodgson, pubblicato su martinfowler.com. Indirizzo: https://martinfowler.com/articles/feature-toggles.html. Data dichiarata: 9 ottobre 2017. Licenza: non dichiarata. Consultata il 2026-09-23, letta.

Autorevole su: le quattro categorie di interruttori di funzionalità e il loro costo.

Affermazioni. "allowing teams to modify system behavior without changing code"; interruttori di rilascio: "Allow incomplete and un-tested codepaths to be shipped to production as latent code which may never be turned on"; operativi: "Used to control operational aspects of our system's behavior"; di permesso: "Used to change the features or product experience that certain users receive"; sul debito: "Savvy teams view the Feature Toggles in their codebase as inventory which comes with a carrying cost and seek to keep that inventory as low as possible"; sulle prove: "our Continuous Delivery process becomes more complex, particularly in regard to testing".

Usata in: guida, sezione sugli interruttori di funzionalità.

## Tecniche di rilascio e di cambiamento dei dati

### F18 - Blue Green Deployment (bliki)

Autore: Martin Fowler. Indirizzo: https://martinfowler.com/bliki/BlueGreenDeployment.html. Data dichiarata: 1 marzo 2010. Consultata il 2026-09-23, letta.

Affermazioni. "Once the software is working in the green environment, you switch the router so that all incoming requests go to the green environment".

Limiti. La fonte indica le modifiche allo schema della base dati come il problema principale, da separare dal rilascio applicativo.

Usata in: guida, sezione sulle tecniche di rilascio.

### F19 - Canary Release (bliki)

Autore: Danilo Sato. Indirizzo: https://martinfowler.com/bliki/CanaryRelease.html. Data dichiarata: 25 giugno 2014. Consultata il 2026-09-23, letta.

Affermazioni. "a technique to reduce the risk of introducing a new software version in production by slowly rolling out the change to a small subset of users before rolling it out to the entire infrastructure".

Limiti. Più versioni convivono in produzione; difficile dove l'aggiornamento lato utente non è controllabile; richiede il cambiamento in parallelo per lo schema.

Usata in: guida, sezione sulle tecniche di rilascio.

### F20 - Parallel Change (bliki)

Autore: Danilo Sato. Indirizzo: https://martinfowler.com/bliki/ParallelChange.html. Data dichiarata: 13 maggio 2014. Consultata il 2026-09-23, letta.

Affermazioni. "breaking the change into three distinct phases: expand, migrate, and contract"; "augment the interface to support both the old and the new versions"; "remove the old version and change the interface so that it only supports the new version".

Limiti. "if the contract phase is not executed you might end up in a worse state than you started".

Usata in: guida, sezione sulle migrazioni della base dati.

### F21 - Dark Launching (bliki)

Autore: Martin Fowler. Indirizzo: https://martinfowler.com/bliki/DarkLaunching.html. Data dichiarata: 29 aprile 2020. Consultata il 2026-09-23, letta.

Affermazioni. "taking a new or changed back-end behavior and calling it from existing users without the users being able to tell it's being called".

Limiti. Adatto a comportamenti automatici, non a funzionalità che l'utente sceglie; il termine è usato anche per indicare i rilasci canarini.

Usata in: guida, sezione sulle tecniche di rilascio.

### F22 - Canarying Releases

Organizzazione: Google, SRE[^4] Workbook, capitolo 16; autori Alec Warner e Štěpán Davidovič, con Alex Hidalgo, Betsy Beyer, Kyle Smith, Matt Duftler. Indirizzo: https://sre.google/workbook/canarying-releases/. Data: 2018. Licenza: CC BY-NC-ND 4.0. Consultata il 2026-09-23, letta.

Affermazioni. "a partial and time-limited deployment of a change in a service and its evaluation"; l'esempio del canarino al cinque per cento del traffico con un tasso d'errore del venti per cento, che produce un impatto complessivo dell'uno per cento.

Limiti. L'isolamento imperfetto può propagare il guasto al gruppo di controllo; i sistemi non interattivi richiedono durate più lunghe.

Usata in: guida, sezione sulle tecniche di rilascio, per il requisito di metriche attribuibili.

### F23 - Evolutionary Database Design

Autori: Pramod Sadalage e Martin Fowler. Indirizzo: https://martinfowler.com/articles/evodb.html. Data dichiarata: gennaio 2003, riscritto per intero nel maggio 2016. Consultata il 2026-09-23, letta.

Affermazioni. Ogni cambiamento "represented as a database migration script which is version controlled together with application code changes"; "each developer gets their own database instance which they can freely modify without touching other people's work"; "a transition phase is a period of time when the database supports both the old access pattern and the new ones simultaneously".

Limiti. Gli autori dichiarano irrisolti la personalizzazione su larga scala fra migliaia di installazioni e la gestione di centinaia di schemi in un solo ambiente.

Usata in: guida, sezione sulle migrazioni e asse D.

## Documentazione degli strumenti

### F24 - Docker Compose

Organizzazione: Docker, Inc. Indirizzi: https://docs.docker.com/compose/how-tos/project-name/, https://docs.docker.com/compose/how-tos/profiles/, https://docs.docker.com/compose/how-tos/multiple-compose-files/, https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/, https://docs.docker.com/compose/how-tos/production/. Data: non dichiarata. Consultate il 2026-09-23, lette.

Autorevole su: il comportamento di Compose rispetto a nome del progetto, profili, composizione di più file e precedenza delle variabili.

Affermazioni. Il nome del progetto si determina in ordine dall'opzione `-p`, da `COMPOSE_PROJECT_NAME`, dall'attributo `name:` e dalla cartella; "Services without a `profiles` attribute are always enabled"; "The simplest way to work with multiple Compose files is to merge them using the `-f` flag"; per la produzione un file aggiuntivo che "only needs to include the changes you want to make from the original Compose file".

Limiti. "the merging rules can make it complex to manage as your configuration grows".

Usata in: guida, forma R2 e i due esempi di composizione.

### F25 - git-worktree

Organizzazione: progetto Git. Indirizzo: https://git-scm.com/docs/git-worktree. Data: non dichiarata. Consultata il 2026-09-23, letta.

Affermazioni. "A git repository can support multiple working trees, allowing you to check out more than one branch at a time"; `add` "refuses to create a new worktree when <commit-ish> is a branch name and is already checked out by another worktree"; "Only clean worktrees (no untracked files and no modification in tracked files) can be removed"; "all pseudo refs are per-worktree and all refs starting with refs/ are shared", e il file `config` "is shared across all worktrees" salvo `extensions.worktreeConfig`.

Usata in: guida, forma L2; norma `skills/alberi-di-lavoro/RIFERIMENTO.md`.

### F26 - Firebase, ambienti

Organizzazione: Google. Indirizzo: https://firebase.google.com/docs/projects/dev-workflows/overview-environments. Data dichiarata: aggiornata il 2026-09-17. Licenza: contenuti CC BY 4.0, esempi Apache 2.0. Consultata il 2026-09-23, letta.

Affermazioni. "Firebase recommends using a separate Firebase project for each environment in your development workflow"; "every app should have at least one pre-production environment that's isolated from production data and resources".

Usata in: guida, forma R4.

### F27 - Firebase Hosting, canali di anteprima

Organizzazione: Google. Indirizzo: https://firebase.google.com/docs/hosting/test-preview-deploy. Data dichiarata: aggiornata il 2026-09-17. Licenza: come F26. Consultata il 2026-09-23, letta.

Affermazioni. I canali si creano con `firebase hosting:channel:deploy CHANNEL_ID`; "anyone who knows the URL can access it"; le anteprime "always interact with real project resources".

Usata in: guida, forma R4 e sezione sugli ambienti effimeri; regola, costo delle anteprime che condividono i dati.

### F28 - Firebase Local Emulator Suite

Organizzazione: Google. Indirizzo: https://firebase.google.com/docs/emulator-suite. Data dichiarata: aggiornata il 2026-09-23. Licenza: come F26. Consultata il 2026-09-23, letta.

Limiti dichiarati. "Do not attempt to use these emulators as 'self-hosted' versions of Firebase services. They are built for accuracy, not performance or security, and are not appropriate to use in production".

Usata in: guida, forma R4.

### F29 - Vercel, ambienti

Organizzazione: Vercel Inc. Indirizzo: https://vercel.com/docs/deployments/environments. Data dichiarata: 2026-09-17. Consultata il 2026-09-23, letta.

Affermazioni. "Vercel provides three default environments (Local, Preview, and Production)"; un'anteprima nasce da "Push a commit to a branch that is not your production branch"; "The first deployment of a new project is always a production deployment".

Limiti dichiarati. I rilasci di produzione in stadio "use production environment variables, so testing can access production services and data".

Usata in: guida, sezione sugli ambienti effimeri, come secondo esempio di piattaforma.

### F30 - Odoo, base dati neutralizzata

Organizzazione: Odoo S.A. Indirizzi: https://www.odoo.com/documentation/19.0/administration/neutralized_database.html e https://www.odoo.com/documentation/19.0/developer/reference/cli.html, sezione "neutralize". Versione della documentazione: 19.0. Data: non dichiarata. Consultate il 2026-09-23, lette sulla pagina scaricata dal terminale, perché il recupero ordinario restituiva solo la navigazione.

Affermazioni. "A neutralized database is a non-production database on which several parameters are deactivated [...] to impact production data (e.g., sending emails to customers)"; il comando `odoo-bin --addons-path <PATH,...> neutralize -d <database>`, con `--stdout` per ottenere le istruzioni invece di applicarle; fra le funzioni disattivate "all planned actions [...], outgoing emails, bank synchronization, payment providers, delivery methods, IAP tokens, website visibility".

Limiti dichiarati. L'elenco è "a non-exhaustive list".

Usata in: guida, forma D2; esempio di neutralizzazione.

### F31 - Odoo.sh, branch

Organizzazione: Odoo S.A. Indirizzo: https://www.odoo.com/documentation/19.0/administration/odoo_sh/getting_started/branches.html. Consultata il 2026-09-23, letta come F30.

Affermazioni. "Staging branches are meant to test new features using production data without compromising the actual production database [...] They create neutralized duplicates of the production database"; "Databases created for staging branches are automatically deleted after one month".

Limiti dichiarati. "Unit tests are not performed. They rely on demo data, which is not loaded into the production and staging databases".

Usata in: guida, forma D2, come conferma che il fornitore stesso adotta la copia neutralizzata.

### F32 - Proxmox VE, modelli e cloni

Organizzazione: Proxmox Server Solutions GmbH. Indirizzo: https://pve.proxmox.com/wiki/VM_Templates_and_Clones. Data dichiarata: ultima modifica 31 gennaio 2018. Consultata il 2026-09-23, letta.

Affermazioni. "A full clone VM is a complete copy and is fully independent from the original VM or VM Template, but it requires the same disk space as the original"; "A linked clone VM requires less disk space but cannot run without access to the base VM Template".

Limiti. È la fonte meno recente del registro: vale come descrizione concettuale, non come riferimento delle opzioni correnti.

Usata in: guida, forma R3 in variante su macchine virtuali.

### F33 - Proxmox VE, qm

Organizzazione: Proxmox Server Solutions GmbH. Indirizzo: https://pve.proxmox.com/pve-docs/qm.1.html. Data: non dichiarata. Consultata il 2026-09-23, letta.

Affermazioni. `qm snapshot <vmid> <snapname>` con `--vmstate` per salvare lo stato della memoria; `qm rollback`, dopo il quale la macchina riparte da sola se l'istantanea comprende la memoria.

Usata in: guida, forma R0.

### F34 - Proxmox VE, backup e ripristino

Organizzazione: Proxmox Server Solutions GmbH. Indirizzo: https://pve.proxmox.com/wiki/Backup_and_Restore. Data dichiarata: ultima modifica 21 maggio 2026. Consultata il 2026-09-23, letta.

Affermazioni. "Proxmox VE backups are always full backups - containing the VM/CT configuration and all data"; "live backup provides snapshot-like semantics on any storage type".

Limiti dichiarati. Nel modo a istantanea esiste un "small inconsistency risk" rispetto al modo con arresto.

Usata in: guida, forma R0 e rischio dello staging escluso dai backup.

### F35 - Next.js, variabili d'ambiente

Organizzazione: Vercel, documentazione di Next.js. Indirizzo: https://nextjs.org/docs/app/guides/environment-variables. Data dichiarata: 2026-08-25, documentazione della versione 16.3.6. Consultata il 2026-09-23, letta.

Affermazioni. Next.js può "'inline' a value, at build time, into the js bundle that is delivered to the client" per le variabili con prefisso `NEXT_PUBLIC_`; "if [...] you build and deploy a single Docker image to multiple environments, all NEXT_PUBLIC_ variables will be frozen with the value evaluated at build time"; "By default, environment variables are only available on the server".

Limiti dichiarati. I riferimenti dinamici non vengono sostituiti: "This will NOT be inlined, because it uses a variable".

Usata in: guida e regola, rischio della configurazione fissata alla costruzione, come caso concreto che contraddice F05 se non lo si conosce.

### F36 - nginx, direttiva listen

Organizzazione: nginx. Indirizzo: http://nginx.org/en/docs/http/ngx_http_core_module.html#listen. Data: non dichiarata. Consultata il 2026-09-23, letta.

Affermazioni. "If the directive is not present then either *:80 is used if nginx runs with the superuser privileges, or *:8000 otherwise"; fra le forme valide, `listen 127.0.0.1:8000;`.

Usata in: guida e regola, rischio dell'ambiente di prova esposto alla rete.

### F37 - Docker, pubblicazione delle porte

Organizzazione: Docker, Inc. Indirizzo: https://docs.docker.com/engine/network/port-publishing/. Data: non dichiarata. Consultata il 2026-09-23, letta.

Affermazioni. Senza indirizzo esplicito "the Docker daemon publishes ports to all host addresses (0.0.0.0 and [::])"; con `-p 127.0.0.1:8080:80` "only the Docker host can access the published container port"; "Publishing container ports is insecure by default"; l'impostazione predefinita si porta sull'interfaccia locale con `"com.docker.network.bridge.host_binding_ipv4": "127.0.0.1"` in `daemon.json`.

Usata in: guida, regola ed esempi di composizione, rischio dell'ambiente di prova esposto alla rete.

## Fonti non ancora consultate, e perché sono qui

Due fonti sono citate spesso su questi temi e non sono state lette: il libro *Continuous Delivery* di Jez Humble e David Farley, del 2010, e *Accelerate* di Nicole Forsgren, Jez Humble e Gene Kim, del 2018, da cui nasce la ricerca DORA. Non sono accessibili come pagine e il template non se ne serve: F04, F05 e F09-F12 ne sono le forme pubblicate dagli stessi autori. Restano elencate come luogo dove cercare, non come fonti verificate, secondo la norma `skills/fonti-non-recuperabili/RIFERIMENTO.md`.

[^1]: *CNCF*, Cloud Native Computing Foundation, fondazione della Linux Foundation che governa progetti come Kubernetes e gruppi di lavoro come quello su GitOps.
[^2]: *OWASP*, Open Worldwide Application Security Project, fondazione senza scopo di lucro che pubblica riferimenti aperti sulla sicurezza applicativa.
[^3]: *DORA*, DevOps Research and Assessment, programma di ricerca pluriennale sulle prestazioni di consegna del software, oggi parte di Google Cloud.
[^4]: *SRE*, Site Reliability Engineering, disciplina che applica metodi di ingegneria del software all'esercizio dei sistemi in produzione.
