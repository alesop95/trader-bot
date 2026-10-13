# ============================================================================
# test-wipe-per-sessione.ps1
# Prova end-to-end di session-end-wipe.ps1 nel modo per sessione introdotto il
# 2026-10-09: il wipe toglie subito cio che appartiene a sessioni chiuse e conserva solo
# cio che appartiene a una sessione con un processo vivo.
#
# Costruisce in una cartella temporanea due home finte, .claude-accountT e
# .claude-accountU, e una radice di scratchpad finta, e avvia un processo vero di nome
# claude.exe (una copia di cmd.exe che aspetta), con il suo sessions\<pid>.json: e' il
# solo modo di esercitare la protezione, che si decide sui processi vivi e non su un
# elenco passato a mano. Il wipe gira con -BaseProva e -TempProva, quindi non tocca le
# home reali ne la radice reale degli scratchpad.
#
# Sei scenari, ciascuno con l'esito opposto a quello accanto:
#   1. senza stato-magazzino.ps1 accanto al wipe: rinvio totale, niente rimosso;
#   2. con la libreria: la sessione A del processo vivo resta in ogni store, la sessione
#      chiusa B sparisce da ogni store, .claude.json di T non si tocca;
#   3. account U senza sessioni aperte: verbali via, .claude.json ridotto alla configurazione;
#   4. -Forza su T: sparisce anche A;
#   5. wipe lanciato a mano da dentro un claude.exe finto: la sessione di quel processo
#      resta, perche' e' viva;
#   6. lo stesso con il payload di SessionEnd sullo standard input, come fa l'hook: il wipe
#      si rilancia fuori dall'albero dei processi, attende che il claude.exe finto esca, e
#      solo allora pulisce; la sessione di quel processo sparisce;
#   7. un claude.exe finto vivo SENZA file di sessione, avviato con CLAUDE_CONFIG_DIR di un
#      account W e dalla cartella di un progetto: il wipe legge account e cartella dal
#      processo, conserva verbali e scratchpad recenti di quel progetto in W, toglie quelli
#      vecchi, e non protegge il verbale recente di un altro account X, che con la sola
#      ipotesi sarebbe stato fra le candidate.
#
# Uso:  powershell -NoProfile -ExecutionPolicy Bypass -File tools/tests/test-wipe-per-sessione.ps1
# Esce 0 se tutti i casi passano, 1 altrimenti.
# ============================================================================
$ErrorActionPreference = 'Stop'
$qui = Split-Path -Parent $MyInvocation.MyCommand.Path
$tools = Split-Path -Parent $qui
$wipeTpl = Join-Path $tools 'session-end-wipe.ps1'
$scrub = Join-Path $tools 'scrub-claude-json.js'
$lib = Join-Path $tools 'stato-magazzino.ps1'

