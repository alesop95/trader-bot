// ============================================================================
// scrub-claude-json.js  (TEMPLATE, companion di session-end-wipe.ps1/.sh)
// Rimuove da .claude.json le voci di "projects" i cui percorsi non iniziano con
// uno dei prefissi da preservare, lasciando intatto tutto il resto del file:
// login, credenziali, configurazione, cache di stato.
//
//   node scrub-claude-json.js <percorso .claude.json> [--solo-config] <prefisso> [<prefisso> ...]
//
// Con --solo-config, aggiunto il 2026-10-09, dalle voci CONSERVATE si tolgono anche le
// metriche dell'ultima sessione: i campi che iniziano con 'last' seguito da una
// maiuscola (lastSessionId, lastCost, i contatori di token e di durata), piu'
// exampleFiles, exampleFilesGeneratedAt e loggedAuthoredArtifactPaths, che elenca i
// file toccati. Restano permessi, server MCP e fiducia nella cartella, cioe' cio' che
// serve perche' il lavoro sul progetto continui senza dialoghi da rifare. E' la
// direttiva del proprietario del 2026-10-08: in locale resta l'impianto, non le tracce
// delle sessioni. Senza l'opzione il comportamento e' quello di prima, cosi' una copia
// vecchia del wipe che non la passa resta corretta.
//
// I prefissi sono PERCORSI, non slug: su Windows di norma la radice del disco dei
// progetti di sviluppo ("D:", "E:"), su POSIX la radice della cartella di sviluppo
// ("/home/utente/dev"). Passarli come argomenti distinti, cosi' i percorsi con
// spazi non richiedono accorgimenti. Il confronto e' case-insensitive: e' cio' che
// serve su Windows, dove lo stesso progetto compare a volte come 'e:/x' e a volte
// come 'E:/x', ed e' il verso prudente per uno script distruttivo.
//
// Perche' Node e non PowerShell: ConvertFrom-Json di PowerShell 5.1 tratta le chiavi
// come case-insensitive e va in errore su un file che contenga sia 'e:/x' sia 'E:/x'.
// JSON.parse/JSON.stringify e' invece la stessa semantica che Claude Code applica al
// proprio file.
//
// Il file non viene mai riscritto alla cieca: si valida il risultato, si rilegge da
// disco e solo allora si sostituisce l'originale.
// Exit code: 0 = fatto o niente da fare, 1 = annullato senza toccare nulla.
// ============================================================================
'use strict';
const fs = require('fs');

const args = process.argv.slice(2);
const cfgPath = args[0];
const soloConfig = args.includes('--solo-config');
const keepPrefixes = args.slice(1).filter(a => a !== '--solo-config');
if (!cfgPath) {
  console.error('scrub: percorso di .claude.json mancante');
  process.exit(1);
}
const keep = keepPrefixes.map(s => s.trim().toLowerCase()).filter(Boolean);
if (keep.length === 0) {
  console.error('scrub: nessun prefisso da preservare, annullo per prudenza');
  process.exit(1);
}

let cfg;
try {
  cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
} catch (err) {
  console.error(`scrub: ${cfgPath} illeggibile o non valido (${err.message}), annullo`);
  process.exit(1);
}

if (!cfg.projects || typeof cfg.projects !== 'object' || Array.isArray(cfg.projects)) {
  process.exit(0);
}

const allKeys = Object.keys(cfg.projects);
const kept = {};
for (const key of allKeys) {
  const k = key.toLowerCase();
  if (keep.some(prefix => k.startsWith(prefix))) kept[key] = cfg.projects[key];
}
const dropped = allKeys.length - Object.keys(kept).length;
const METRICHE = new Set(['exampleFiles', 'exampleFilesGeneratedAt', 'loggedAuthoredArtifactPaths']);
let stripped = 0;
if (soloConfig) {
  for (const key of Object.keys(kept)) {
    const voce = kept[key];
    if (!voce || typeof voce !== 'object' || Array.isArray(voce)) continue;
    for (const campo of Object.keys(voce)) {
      if (/^last[A-Z]/.test(campo) || METRICHE.has(campo)) { delete voce[campo]; stripped++; }
    }
  }
}
if (dropped === 0 && stripped === 0) process.exit(0);

// Non si riscrive un file che custodisce il login senza avere il login sotto mano.
if (!cfg.oauthAccount || !cfg.userID) {
  console.error('scrub: campi di login assenti nell oggetto in memoria, annullo');
  process.exit(1);
}

cfg.projects = kept;
const out = JSON.stringify(cfg, null, 2);
try {
  JSON.parse(out);
} catch (err) {
  console.error(`scrub: risultato non valido (${err.message}), annullo`);
  process.exit(1);
}

const tmp = `${cfgPath}.tmp`;
try {
  fs.writeFileSync(tmp, out, 'utf8');
  JSON.parse(fs.readFileSync(tmp, 'utf8'));   // rilettura da disco prima di sostituire
  fs.renameSync(tmp, cfgPath);
} catch (err) {
  try { fs.unlinkSync(tmp); } catch (_) { /* niente da ripulire */ }
  console.error(`scrub: scrittura annullata (${err.message}), originale intatto`);
  process.exit(1);
}

console.error(`scrub: rimosse ${dropped} voci di projects, conservate ${Object.keys(kept).length}, tolti ${stripped} campi di metrica`);
