/*
 * instradamento-modelli - register.js
 *
 * Mod di Claude Code che fa due cose, e la seconda e' la ragione della prima.
 *
 * MISURA. A ogni richiesta che parte verso il modello, l'hook turn.step legge
 * i token che l'API riporta e li somma per modello: richieste, ingresso,
 * uscita, cache letta e cache scritta. Il totale di sessione vive in memoria,
 * quello cumulato nello store del plugin, che e' condiviso fra le sessioni
 * della macchina. Senza questa misura l'instradamento sarebbe una speranza.
 *
 * INSTRADA. L'hook agent.spawn riscrive il modello del subagent che sta per
 * partire, secondo una tabella che dice quale tipo di agente va su quale
 * modello, e turn.step riscrive lo sforzo di ragionamento delle richieste di
 * quel subagent. La conversazione principale si tocca solo se la
 * configurazione lo chiede esplicitamente.
 *
 * TRE MODI, e il predefinito non instrada niente. In `osserva` la mod dichiara
 * in trascrizione che cosa instraderebbe e lascia correre: e' il modo con cui
 * si misura la linea di partenza, che e' la prima regola del settore. In
 * `instrada` riscrive davvero. In `spento` non fa nulla, nemmeno la misura.
 *
 * FALLISCE APERTO, sempre. Qualunque errore di configurazione o di lettura
 * lascia passare la chiamata intatta: una mod che instrada non e' una guardia
 * di sicurezza, e un suo guasto non deve mai fermare il lavoro.
 *
 * La configurazione si legge per account da <CLAUDE_CONFIG_DIR>/instradamento-
 * modelli.json, con un file di progetto che puo' sovrascriverla. Il perche'
 * della forma e i limiti stanno nel README del pacchetto.
 */

const NOME_FILE = 'instradamento-modelli.json'
const CHIAVE_CONTATORI = 'contatori'
const MODI = ['spento', 'osserva', 'instrada']

const CHIAVE_PROPOSTE = 'proposte'
// Lo sforzo sta in un contatore suo perche' risponde a una domanda diversa dai
// token: non quanto e' costato, ma se la riscrittura dello sforzo abbia davvero
// raggiunto le richieste del subagent. Il segnale e' nel rapporto fra due numeri,
// gli spawn instradati con una regola di sforzo e le richieste che quello sforzo
// lo hanno ricevuto: se il primo cresce e il secondo resta a zero, la riscrittura
// non arriva, e senza questi due conteggi la cosa non si vede da nessuna parte.
const CHIAVE_SFORZO = 'sforzo'

const PREDEFINITA = {
  modo: 'osserva',
  agenti: {},
  conversazione: {},
  rispettaModelloChiesto: true,
  annuncia: true,
  promemoriaDopo: 10,
}

let conf = PREDEFINITA
let origini = []
let avvisi = []
let caricata = false
let percorsoAccount = null

const sforzoPerAgente = new Map()
const tipiOfferti = new Set()
let contatoriSessione = {}
let instradati = 0
let proposti = 0
let propostiDaRiversare = 0
let spawnConSforzo = 0
let spawnConSforzoDaRiversare = 0
let richiesteConSforzo = {}
let richiesteConSforzoDaRiversare = {}

function contatoriVuoti() {
  return { richieste: 0, ingresso: 0, uscita: 0, cacheLetta: 0, cacheScritta: 0 }
}

function somma(contatori, modello, uso) {
  const nome = modello || 'ignoto'
  if (!contatori[nome]) contatori[nome] = contatoriVuoti()
  const c = contatori[nome]
  c.richieste += 1
  if (!uso) return
  c.ingresso += uso.input_tokens || 0
  c.uscita += uso.output_tokens || 0
  c.cacheLetta += uso.cache_read_input_tokens || 0
  c.cacheScritta += uso.cache_creation_input_tokens || 0
}

function segnaSforzo(destinazione, applicato, entrante) {
  const chiave = String(applicato)
  if (!destinazione[chiave]) destinazione[chiave] = { totale: 0, da: {} }
  const voce = destinazione[chiave]
  voce.totale += 1
  // Lo sforzo entrante e' quello che il motore aveva gia' deciso per la
  // richiesta: serve a distinguere una riscrittura che cambia qualcosa da una
  // che riscrive lo stesso valore, cioe' da un risparmio che non c'e'.
  const da = entrante === undefined || entrante === null ? 'senza' : String(entrante)
  voce.da[da] = (voce.da[da] || 0) + 1
}

