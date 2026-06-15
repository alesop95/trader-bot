#!/usr/bin/env node
// Rende i diagrammi Mermaid (.mmd) in .svg riusando il browser gia installato
// (Edge o Chrome), senza scaricare il Chromium di Puppeteer.
//
// Uso:
//   node tools/render-diagrams.mjs                 # rende .claude/context/diagrams/*.mmd
//   node tools/render-diagrams.mjs <cartella>      # rende <cartella>/*.mmd
//
// Prerequisiti: Node e un browser Chromium-based di sistema (Edge o Chrome).
// La prima esecuzione scarica via npx i soli script di mermaid-cli (pochi MB),
// mai un browser: il download del Chromium e disattivato e si usa quello locale.
//
// Override manuale del browser, se l'autorilevamento fallisce:
//   PUPPETEER_EXECUTABLE_PATH="/percorso/al/browser" node tools/render-diagrams.mjs

import { existsSync, readdirSync, writeFileSync, mkdtempSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { tmpdir } from 'node:os'
import { join, dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const repoRoot = resolve(__dirname, '..')
const diagramsDir = resolve(process.argv[2] ?? join(repoRoot, '.claude', 'context', 'diagrams'))

function findBrowser () {
  const fromEnv = process.env.PUPPETEER_EXECUTABLE_PATH || process.env.CHROME_PATH
  if (fromEnv && existsSync(fromEnv)) return fromEnv
  const pf = process.env['ProgramFiles'] || 'C:/Program Files'
  const pf86 = process.env['ProgramFiles(x86)'] || 'C:/Program Files (x86)'
  const local = process.env['LOCALAPPDATA'] || ''
  const candidates = process.platform === 'win32'
    ? [
        `${pf}/Microsoft/Edge/Application/msedge.exe`,
        `${pf86}/Microsoft/Edge/Application/msedge.exe`,
        `${pf}/Google/Chrome/Application/chrome.exe`,
        `${pf86}/Google/Chrome/Application/chrome.exe`,
        `${local}/Google/Chrome/Application/chrome.exe`
      ]
    : process.platform === 'darwin'
      ? [
          '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
          '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'
        ]
      : [
          '/usr/bin/google-chrome',
          '/usr/bin/chromium',
          '/usr/bin/chromium-browser',
          '/usr/bin/microsoft-edge'
        ]
  return candidates.find((p) => existsSync(p))
}

const browser = findBrowser()
if (!browser) {
  console.error('Nessun browser Chromium-based trovato. Imposta PUPPETEER_EXECUTABLE_PATH al percorso di Edge o Chrome.')
  process.exit(1)
}
if (!existsSync(diagramsDir)) {
  console.error(`Cartella diagrammi inesistente: ${diagramsDir}`)
  process.exit(1)
}

const cfgDir = mkdtempSync(join(tmpdir(), 'mmd-'))
const cfgPath = join(cfgDir, 'puppeteer.json')
writeFileSync(cfgPath, JSON.stringify({ executablePath: browser, args: ['--no-sandbox'] }, null, 2))

const sources = readdirSync(diagramsDir).filter((f) => f.endsWith('.mmd'))
if (sources.length === 0) {
  console.error(`Nessun file .mmd in ${diagramsDir}`)
  process.exit(1)
}

console.log(`Browser: ${browser}`)
console.log(`Diagrammi: ${diagramsDir}  (${sources.length} file)\n`)

const env = { ...process.env, PUPPETEER_SKIP_DOWNLOAD: 'true', PUPPETEER_SKIP_CHROMIUM_DOWNLOAD: 'true' }
// Su Windows npx e un .cmd: spawnSync lo rifiuta senza shell, quindi usiamo la
// shell e quotiamo i percorsi (possono contenere spazi).
const useShell = process.platform === 'win32'
const npx = useShell ? 'npx.cmd' : 'npx'
const q = (s) => (useShell ? `"${s}"` : s)
let failed = 0

for (const src of sources) {
  const input = join(diagramsDir, src)
  const output = join(diagramsDir, src.replace(/\.mmd$/, '.svg'))
  const r = spawnSync(npx, ['-y', '@mermaid-js/mermaid-cli', '-i', q(input), '-o', q(output), '-p', q(cfgPath)], {
    env, stdio: ['ignore', 'pipe', 'pipe'], encoding: 'utf8', shell: useShell
  })
  if (r.status === 0 && existsSync(output)) {
    console.log(`  ok   ${src} -> ${src.replace(/\.mmd$/, '.svg')}`)
  } else {
    failed++
    console.error(`  FAIL ${src}`)
    if (r.stderr) console.error(r.stderr.trim().split('\n').slice(-3).map((l) => '       ' + l).join('\n'))
  }
}

console.log(`\nCompletati ${sources.length - failed}/${sources.length}.`)
process.exit(failed ? 1 : 0)
