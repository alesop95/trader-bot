// Prove della mod instradamento-modelli, eseguite con `claude plugin test`
// dalla cartella `mod`. Ogni prova carica il modulo da zero, quindi le
// variabili di modulo ripartono dai valori iniziali.
//
// Che cosa misurano, e perche' queste e non altre. Le cinque prove sullo spawn
// coprono i cinque rami della decisione, uno per prova, perche' un ramo coperto
// da un caso che ne esercita due non dice quale dei due lo tiene verde. Le due
// prove sullo sforzo e sulla misura separano cio' che la mod riscrive da cio'
// che si limita a contare. L'ultima verifica il fallimento aperto: una
// configurazione illeggibile non deve cambiare niente.

import { expect, mock, test } from 'claude-code/testing'

const CONF_BASE = {
  modo: 'instrada',
  agenti: { Explore: 'haiku', 'general-purpose': { modello: 'sonnet', sforzo: 'low' } },
}

type Registro = { righe: string[]; spawn: any[]; passi: any[]; store: Map<string, unknown> }

// Registra gli stub comuni e restituisce cio' che la mod ha scritto o passato.
function prepara(on: any, testoConfigurazione: string, inizialeStore: Record<string, unknown> = {}): Registro {
  const registro: Registro = { righe: [], spawn: [], passi: [], store: new Map<string, unknown>() }
  const salvato = registro.store
  for (const chiave of Object.keys(inizialeStore)) salvato.set(chiave, inizialeStore[chiave])

  mock.env(on, { CLAUDE_CONFIG_DIR: '/conf' })

  on('fs.read', ($: any, e: any) => {
    const percorso = String(e.path).replace(/\\/g, '/')
    if (percorso.includes('/.claude/')) return { value: '' }
    if (percorso.endsWith('instradamento-modelli.json')) return { value: testoConfigurazione }
    return { value: '' }
  })
  on('command.register', () => ({ value: undefined }))
  on('store.get', ($: any, e: any) => ({ value: salvato.get(e.key) }))
  on('store.set', ($: any, e: any) => {
    salvato.set(e.key, e.value)
    return { value: undefined }
  })
  on('ui.log', ($: any, e: any) => {
    registro.righe.push(e.text)
    return { value: undefined }
  })
  on('session.start', () => ({ cwd: '/work' }))
  on('turn.complete', () => ({ text: '' }))

  on('agent.spawn', ($: any, e: any) => {
    registro.spawn.push({ subagentType: e.subagentType, model: e.model })
    return { model: e.model || 'eredita', agentId: 'ag-' + registro.spawn.length }
  })

  on('turn.step', async function* ($: any, e: any) {
    registro.passi.push({ model: e.model, effort: e.effort, agentId: e.agentId })
    yield { kind: 'text', index: 0, text: 'ok' }
    return {
      turnId: e.turnId,
      index: e.index,
      answer: 'ok',
      toolUses: [],
      stopReason: 'end_turn',
      usage: {
        model: e.model,
        input_tokens: 100,
        output_tokens: 10,
        cache_read_input_tokens: 5,
        cache_creation_input_tokens: 0,
      },
    }
  })

  return registro
}

async function avvia($: any) {
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
}

async function passo($: any, input: any) {
  const flusso = $.turn.step(input)
  let stato = await flusso.next()
  while (stato.done !== true) stato = await flusso.next()
  return stato.value
}

test('in modo instrada un Explore parte sul modello della tabella', async ($, on) => {
  const registro = prepara(on, JSON.stringify(CONF_BASE))
  await avvia($)

  await $.agent.spawn({ prompt: 'cerca', description: 'cerca', subagentType: 'Explore' })

  expect(registro.spawn[0].model).toBe('haiku')
  expect(registro.righe.join('\n')).toContain('Explore su haiku')
})

test('in modo osserva la tabella si dichiara e non si applica', async ($, on) => {
  const registro = prepara(on, JSON.stringify({ ...CONF_BASE, modo: 'osserva' }))
  await avvia($)

  await $.agent.spawn({ prompt: 'cerca', description: 'cerca', subagentType: 'Explore' })

  expect(registro.spawn[0].model).toBeUndefined()
  expect(registro.righe.join('\n')).toContain('andrebbe su haiku')
})