function righeSforzo(spawn, richieste) {
  const chiavi = Object.keys(richieste || {})
  if (spawn === 0 && chiavi.length === 0) return []
  const righe = []
  const totale = chiavi.reduce(function (somma, k) { return somma + (richieste[k].totale || 0) }, 0)
  righe.push('sforzo di ragionamento: ' + spawn + ' spawn instradati con una regola di sforzo, ' +
    totale + ' richieste lo hanno ricevuto')
  for (const chiave of chiavi.sort()) {
    const voce = richieste[chiave]
    const da = Object.keys(voce.da || {}).sort()
      .map(function (k) { return k + ' ' + voce.da[k] }).join(', ')
    righe.push('  ' + chiave + ': ' + voce.totale + (da ? '  (entranti: ' + da + ')' : ''))
  }
  // Il caso che questo conteggio esiste per rendere visibile: la regola e'
  // scattata allo spawn e nessuna richiesta di quel subagent e' mai passata di
  // qui, quindi lo sforzo non lo ha ricevuto nessuno. Senza questa riga si
  // vedrebbe solo che il modello e' cambiato, e si darebbe per fatto il resto.
  if (spawn > 0 && totale === 0) {
    righe.push('  ATTENZIONE: nessuna richiesta ha ricevuto lo sforzo, la riscrittura non sta arrivando al subagent')
  }
  return righe
}

function fondiSforzi(destinazione, aggiunta) {
  for (const chiave of Object.keys(aggiunta || {})) {
    if (!destinazione[chiave]) destinazione[chiave] = { totale: 0, da: {} }
    const a = aggiunta[chiave]
    const d = destinazione[chiave]
    d.totale += a.totale || 0
    for (const nome of Object.keys(a.da || {})) {
      d.da[nome] = (d.da[nome] || 0) + a.da[nome]
    }
  }
  return destinazione
}

function fondiContatori(destinazione, aggiunta) {
  for (const nome of Object.keys(aggiunta || {})) {
    if (!destinazione[nome]) destinazione[nome] = contatoriVuoti()
    const a = aggiunta[nome]
    const d = destinazione[nome]
    d.richieste += a.richieste || 0
    d.ingresso += a.ingresso || 0
    d.uscita += a.uscita || 0
    d.cacheLetta += a.cacheLetta || 0
    d.cacheScritta += a.cacheScritta || 0
  }
  return destinazione
}

/*
 * Una regola si scrive in forma breve, "Explore": "haiku", oppure estesa,
 * "Explore": { "modello": "haiku", "sforzo": "low" }. La forma breve copre il
 * caso ordinario senza che nessuno debba ricordare lo schema.
 */
function regolaDi(valore) {
  if (!valore) return null
  if (typeof valore === 'string') return { modello: valore, sforzo: undefined }
  if (typeof valore === 'object' && !Array.isArray(valore)) {
    return { modello: valore.modello, sforzo: valore.sforzo }
  }
  return null
}

function fondi(base, aggiunta) {
  const esito = Object.assign({}, base, aggiunta)
  esito.agenti = Object.assign({}, base.agenti || {}, aggiunta.agenti || {})
  esito.conversazione = Object.assign({}, base.conversazione || {}, aggiunta.conversazione || {})
  return esito
}

function unisciPercorso(cartella, nome) {
  if (!cartella) return null
  return String(cartella).replace(/[\\/]+$/, '') + '/' + nome
}

async function leggiJson($, percorso) {
  if (!percorso) return null
  let testo
  try {
    testo = await $.fs.read(percorso)
  } catch (errore) {
    // File assente o illeggibile: e' il caso ordinario, non un problema da dichiarare.
    return null
  }
  if (!testo || !String(testo).trim()) return null
  try {
    const dati = JSON.parse(testo)
    if (!dati || typeof dati !== 'object' || Array.isArray(dati)) {
      avvisi.push(percorso + ': non contiene un oggetto JSON, ignorato')
      return null
    }
    return { percorso: percorso, dati: dati }
  } catch (errore) {
    avvisi.push(percorso + ': JSON non valido, ignorato (' + errore.message + ')')
    return null
  }
}