$T = Join-Path ([IO.Path]::GetTempPath()) ('prova-wipe-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
$accT = Join-Path $T '.claude-accountT'
$accU = Join-Path $T '.claude-accountU'
$tmpR = Join-Path $T 'tmpclaude'
$mcpR = Join-Path $T 'mcpcache'
$A = 'aaaaaaaa-1111-2222-3333-444444444444'
$B = 'bbbbbbbb-1111-2222-3333-444444444444'
$C = 'cccccccc-1111-2222-3333-444444444444'
$D = 'dddddddd-1111-2222-3333-444444444444'
$accV = Join-Path $T '.claude-accountV'
$vecchio = Get-Date '2026-01-01T00:00:00'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$script:casi = 0; $script:falliti = 0
function Atteso($nome, $cond) {
  $script:casi++
  if ($cond) { Write-Host "  ok    $nome" } else { $script:falliti++; Write-Host "  FALLITO $nome" -ForegroundColor Red }
}
function Scrivi($path, $testo, $quando) {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null
  [IO.File]::WriteAllText($path, $testo, $utf8)
  if ($quando) { (Get-Item -LiteralPath $path).LastWriteTime = $quando }
}
function Cartella($path, $quando) {
  New-Item -ItemType Directory -Force -Path $path | Out-Null
  Scrivi (Join-Path $path 'x.txt') 'x' $quando
  if ($quando) { (Get-Item -LiteralPath $path).LastWriteTime = $quando }
}
# Compila il template come fa Installa-Claude.ps1: nessuna trascrizione preservata,
# permessi e fiducia conservati per E:, home finta passata con -BaseProva.
function Installa($acc, [switch]$ConLibreria) {
  $h = Join-Path $acc 'hooks'
  New-Item -ItemType Directory -Force -Path $h | Out-Null
  $righe = foreach ($r in (Get-Content -LiteralPath $wipeTpl)) {
    $t = $r.TrimStart()
    if ($t.StartsWith('$keepPrefixes = ') -and $r.Contains('<KEEP_PREFIXES>')) { '$keepPrefixes = @()' }
    elseif ($t.StartsWith('$keepPathPrefixes = ') -and $r.Contains('<KEEP_PATH_PREFIXES>')) { '$keepPathPrefixes = @(' + [char]39 + 'E:' + [char]39 + ')' }
    elseif ($t.StartsWith('$allowEmptyKeep = ')) { '$allowEmptyKeep = $true' }
    else { $r }
  }
  Set-Content -LiteralPath (Join-Path $h 'session-end-wipe.ps1') -Value $righe -Encoding ascii
  Copy-Item -LiteralPath $scrub -Destination $h -Force
  if ($ConLibreria) { Copy-Item -LiteralPath $lib -Destination $h -Force }
}
function Esegui($acc, [switch]$Forza) {
  $argomenti = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $acc 'hooks\session-end-wipe.ps1'), '-BaseProva', $acc, '-TempProva', $tmpR, '-McpProva', $mcpR)
  if ($Forza) { $argomenti += '-Forza' }
  # scrub-claude-json.js scrive il suo riepilogo su stderr: non e' un errore.
  $ErrorActionPreference = 'Continue'
  $out = & powershell @argomenti 2>&1
  return [pscustomobject]@{ Uscita = $LASTEXITCODE; Testo = ($out -join "`n") }
}
function C($rel) { Test-Path -LiteralPath (Join-Path $accT $rel) }

