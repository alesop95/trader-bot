#!/usr/bin/env node
/*
 * merge-instradamento-settings.js - registra (o toglie) la cartella della mod
 * `instradamento-modelli` dentro env.CLAUDE_CODE_PLUGIN_DIRS del settings.json
 * di un account Claude Code, PRESERVANDO tutto il resto.
 *
 * Uso: node merge-instradamento-settings.js <settings.json> <cartella-mod> [--rimuovi]
 *      node merge-instradamento-settings.js <settings.json> <cartella-mod> --stato
 *
 * Il modo --stato e' in sola lettura e risponde a una domanda sola: quella
 * cartella risulta registrata in quel settings.json? Esiste perche' la stessa
 * domanda, posta cercando il percorso nel testo grezzo del file, ottiene la
 * risposta sbagliata su Windows: dentro il JSON le barre rovesciate sono
 * raddoppiate, quindi il percorso scritto con barre singole non si trova e una
 * mod regolarmente registrata viene dichiarata assente. Il confronto si fa sui
 * percorsi normalizzati dopo JSON.parse, non sui byte del file.
 *
 * Perche' Node e non PowerShell, come per merge-claude-settings.js del
 * pacchetto agenti-terminale: ConvertFrom-Json di PowerShell 5.1 tratta le
 * chiavi JSON come case-insensitive e va in errore su file che contengano
 * chiavi che differiscono solo per maiuscole. JSON.parse ha la stessa semantica
 * che applica Claude Code al proprio file, quindi e' la scelta corretta.
 *
 * Perche' CLAUDE_CODE_PLUGIN_DIRS e non un marketplace: la mod vive nel
 * template, in un percorso stabile, e un marketplace aggiungerebbe un secondo
 * posto da cui la stessa cartella si puo' caricare, cioe' una copia che nessuno
 * invalida. La variabile si legge per account perche' sta nel settings.json
 * della radice di quell'account, che e' esattamente il grado di separazione
 * chiesto: due account della stessa macchina possono averla diversa, o uno sola
 * averla.
 *
 * La scrittura e' difensiva: si valida il JSON prodotto, si scrive su un
 * temporaneo, lo si rilegge da disco e solo allora si sostituisce l'originale.
 * Qualunque anomalia annulla tutto senza lasciare residui. Non tocca mai
 * .credentials.json.
 */
'use strict';

const fs = require('fs');
const path = require('path');

function fallisci(messaggio) {
  console.error('ERRORE: ' + messaggio);
  process.exit(1);
}

const percorso = process.argv[2];
const cartellaMod = process.argv[3];
const rimuovi = process.argv.indexOf('--rimuovi') !== -1;
const soloStato = process.argv.indexOf('--stato') !== -1;

if (!percorso || !cartellaMod) {
  fallisci('uso: node merge-instradamento-settings.js <settings.json> <cartella-mod> [--rimuovi]');
}

// Il separatore dipende dal sistema, non dal file: ';' su Windows, ':' altrove.
const SEPARATORE = process.platform === 'win32' ? ';' : ':';

function normalizza(p) {
  const assoluto = path.resolve(p);
  return process.platform === 'win32' ? assoluto.toLowerCase() : assoluto;
}

const atteso = path.resolve(cartellaMod);

function leggiCartelle(file) {
  if (!fs.existsSync(file)) return [];
  let grezzo;
  try {
    grezzo = fs.readFileSync(file, 'utf8');
  } catch (e) {
    fallisci('impossibile leggere ' + file + ': ' + e.message);
  }
  if (grezzo.trim() === '') return [];
  let dati;
  try {
    dati = JSON.parse(grezzo);
  } catch (e) {
    fallisci(file + ' esiste ma non contiene JSON valido: ' + e.message);
  }
  if (dati === null || typeof dati !== 'object' || Array.isArray(dati)) {
    fallisci(file + ' non contiene un oggetto JSON.');
  }
  const env = (dati.env && typeof dati.env === 'object' && !Array.isArray(dati.env)) ? dati.env : {};
  return String(env.CLAUDE_CODE_PLUGIN_DIRS || '')
    .split(SEPARATORE)
    .map(function (v) { return v.trim(); })
    .filter(function (v) { return v !== ''; });
}