async function cartellaAccount($) {
  let cartella = null
  try {
    cartella = await $.env.get('CLAUDE_CONFIG_DIR')
  } catch (errore) {
    cartella = null
  }
  if (cartella) return cartella
  let casa = null
  try {
    casa = (await $.env.get('USERPROFILE')) || (await $.env.get('HOME'))
  } catch (errore) {
    casa = null
  }
  return casa ? unisciPercorso(casa, '.claude') : null
}

async function carica($, cwd) {
  origini = []
  avvisi = []
  let composta = PREDEFINITA

  const account = await cartellaAccount($)
  percorsoAccount = unisciPercorso(account, NOME_FILE)
  const perAccount = await leggiJson($, percorsoAccount)
  if (perAccount) {
    composta = fondi(composta, perAccount.dati)
    origini.push(perAccount.percorso)
  }

  const perProgetto = cwd ? await leggiJson($, unisciPercorso(cwd, '.claude/' + NOME_FILE)) : null
  if (perProgetto) {
    composta = fondi(composta, perProgetto.dati)
    origini.push(perProgetto.percorso)
  }

  if (MODI.indexOf(composta.modo) === -1) {
    avvisi.push('modo "' + composta.modo + '" sconosciuto, torno a osserva')
    composta.modo = 'osserva'
  }
  conf = composta
  caricata = true
  return conf
}

function attivo() {
  return conf.modo !== 'spento'
}

function instrada() {
  return conf.modo === 'instrada'
}

async function annuncia($, testo) {
  if (!conf.annuncia) return
  try {
    await $.ui.log(testo)
  } catch (errore) {
    // Una riga non scritta non vale il fallimento di uno spawn.
  }
}

async function salvaContatori($) {
  try {
    const salvato = (await $.store.get(CHIAVE_CONTATORI)) || {}
    const cumulato = fondiContatori(Object.assign({}, salvato), contatoriSessione)
    await $.store.set(CHIAVE_CONTATORI, cumulato)
    contatoriSessione = {}
    if (propostiDaRiversare > 0) {
      const proposteSalvate = (await $.store.get(CHIAVE_PROPOSTE)) || 0
      await $.store.set(CHIAVE_PROPOSTE, proposteSalvate + propostiDaRiversare)
      propostiDaRiversare = 0
    }
    if (spawnConSforzoDaRiversare > 0 || Object.keys(richiesteConSforzoDaRiversare).length > 0) {
      const salvatoSforzo = (await $.store.get(CHIAVE_SFORZO)) || {}
      const unito = {
        spawn: (salvatoSforzo.spawn || 0) + spawnConSforzoDaRiversare,
        richieste: fondiSforzi(Object.assign({}, salvatoSforzo.richieste || {}), richiesteConSforzoDaRiversare),
      }
      await $.store.set(CHIAVE_SFORZO, unito)
      spawnConSforzoDaRiversare = 0
      richiesteConSforzoDaRiversare = {}
    }
  } catch (errore) {
    // Lo store e' una comodita': se non risponde, il totale di sessione resta
    // in memoria e si somma al prossimo giro.
  }
}

function tabellaContatori(contatori) {
  const nomi = Object.keys(contatori || {}).sort()
  if (nomi.length === 0) return ['  (nessuna richiesta misurata)']
  return nomi.map(function (nome) {
    const c = contatori[nome]
    return '  ' + nome + ': ' + c.richieste + ' richieste, ' + c.ingresso + ' in, ' +
      c.uscita + ' out, cache ' + c.cacheLetta + ' letti / ' + c.cacheScritta + ' scritti'
  })
}

