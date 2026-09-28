#!/usr/bin/env node
/*
 * merge-claude-settings.js — fonde l'hook SessionEnd e autoMemoryEnabled dentro
 * il settings.json di un account Claude Code, PRESERVANDO tutto il resto.
 *
 * Uso: node merge-claude-settings.js <percorso-settings.json> <percorso-script-wipe>
 *
 * Si riceve il PERCORSO dello script, non il comando gia' composto: PowerShell
 * 5.1 mangia le virgolette annidate quando passa un argomento a un eseguibile
 * nativo, e l'hook finirebbe registrato con il percorso non quotato. Il comando
 * lo compone questo file, dove le virgolette sono al sicuro.
 *
 * Perche' Node e non PowerShell, come per scrub-claude-json.js del template:
 * ConvertFrom-Json di PowerShell 5.1 tratta le chiavi JSON come
 * case-insensitive e va in errore su file che contengano chiavi che
 * differiscono solo per maiuscole. JSON.parse ha la stessa semantica che
 * applica Claude Code al proprio file, quindi e' la scelta corretta.
 *
 * La scrittura e' difensiva: si valida il JSON prodotto, si scrive su un
 * temporaneo, lo si rilegge da disco, e solo allora si sostituisce l'originale.
 * Qualunque anomalia annulla tutto senza lasciare residui.
 *
 * Non tocca mai .credentials.json.
 */
'use strict';

const fs = require('fs');
const path = require('path');

function fallisci(messaggio) {
  console.error('ERRORE: ' + messaggio);
  process.exit(1);
}

const percorso = process.argv[2];
const percorsoWipe = process.argv[3];

if (!percorso || !percorsoWipe) {
  fallisci('uso: node merge-claude-settings.js <settings.json> <percorso-script-wipe>');
}

const comandoHook =
  'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + percorsoWipe + '"';

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

impostazioni.autoMemoryEnabled = false;

if (!impostazioni.hooks || typeof impostazioni.hooks !== 'object' || Array.isArray(impostazioni.hooks)) {
  impostazioni.hooks = {};
}
impostazioni.hooks.SessionEnd = [
  { hooks: [{ type: 'command', command: comandoHook }] }
];

let prodotto;
try {
  prodotto = JSON.stringify(impostazioni, null, 2) + '\n';
  JSON.parse(prodotto);
} catch (e) {
  fallisci('il JSON prodotto non e\' valido, non scrivo nulla: ' + e.message);
}

const temporaneo = percorso + '.tmp-merge';
try {
  fs.mkdirSync(path.dirname(percorso), { recursive: true });
  fs.writeFileSync(temporaneo, prodotto, 'utf8');
  const riletto = JSON.parse(fs.readFileSync(temporaneo, 'utf8'));
  if (riletto.autoMemoryEnabled !== false) {
    throw new Error('autoMemoryEnabled non risulta false dopo la rilettura');
  }
  if (!riletto.hooks || !Array.isArray(riletto.hooks.SessionEnd)) {
    throw new Error('hook SessionEnd non risulta presente dopo la rilettura');
  }
  for (const k of chiaviPrima) {
    if (!(k in riletto)) {
      throw new Error('la chiave preesistente "' + k + '" e\' sparita');
    }
  }
  fs.renameSync(temporaneo, percorso);
} catch (e) {
  try { if (fs.existsSync(temporaneo)) fs.unlinkSync(temporaneo); } catch (e2) { /* ignorato */ }
  fallisci('scrittura annullata: ' + e.message);
}

const chiaviDopo = Object.keys(impostazioni).sort();
const aggiunte = chiaviDopo.filter(function (k) { return chiaviPrima.indexOf(k) === -1; });
console.log('ok: ' + percorso);
console.log('    chiavi preservate: ' + (chiaviPrima.length ? chiaviPrima.join(', ') : '(nessuna, file nuovo)'));
if (aggiunte.length) {
  console.log('    chiavi aggiunte:   ' + aggiunte.join(', '));
}