if (soloStato) {
  const registrata = leggiCartelle(percorso).some(function (v) {
    return normalizza(v) === normalizza(atteso);
  });
  console.log(registrata ? 'registrata' : 'non registrata');
  process.exit(registrata ? 0 : 3);
}

if (!rimuovi && !fs.existsSync(path.join(atteso, '.claude-plugin', 'plugin.json'))) {
  fallisci(atteso + ' non sembra una mod: manca .claude-plugin/plugin.json');
}

let impostazioni = {};
if (fs.existsSync(percorso)) {
  let grezzo;
  try {
    grezzo = fs.readFileSync(percorso, 'utf8');
  } catch (e) {
    fallisci('impossibile leggere ' + percorso + ': ' + e.message);
  }
  if (grezzo.trim() !== '') {
    try {
      impostazioni = JSON.parse(grezzo);
    } catch (e) {
      // Non si sovrascrive un file che non si e' riusciti a interpretare:
      // conterrebbe configurazione che andrebbe persa senza preavviso.
      fallisci(percorso + ' esiste ma non e\' JSON valido. Non lo sovrascrivo. ' + e.message);
    }
  }
}

if (impostazioni === null || typeof impostazioni !== 'object' || Array.isArray(impostazioni)) {
  fallisci(percorso + ' non contiene un oggetto JSON.');
}

const chiaviPrima = Object.keys(impostazioni).sort();

if (!impostazioni.env || typeof impostazioni.env !== 'object' || Array.isArray(impostazioni.env)) {
  impostazioni.env = {};
}

const correnti = String(impostazioni.env.CLAUDE_CODE_PLUGIN_DIRS || '')
  .split(SEPARATORE)
  .map(function (v) { return v.trim(); })
  .filter(function (v) { return v !== ''; });

const altri = correnti.filter(function (v) { return normalizza(v) !== normalizza(atteso); });
const eraPresente = altri.length !== correnti.length;

let finali;
if (rimuovi) {
  finali = altri;
} else {
  finali = altri.concat([atteso]);
}

if (finali.length === 0) {
  delete impostazioni.env.CLAUDE_CODE_PLUGIN_DIRS;
  if (Object.keys(impostazioni.env).length === 0) delete impostazioni.env;
} else {
  impostazioni.env.CLAUDE_CODE_PLUGIN_DIRS = finali.join(SEPARATORE);
}

let prodotto;
try {
  prodotto = JSON.stringify(impostazioni, null, 2) + '\n';
  JSON.parse(prodotto);
} catch (e) {
  fallisci('il JSON prodotto non e\' valido, non scrivo nulla: ' + e.message);
}

const temporaneo = percorso + '.tmp-instradamento';
try {
  fs.mkdirSync(path.dirname(percorso), { recursive: true });
  fs.writeFileSync(temporaneo, prodotto, 'utf8');
  const riletto = JSON.parse(fs.readFileSync(temporaneo, 'utf8'));
  const letti = String((riletto.env && riletto.env.CLAUDE_CODE_PLUGIN_DIRS) || '')
    .split(SEPARATORE)
    .map(normalizza);
  const presenteDopo = letti.indexOf(normalizza(atteso)) !== -1;
  if (!rimuovi && !presenteDopo) throw new Error('la cartella non risulta registrata dopo la rilettura');
  if (rimuovi && presenteDopo) throw new Error('la cartella risulta ancora registrata dopo la rilettura');
  for (const k of chiaviPrima) {
    if (!(k in riletto)) throw new Error('la chiave preesistente "' + k + '" e\' sparita');
  }
  fs.renameSync(temporaneo, percorso);
} catch (e) {
  try { if (fs.existsSync(temporaneo)) fs.unlinkSync(temporaneo); } catch (e2) { /* ignorato */ }
  fallisci('scrittura annullata: ' + e.message);
}

console.log('ok: ' + percorso);
console.log('    chiavi preservate: ' + (chiaviPrima.length ? chiaviPrima.join(', ') : '(nessuna, file nuovo)'));
if (rimuovi) {
  console.log('    mod ' + (eraPresente ? 'tolta' : 'non era registrata') + ': ' + atteso);
} else {
  console.log('    mod ' + (eraPresente ? 'gia\' registrata, percorso riallineato' : 'registrata') + ': ' + atteso);
}
console.log('    CLAUDE_CODE_PLUGIN_DIRS: ' + (finali.length ? finali.join(SEPARATORE) : '(vuota, chiave tolta)'));