async function resoconto($) {
  const righe = []
  righe.push('instradamento-modelli: modo ' + conf.modo)
  righe.push('configurazione: ' + (origini.length ? origini.join(' poi ') : '(nessun file, valori predefiniti)'))
  for (const avviso of avvisi) righe.push('avviso: ' + avviso)

  const tipi = Object.keys(conf.agenti || {}).sort()
  if (tipi.length === 0) {
    righe.push('tabella agenti: vuota')
  } else {
    righe.push('tabella agenti:')
    for (const tipo of tipi) {
      const r = regolaDi(conf.agenti[tipo])
      if (!r) continue
      // Un nome che nessuno ha mai offerto e' quasi sempre un refuso, e un
      // refuso qui non produce alcun errore: produce una regola che non scatta
      // mai. Si dichiara, invece di lasciarlo scoprire a un conto che non cala.
      const visto = tipiOfferti.size === 0 ? '' : (tipiOfferti.has(tipo) ? '' : '  [mai offerto in questa sessione: nome giusto?]')
      righe.push('  ' + tipo + ' -> ' + (r.modello || 'eredita') + (r.sforzo ? ' (sforzo ' + r.sforzo + ')' : '') + visto)
    }
  }
  const c = conf.conversazione || {}
  righe.push('conversazione principale: ' +
    (c.modello || c.sforzo ? (c.modello || 'modello invariato') + (c.sforzo ? ' / sforzo ' + c.sforzo : '') : 'non toccata'))
  righe.push('spawn instradati in questa sessione: ' + instradati + ' su ' + proposti + ' proposti')
  for (const riga of righeSforzo(spawnConSforzo, richiesteConSforzo)) righe.push(riga)
  righe.push('token di questa sessione, per modello:')
  for (const riga of tabellaContatori(contatoriSessione)) righe.push(riga)

  let cumulato = null
  try {
    cumulato = await $.store.get(CHIAVE_CONTATORI)
  } catch (errore) {
    cumulato = null
  }
  righe.push('token cumulati sulla macchina, per modello:')
  for (const riga of tabellaContatori(cumulato || {})) righe.push(riga)

  let sforzoCumulato = null
  try {
    sforzoCumulato = await $.store.get(CHIAVE_SFORZO)
  } catch (errore) {
    sforzoCumulato = null
  }
  if (sforzoCumulato) {
    for (const riga of righeSforzo(sforzoCumulato.spawn || 0, sforzoCumulato.richieste || {})) {
      righe.push(riga.indexOf('  ') === 0 ? riga : 'cumulato, ' + riga)
    }
  }
  return righe.join('\n')
}

/*
 * Il promemoria esiste perche' il modo `osserva` ha un difetto che si produce
 * da se': fa esattamente il suo mestiere, cioe' niente, e chi lo installa se ne
 * dimentica. Una misura raccolta che nessuno guarda e' lavoro buttato, quindi
 * quando le occasioni accumulate superano la soglia la mod lo dice da sola, una
 * volta per sessione, e nomina il file da cambiare invece di dire di cambiarlo.
 */
async function promemoria($) {
  const soglia = Number(conf.promemoriaDopo)
  if (conf.modo !== 'osserva' || !soglia || soglia < 1) return
  let proposte = 0
  try {
    proposte = (await $.store.get(CHIAVE_PROPOSTE)) || 0
  } catch (errore) {
    return
  }
  if (proposte < soglia) return
  await annuncia($, 'instradamento-modelli: sei in modo osserva e ' + proposte +
    ' spawn sarebbero stati instradati. Guarda i numeri con /instradamento, e se convincono metti "modo": "instrada" in ' +
    (percorsoAccount || 'instradamento-modelli.json') + '.')
}