$finto = $null
$senzaFile = $null
try {
  # --- magazzino finto ---------------------------------------------------------
  foreach ($acc in $accT, $accU) { Scrivi (Join-Path $acc 'settings.json') '{}' $null }
  $slug = Join-Path $accT 'projects\E--p'
  Scrivi (Join-Path $slug "$A.jsonl") ('{"type":"queue-operation","timestamp":"' + (Get-Date).ToUniversalTime().ToString('o') + '"}') $null
  Cartella (Join-Path $slug $A) $null
  Scrivi (Join-Path $slug "$B.jsonl") '{"type":"queue-operation","timestamp":"2026-01-01T00:00:00.000Z"}' $vecchio
  Cartella (Join-Path $slug $B) $vecchio
  Cartella (Join-Path $slug 'memory') $vecchio
  foreach ($st in 'file-history', 'session-env') { Cartella (Join-Path $accT "$st\$A") $null; Cartella (Join-Path $accT "$st\$B") $vecchio }
  Scrivi (Join-Path $accT "todos\$A-agent-$A.json") '[]' $null
  Scrivi (Join-Path $accT "todos\$B-agent-$B.json") '[]' $vecchio
  Cartella (Join-Path $accT 'jobs\aaaaaaaa') $null
  Cartella (Join-Path $accT 'jobs\bbbbbbbb') $vecchio
  Scrivi (Join-Path $accT 'plans\vecchio-piano-qui.md') 'v' $vecchio
  Scrivi (Join-Path $accT 'sessions\99999.json') '{"pid":99999,"sessionId":"x"}' $vecchio
  $histA = '{"display":"richiesta di A","timestamp":1,"project":"E:\\p","sessionId":"' + $A + '"}'
  $histB = '{"display":"richiesta di B","timestamp":1,"project":"E:\\p","sessionId":"' + $B + '"}'
  [IO.File]::WriteAllLines((Join-Path $accT 'history.jsonl'), [string[]]@($histA, $histB), $utf8)
  $cfg = '{"oauthAccount":{"x":1},"userID":"u","projects":{"E:/p":{"allowedTools":["a"],"hasTrustDialogAccepted":true,"lastCost":3,"lastSessionId":"s","exampleFiles":["f"]},"C:/x":{"lastCost":1}}}'
  Scrivi (Join-Path $accT '.claude.json') $cfg $null
  Scrivi (Join-Path $accU '.claude.json') $cfg $null
  Scrivi (Join-Path $accU "projects\E--q\$C.jsonl") '{"type":"queue-operation","timestamp":"2026-01-01T00:00:00.000Z"}' $vecchio
  Cartella (Join-Path $tmpR "E--p\$A") $null
  Cartella (Join-Path $tmpR "E--p\$B") $vecchio
  Scrivi (Join-Path $tmpR 'E--p\altro.txt') 'v' $vecchio
  Scrivi (Join-Path $mcpR 'E--p\mcp-logs-x\vecchio.txt') 'v' $vecchio
  Scrivi (Join-Path $mcpR 'E--z\mcp-logs-y\vecchio.txt') 'v' $vecchio

  # --- il processo vivo finto, con il suo file di sessione ----------------------
  $bin = Join-Path $T 'bin'
  New-Item -ItemType Directory -Force -Path $bin | Out-Null
  Copy-Item -LiteralPath (Join-Path $env:WINDIR 'System32\cmd.exe') -Destination (Join-Path $bin 'claude.exe')
  $finto = Start-Process -FilePath (Join-Path $bin 'claude.exe') -ArgumentList '/c', 'ping -n 300 127.0.0.1 >nul' -WindowStyle Hidden -PassThru
  Start-Sleep -Milliseconds 500
  $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$($finto.Id)"
  Scrivi (Join-Path $accT "sessions\$($finto.Id).json") ('{"pid":' + $finto.Id + ',"sessionId":"' + $A + '","procStart":"' + $cim.CreationDate.ToFileTimeUtc() + '"}') $null
  Scrivi (Join-Path $accT 'plans\nuovo-piano-qui.md') 'n' (Get-Date).AddSeconds(5)
  Scrivi (Join-Path $mcpR 'E--p\mcp-logs-x\nuovo.txt') 'n' (Get-Date).AddSeconds(5)

  # --- 1. senza libreria: rinvio totale -----------------------------------------
  Installa $accT
  $r = Esegui $accT
  Write-Host 'scenario 1, senza libreria'
  Atteso 'esce con 0' ($r.Uscita -eq 0)
  Atteso 'il diario dice Rimandato' ((Get-Content (Join-Path $accT 'session-end-wipe.log') -Raw) -match 'Rimandato')
  Atteso 'la sessione chiusa B e'' ancora li' ((C "projects\E--p\$B.jsonl") -and (Test-Path (Join-Path $tmpR "E--p\$B")))

  # --- 2. con la libreria: per sessione ------------------------------------------
  Installa $accT -ConLibreria
  $r = Esegui $accT
  $log = Get-Content (Join-Path $accT 'session-end-wipe.log') -Raw
  Write-Host 'scenario 2, con la libreria'
  Atteso 'esce con 0 e dice Fatto' ($r.Uscita -eq 0 -and $log -match 'Fatto\.')
  Atteso 'il diario nomina la sessione A fra le conservate' ($log -match "Conservate \d+ sessioni" -and $log -match [regex]::Escape($A))
  Atteso 'verbale e cartella di A restano' ((C "projects\E--p\$A.jsonl") -and (C "projects\E--p\$A"))
  Atteso 'verbale, cartella e memoria di B spariscono' (-not (C "projects\E--p\$B.jsonl") -and -not (C "projects\E--p\$B") -and -not (C 'projects\E--p\memory'))
  Atteso 'file-history e session-env: A resta, B sparisce' ((C "file-history\$A") -and -not (C "file-history\$B") -and (C "session-env\$A") -and -not (C "session-env\$B"))
  Atteso 'todos: A resta, B sparisce' ((C "todos\$A-agent-$A.json") -and -not (C "todos\$B-agent-$B.json"))
  Atteso 'jobs per identificativo breve: A resta, B sparisce' ((C 'jobs\aaaaaaaa') -and -not (C 'jobs\bbbbbbbb'))
  Atteso 'plans: il piano recente resta, il vecchio sparisce' ((C 'plans\nuovo-piano-qui.md') -and -not (C 'plans\vecchio-piano-qui.md'))
  Atteso 'sessions: il file del processo vivo resta, quello morto sparisce' ((C "sessions\$($finto.Id).json") -and -not (C 'sessions\99999.json'))
  $h = [string](Get-Content (Join-Path $accT 'history.jsonl') -Raw -ErrorAction SilentlyContinue)
  Atteso 'history.jsonl: resta la riga di A, sparisce quella di B' ($h -match 'richiesta di A' -and $h -notmatch 'richiesta di B')
  Atteso 'scratchpad: A resta, B e il file vecchio spariscono' ((Test-Path (Join-Path $tmpR "E--p\$A")) -and -not (Test-Path (Join-Path $tmpR "E--p\$B")) -and -not (Test-Path (Join-Path $tmpR 'E--p\altro.txt')))
  Atteso 'log MCP: il file recente resta, il vecchio sparisce' ((Test-Path (Join-Path $mcpR 'E--p\mcp-logs-x\nuovo.txt')) -and -not (Test-Path (Join-Path $mcpR 'E--p\mcp-logs-x\vecchio.txt')))
  Atteso 'log MCP: la cartella con soli file vecchi sparisce' (-not (Test-Path (Join-Path $mcpR 'E--z')))
  Atteso '.claude.json di un account con sessione aperta non si tocca' ((Get-Content (Join-Path $accT '.claude.json') -Raw) -match 'lastCost' -and $log -match 'Blocco 4 rimandato')

  # --- 3. account senza sessioni aperte -------------------------------------------
  Installa $accU -ConLibreria
  $r = Esegui $accU
  Write-Host 'scenario 3, account senza sessioni aperte'
  $j = Get-Content (Join-Path $accU '.claude.json') -Raw
  Atteso 'esce con 0' ($r.Uscita -eq 0)
  Atteso 'il verbale chiuso C e il suo slug spariscono' (-not (Test-Path (Join-Path $accU 'projects\E--q')))
  Atteso '.claude.json: resta la voce E: con permessi e fiducia' ($j -match '"E:/p"' -and $j -match 'allowedTools' -and $j -match 'hasTrustDialogAccepted')
  Atteso '.claude.json: spariscono le metriche e la voce C:' ($j -notmatch 'lastCost' -and $j -notmatch 'exampleFiles' -and $j -notmatch '"C:/x"')
  Atteso '.claude.json: il login resta' ($j -match 'oauthAccount' -and $j -match 'userID')

  # --- 4. -Forza ------------------------------------------------------------------
  $r = Esegui $accT -Forza
  Write-Host 'scenario 4, -Forza'
  Atteso 'con -Forza sparisce anche la sessione aperta A' (-not (C 'projects\E--p') -and -not (Test-Path (Join-Path $tmpR 'E--p')) -and -not (Test-Path (Join-Path $mcpR 'E--p')))
  Atteso 'con -Forza la configurazione resta' ((C 'settings.json') -and (C 'hooks\session-end-wipe.ps1'))

  # --- 5 e 6. il wipe discende da un claude.exe: a mano o dall'hook -----------------
  # Il claude.exe finto esegue un .cmd che prima scrive il file di sessione del proprio
  # processo genitore, cioe' del claude.exe stesso, e poi lancia il wipe come suo figlio.
  Installa $accV -ConLibreria
  Scrivi (Join-Path $accV 'settings.json') '{}' $null
  $prelude = Join-Path $T 'prelude.ps1'
  $righePrelude = @(
    '$me = Get-CimInstance Win32_Process -Filter "ProcessId=$PID"',
    '$padre = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $me.ParentProcessId)',
    ('$f = ' + [char]39 + (Join-Path $accV 'sessions') + [char]39 + ' + "\" + $padre.ProcessId + ".json"'),
    'New-Item -ItemType Directory -Force -Path (Split-Path -Parent $f) | Out-Null',
    ('Set-Content -LiteralPath $f -Encoding ascii -Value (' + [char]39 + '{"pid":' + [char]39 + ' + $padre.ProcessId + ' + [char]39 + ',"sessionId":"' + $D + '","procStart":"' + [char]39 + ' + $padre.CreationDate.ToFileTimeUtc() + ' + [char]39 + '"}' + [char]39 + ')'))
  Set-Content -LiteralPath $prelude -Value $righePrelude -Encoding ascii
  $payload = Join-Path $T 'payload.json'
  Set-Content -LiteralPath $payload -Value ('{"session_id":"' + $D + '","hook_event_name":"SessionEnd","reason":"exit"}') -Encoding ascii
  $wipeV = Join-Path $accV 'hooks\session-end-wipe.ps1'
  $lancio = 'powershell -NoProfile -ExecutionPolicy Bypass -File "' + $wipeV + '" -BaseProva "' + $accV + '" -TempProva "' + $tmpR + '" -McpProva "' + $mcpR + '"'
  foreach ($modo in 'manuale', 'hook') {
    Scrivi (Join-Path $accV "projects\E--v\$D.jsonl") ('{"type":"queue-operation","timestamp":"' + (Get-Date).ToUniversalTime().ToString('o') + '"}') $null
    $cmd = Join-Path $T "lancia-$modo.cmd"
    $coda = if ($modo -eq 'hook') { ' < "' + $payload + '"' } else { ' < NUL' }
    Set-Content -LiteralPath $cmd -Encoding ascii -Value @('@echo off', ('powershell -NoProfile -ExecutionPolicy Bypass -File "' + $prelude + '"'), ($lancio + $coda))
    $ErrorActionPreference = 'Continue'
    & (Join-Path $bin 'claude.exe') /c $cmd 2>&1 | Out-Null
    $ErrorActionPreference = 'Stop'
    $logV = [string](Get-Content (Join-Path $accV 'session-end-wipe.log') -Raw -ErrorAction SilentlyContinue)
    if ($modo -eq 'hook') {
      # la copia rilanciata lavora dopo l'uscita del claude.exe finto: si attende il suo Fatto
      $cron = [Diagnostics.Stopwatch]::StartNew()
      while ($logV -notmatch 'Fatto\.' -and $cron.Elapsed.TotalSeconds -lt 90) {
        Start-Sleep -Milliseconds 500
        $logV = [string](Get-Content (Join-Path $accV 'session-end-wipe.log') -Raw -ErrorAction SilentlyContinue)
      }
    }
    $resta = Test-Path (Join-Path $accV "projects\E--v\$D.jsonl")
    if ($modo -eq 'manuale') {
      Write-Host 'scenario 5, a mano da dentro una sessione'
      Atteso 'il diario dice modo manuale' ($logV -match 'Modo manuale')
      Atteso 'la sessione da cui e'' stato lanciato resta' $resta
    }
    else {
      Write-Host 'scenario 6, dall''hook SessionEnd'
      Atteso 'il diario dice modo hook con la sessione che chiude' ($logV -match ('Modo hook: SessionEnd della sessione ' + $D))
      Atteso 'il modo hook si rilancia fuori dall''hook e attende la fine del processo' ($logV -match 'Rilanciato fuori dall''hook' -and $logV -match 'Modo distaccato: il PID \d+ e uscito')
      Atteso 'la copia rilanciata finisce e la sessione che chiudeva sparisce' ($logV -match 'Fatto\.' -and -not $resta)
      if (-not ($logV -match 'Fatto\.' -and -not $resta)) { Write-Host '--- diario di V, per la diagnosi:'; Write-Host $logV }
    }
  }

  # --- 7. processo vivo senza file di sessione, con account e cartella leggibili ------
  $accW = Join-Path $T '.claude-accountW'
  $accX = Join-Path $T '.claude-accountX'
  $progW = Join-Path $T 'progettoW'
  New-Item -ItemType Directory -Force -Path $progW | Out-Null
  $slugW = ($progW.TrimEnd('\') -replace '[^A-Za-z0-9]', '-')
  $E = 'eeeeeeee-1111-2222-3333-444444444444'
  $F = 'ffffffff-1111-2222-3333-444444444444'
  $G = '99999999-1111-2222-3333-444444444444'
  Scrivi (Join-Path $accW 'settings.json') '{}' $null
  Scrivi (Join-Path $accX 'settings.json') '{}' $null
  Scrivi (Join-Path $accW "projects\$slugW\$F.jsonl") '{"type":"queue-operation","timestamp":"2026-01-01T00:00:00.000Z"}' $vecchio
  Cartella (Join-Path $tmpR "$slugW\vecchia-sessione") $vecchio
  $salvato = $env:CLAUDE_CONFIG_DIR
  $env:CLAUDE_CONFIG_DIR = $accW
  $senzaFile = Start-Process -FilePath (Join-Path $bin 'claude.exe') -ArgumentList '/c', 'ping -n 300 127.0.0.1 >nul' -WorkingDirectory $progW -WindowStyle Hidden -PassThru
  $env:CLAUDE_CONFIG_DIR = $salvato
  Start-Sleep -Milliseconds 800
  $adesso = (Get-Date).AddSeconds(2)
  Scrivi (Join-Path $accW "projects\$slugW\$E.jsonl") ('{"type":"queue-operation","timestamp":"' + (Get-Date).ToUniversalTime().ToString('o') + '"}') $adesso
  Cartella (Join-Path $tmpR "$slugW\sessione-recente") $adesso
  Scrivi (Join-Path $accX "projects\E--altro\$G.jsonl") ('{"type":"queue-operation","timestamp":"' + (Get-Date).ToUniversalTime().ToString('o') + '"}') $adesso
  Installa $accW -ConLibreria
  Installa $accX -ConLibreria
  $r = Esegui $accW
  $logW = [string](Get-Content (Join-Path $accW 'session-end-wipe.log') -Raw -ErrorAction SilentlyContinue)
  $r = Esegui $accX
  $logX = [string](Get-Content (Join-Path $accX 'session-end-wipe.log') -Raw -ErrorAction SilentlyContinue)
  Write-Host 'scenario 7, processo vivo senza file di sessione'
  Atteso 'il verbale recente del progetto del processo resta' (Test-Path (Join-Path $accW "projects\$slugW\$E.jsonl"))
  Atteso 'il verbale vecchio dello stesso progetto sparisce' (-not (Test-Path (Join-Path $accW "projects\$slugW\$F.jsonl")))
  Atteso 'lo scratchpad recente del progetto resta, il vecchio sparisce' ((Test-Path (Join-Path $tmpR "$slugW\sessione-recente")) -and -not (Test-Path (Join-Path $tmpR "$slugW\vecchia-sessione")))
  Atteso 'il verbale recente di un altro account non e'' protetto' (-not (Test-Path (Join-Path $accX "projects\E--altro\$G.jsonl")))
  Atteso 'il diario riporta le rimozioni per categoria' ($logW -match 'Rimossi per categoria: ')
  if (-not ((Test-Path (Join-Path $accW "projects\$slugW\$E.jsonl")) -and -not (Test-Path (Join-Path $accX "projects\E--altro\$G.jsonl")))) { Write-Host '--- diario di W:'; Write-Host $logW; Write-Host '--- diario di X:'; Write-Host $logX }
}
finally {
  if ($senzaFile) { Stop-Process -Id $senzaFile.Id -Force -ErrorAction SilentlyContinue; Get-CimInstance Win32_Process -Filter "ParentProcessId=$($senzaFile.Id)" -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } }
  if ($finto) { Stop-Process -Id $finto.Id -Force -ErrorAction SilentlyContinue; Get-CimInstance Win32_Process -Filter "ParentProcessId=$($finto.Id)" -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } }
  Start-Sleep -Milliseconds 300
  Remove-Item -LiteralPath $T -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host ("test-wipe-per-sessione: {0} casi, {1} falliti" -f $script:casi, $script:falliti)
if ($script:falliti -gt 0) { exit 1 } else { exit 0 }