test('un modello chiesto dal chiamante non viene riscritto', async ($, on) => {
  const registro = prepara(on, JSON.stringify(CONF_BASE))
  await avvia($)

  await $.agent.spawn({ prompt: 'cerca', description: 'cerca', subagentType: 'Explore', model: 'opus' })

  expect(registro.spawn[0].model).toBe('opus')
  expect(registro.righe.join('\n')).toContain('non instradato')
})

test('un tipo di agente assente dalla tabella non viene toccato', async ($, on) => {
  const registro = prepara(on, JSON.stringify(CONF_BASE))
  await avvia($)

  await $.agent.spawn({ prompt: 'scrivi', description: 'scrivi', subagentType: 'Plan' })

  expect(registro.spawn[0].model).toBeUndefined()
})

test('un fork non viene mai instradato, perche eredita per definizione', async ($, on) => {
  const registro = prepara(on, JSON.stringify(CONF_BASE))
  await avvia($)

  await $.agent.spawn({ prompt: 'continua', description: 'continua', subagentType: 'Explore', fork: true })

  expect(registro.spawn[0].model).toBeUndefined()
})

test('lo sforzo configurato arriva alle richieste di quel subagent soltanto', async ($, on) => {
  const registro = prepara(on, JSON.stringify(CONF_BASE))
  await avvia($)

  const esito = await $.agent.spawn({ prompt: 'fai', description: 'fai', subagentType: 'general-purpose' })
  expect(registro.spawn[0].model).toBe('sonnet')

  await passo($, { turnId: 't1', index: 0, model: 'sonnet', messageCount: 1, agentId: esito.agentId })
  await passo($, { turnId: 't2', index: 0, model: 'opus', messageCount: 1 })

  expect(registro.passi[0].effort).toBe('low')
  expect(registro.passi[1].effort).toBeUndefined()
  expect(registro.passi[1].model).toBe('opus')
})

test('lo sforzo applicato si conta, e il conteggio distingue lo spawn dalla richiesta', async ($, on) => {
  const registro = prepara(on, JSON.stringify(CONF_BASE))
  await avvia($)

  const esito = await $.agent.spawn({ prompt: 'fai', description: 'fai', subagentType: 'general-purpose' })
  await passo($, { turnId: 't1', index: 0, model: 'sonnet', messageCount: 1, agentId: esito.agentId })
  await passo($, { turnId: 't1', index: 1, model: 'sonnet', messageCount: 2, agentId: esito.agentId })

  await $.command.run({ command: 'instradamento', args: '' })
  const resoconto = registro.righe[registro.righe.length - 1]
  expect(resoconto).toContain('1 spawn instradati con una regola di sforzo, 2 richieste lo hanno ricevuto')
  expect(resoconto).toContain('low: 2')
})

test('uno sforzo che nessuna richiesta riceve viene dichiarato invece di passare inosservato', async ($, on) => {
  const registro = prepara(on, JSON.stringify(CONF_BASE))
  await avvia($)

  // Lo spawn porta la regola di sforzo, ma nessuna richiesta di quel subagent
  // passa da turn.step: e' esattamente il guasto che il contatore esiste per
  // rendere visibile, e senza la riga di avviso si vedrebbe solo il modello
  // riscritto e si darebbe per fatto il resto.
  await $.agent.spawn({ prompt: 'fai', description: 'fai', subagentType: 'general-purpose' })

  await $.command.run({ command: 'instradamento', args: '' })
  const resoconto = registro.righe[registro.righe.length - 1]
  expect(resoconto).toContain('1 spawn instradati con una regola di sforzo, 0 richieste lo hanno ricevuto')
  expect(resoconto).toContain('ATTENZIONE: nessuna richiesta ha ricevuto lo sforzo')
})

test('lo sforzo entrante si registra accanto a quello applicato', async ($, on) => {
  const registro = prepara(on, JSON.stringify(CONF_BASE))
  await avvia($)

  const esito = await $.agent.spawn({ prompt: 'fai', description: 'fai', subagentType: 'general-purpose' })
  await passo($, { turnId: 't1', index: 0, model: 'sonnet', messageCount: 1, agentId: esito.agentId, effort: 'high' })

  await $.command.run({ command: 'instradamento', args: '' })
  const resoconto = registro.righe[registro.righe.length - 1]
  expect(resoconto).toContain('(entranti: high 1)')
})