export function register(on) {
  on('session.start', async ($, e, next) => {
    try {
      await carica($, e && e.cwd)
      await promemoria($)
    } catch (errore) {
      avvisi.push('configurazione non letta: ' + errore.message)
    }
    try {
      await $.command.register({
        name: 'instradamento',
        description: 'Instradamento dei modelli: stato, misura e cambio di modo',
        argumentHint: '[instrada|osserva|spento|ricarica|azzera]',
      })
    } catch (errore) {
      // Un nome gia' preso non deve impedire il resto della mod.
    }
    return next(e)
  })

  on('command.run', { command: 'instradamento' }, async ($, e) => {
    const argomento = String((e && e.args) || '').trim().toLowerCase()
    if (MODI.indexOf(argomento) !== -1) {
      conf = Object.assign({}, conf, { modo: argomento })
      await annuncia($, 'instradamento-modelli: modo ' + argomento + ' per questa sessione, il file non e stato toccato')
      return {}
    }
    if (argomento === 'ricarica') {
      let cwd = null
      try {
        cwd = await $.session.cwd()
      } catch (errore) {
        cwd = null
      }
      try {
        await carica($, cwd)
      } catch (errore) {
        avvisi.push('ricarica fallita: ' + errore.message)
      }
    }
    if (argomento === 'azzera') {
      try {
        await $.store.set(CHIAVE_CONTATORI, {})
        await $.store.set(CHIAVE_SFORZO, { spawn: 0, richieste: {} })
      } catch (errore) {
        avvisi.push('azzeramento fallito: ' + errore.message)
      }
      contatoriSessione = {}
      richiesteConSforzo = {}
      richiesteConSforzoDaRiversare = {}
      spawnConSforzo = 0
      spawnConSforzoDaRiversare = 0
    }
    await annuncia($, await resoconto($))
    return {}
  })

  // Serve solo a sapere quali nomi di agente esistono davvero in questa
  // sessione, per smascherare un refuso nella tabella. Non decide niente.
  on('agent.offer', async ($, e, next) => {
    if (e && e.agent) tipiOfferti.add(e.agent)
    return next(e)
  })

  /*
   * Il modello di un subagent si decide qui, prima che parta. Quattro casi
   * lasciano la chiamata intatta, e ciascuno per una ragione propria: il fork,
   * che eredita per definizione e ignora il campo; il modello gia' chiesto dal
   * chiamante, che e' una decisione presa da chi sa piu' di noi; il tipo di
   * agente assente dalla tabella; e il modo diverso da `instrada`.
   */
  on('agent.spawn', async ($, e, next) => {
    let regola = null
    try {
      if (!caricata) await carica($, null)
      if (!attivo()) return next(e)
      regola = regolaDi((conf.agenti || {})[e.subagentType])
    } catch (errore) {
      return next(e)
    }
    if (!regola || (!regola.modello && !regola.sforzo)) return next(e)
    if (e.fork) return next(e)
    if (e.model && conf.rispettaModelloChiesto) {
      await annuncia($, 'instradamento-modelli: ' + e.subagentType + ' non instradato, il chiamante ha chiesto ' + e.model)
      return next(e)
    }

    proposti += 1
    propostiDaRiversare += 1
    if (!instrada()) {
      await annuncia($, 'instradamento-modelli (osserva): ' + e.subagentType + ' andrebbe su ' +
        (regola.modello || 'modello invariato') + (regola.sforzo ? ' con sforzo ' + regola.sforzo : ''))
      return next(e)
    }

    const evento = regola.modello ? Object.assign({}, e, { model: regola.modello }) : e
    const esito = await next(evento)
    if (esito && !esito.deny) {
      instradati += 1
      if (esito.agentId && regola.sforzo) {
        sforzoPerAgente.set(esito.agentId, regola.sforzo)
        spawnConSforzo += 1
        spawnConSforzoDaRiversare += 1
      }
      await annuncia($, 'instradamento-modelli: ' + e.subagentType + ' su ' + (esito.model || regola.modello) +
        (regola.sforzo ? ' con sforzo ' + regola.sforzo : ''))
    }
    return esito
  }).catch(async ($, e, next) => {
    // Fallimento aperto, dichiarato: se l'hook qui sopra va in errore o sfora
    // il tempo, lo spawn parte come sarebbe partito senza la mod. Una mod che
    // instrada non e' una guardia, e un suo guasto non deve fermare il lavoro.
    return next(e)
  })

  /*
   * Ogni richiesta passa di qui: e' il solo punto in cui si vedono i token
   * davvero consumati, ed e' anche il punto in cui si regola lo sforzo, che
   * agent.spawn non espone.
   */
  on('turn.step', async function* ($, e, next) {
    let evento = e
    try {
      if (attivo() && instrada()) {
        const sforzo = e.agentId
          ? sforzoPerAgente.get(e.agentId)
          : (conf.conversazione || {}).sforzo
        const modello = e.agentId ? null : (conf.conversazione || {}).modello
        if (modello) evento = Object.assign({}, evento, { model: modello })
        if (sforzo) {
          segnaSforzo(richiesteConSforzo, sforzo, e.effort)
          segnaSforzo(richiesteConSforzoDaRiversare, sforzo, e.effort)
          evento = Object.assign({}, evento, { effort: sforzo })
        }
      }
    } catch (errore) {
      evento = e
    }
    const esito = yield* next(evento)
    try {
      if (attivo()) {
        const uso = esito && esito.usage
        somma(contatoriSessione, (uso && uso.model) || evento.model, uso)
      }
    } catch (errore) {
      // Una misura mancata non vale l'interruzione di una risposta.
    }
    return esito
  })

  on('turn.complete', async ($, e, next) => {
    if (attivo()) await salvaContatori($)
    if (e && e.agentId) sforzoPerAgente.delete(e.agentId)
    return next(e)
  })

  on('session.end', async ($, e, next) => {
    if (attivo()) await salvaContatori($)
    return next(e)
  })
}