test('i token di ogni richiesta si sommano per modello e finiscono nello store', async ($, on) => {
  const registro = prepara(on, JSON.stringify(CONF_BASE))
  await avvia($)

  await passo($, { turnId: 't1', index: 0, model: 'opus', messageCount: 1 })
  await passo($, { turnId: 't1', index: 1, model: 'haiku', messageCount: 2 })
  await $.turn.complete({ turnId: 't1', answer: 'ok', durationMs: 10, isAborted: false, usage: null })

  await $.command.run({ command: 'instradamento', args: '' })
  const resoconto = registro.righe[registro.righe.length - 1]
  expect(resoconto).toContain('opus: 1 richieste, 100 in, 10 out')
  expect(resoconto).toContain('haiku: 1 richieste, 100 in, 10 out')
})

test('un nome di agente che nessuno offre viene segnalato come refuso', async ($, on) => {
  const registro = prepara(on, JSON.stringify({ modo: 'instrada', agenti: { Explorer: 'haiku' } }))
  on('agent.offer', () => ({ isOffered: true }))
  await avvia($)

  await $.agent.offer({ agent: 'Explore', description: 'cerca', source: 'built-in' })
  await $.command.run({ command: 'instradamento', args: '' })

  expect(registro.righe[registro.righe.length - 1]).toContain('mai offerto in questa sessione')
})

test('in modo spento non si instrada e non si misura', async ($, on) => {
  const registro = prepara(on, JSON.stringify({ ...CONF_BASE, modo: 'spento' }))
  await avvia($)

  await $.agent.spawn({ prompt: 'cerca', description: 'cerca', subagentType: 'Explore' })
  await passo($, { turnId: 't1', index: 0, model: 'opus', messageCount: 1 })
  await $.command.run({ command: 'instradamento', args: '' })

  expect(registro.spawn[0].model).toBeUndefined()
  expect(registro.righe[registro.righe.length - 1]).toContain('(nessuna richiesta misurata)')
})

test('in osserva le occasioni accumulate si contano e tornano come promemoria', async ($, on) => {
  const osserva = JSON.stringify({ ...CONF_BASE, modo: 'osserva', promemoriaDopo: 2 })

  // Prima sessione: due spawn osservati, nessun promemoria perche' la soglia si
  // guarda all'avvio, quando ancora non era stata superata.
  const prima = prepara(on, osserva)
  await avvia($)
  await $.agent.spawn({ prompt: 'a', description: 'a', subagentType: 'Explore' })
  await $.agent.spawn({ prompt: 'b', description: 'b', subagentType: 'Explore' })
  await $.turn.complete({ turnId: 't1', answer: 'ok', durationMs: 10, isAborted: false, usage: null })
  expect(prima.store.get('proposte')).toBe(2)
  expect(prima.righe.join('\n')).not.toContain('sei in modo osserva')
})

test('il promemoria compare all avvio quando la soglia e gia superata', async ($, on) => {
  const registro = prepara(on, JSON.stringify({ ...CONF_BASE, modo: 'osserva', promemoriaDopo: 2 }), { proposte: 7 })
  await avvia($)

  const testo = registro.righe.join('\n')
  expect(testo).toContain('7 spawn sarebbero stati instradati')
  expect(testo).toContain('instradamento-modelli.json')
})

test('il promemoria tace quando la mod sta gia instradando', async ($, on) => {
  const registro = prepara(on, JSON.stringify({ ...CONF_BASE, promemoriaDopo: 2 }), { proposte: 7 })
  await avvia($)
  expect(registro.righe.join('\n')).not.toContain('sarebbero stati instradati')
})

test('il promemoria tace sotto la soglia configurata', async ($, on) => {
  const registro = prepara(on, JSON.stringify({ ...CONF_BASE, modo: 'osserva', promemoriaDopo: 20 }), { proposte: 7 })
  await avvia($)
  expect(registro.righe.join('\n')).not.toContain('sarebbero stati instradati')
})

test('una configurazione illeggibile lascia tutto come sarebbe senza la mod', async ($, on) => {
  const registro = prepara(on, '{ questo non e JSON')
  await avvia($)

  await $.agent.spawn({ prompt: 'cerca', description: 'cerca', subagentType: 'Explore' })
  await $.command.run({ command: 'instradamento', args: '' })

  expect(registro.spawn[0].model).toBeUndefined()
  expect(registro.righe[registro.righe.length - 1]).toContain('JSON non valido')
})
