# test-pulisci-codex-quarantena.ps1
# Prova di Pulisci-Codex.ps1 dopo un avvio finito senza uscita ordinata (L-018, 2026-11-24).
# Costruisce un profilo utente finto con una radice .codex-account9, due rollout e un segnale
# avvii-in-corso\<pid>.json di un processo che non esiste: il rollout scritto dopo l'avvio
# deve finire in quarantena, quello piu' vecchio no, e il segnale deve sparire. Un secondo
# giro con un segnale del processo di questa prova, che e' vivo, non deve copiare niente.
# Il profilo finto si passa al processo figlio con USERPROFILE, quindi le radici vere non si
# toccano; `codex delete` sulle sessioni finte puo' fallire, e lo script lo dice e prosegue.
# Uso:  powershell -NoProfile -ExecutionPolicy Bypass -File .claude/templates/agenti-terminale/tests/test-pulisci-codex-quarantena.ps1
$ErrorActionPreference = 'Stop'
$pulisci = Join-Path (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)) 'tools\Pulisci-Codex.ps1'
$T = Join-Path ([IO.Path]::GetTempPath()) ('prova-codex-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
$radice = Join-Path $T '.codex-account9'
$quar = Join-Path $T 'quarantena'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$script:casi = 0; $script:falliti = 0
function Atteso($nome, $cond) {
  $script:casi++
  if ($cond) { Write-Host "  ok    $nome" } else { $script:falliti++; Write-Host "  FALLITO $nome" -ForegroundColor Red }
}
function Rollout($id, $quando) {
  $f = Join-Path $radice "sessions\2026\11\24\rollout-2026-11-24T10-00-00-$id.jsonl"
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $f) | Out-Null
  [IO.File]::WriteAllText($f, '{"type":"session_meta","payload":{"cwd":"E:\\prova"}}' + "`n", $utf8)
  (Get-Item -LiteralPath $f).LastWriteTime = $quando
  return $f
}
function Esegui {
  $vecchio = $env:USERPROFILE
  $env:USERPROFILE = $T
  try {
    $ErrorActionPreference = 'Continue'
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $pulisci -Account 9 -QuarantenaProva $quar 2>&1
    return ($out -join "`n")
  }
  finally { $env:USERPROFILE = $vecchio; $ErrorActionPreference = 'Stop' }
}
try {
  New-Item -ItemType Directory -Force -Path $radice | Out-Null
  Set-Content -LiteralPath (Join-Path $radice 'config.toml') -Value '' -Encoding ascii
  $avvio = (Get-Date).AddMinutes(-30)
  $prima = Rollout '01a1aaaa-0000-7000-8000-000000000001' (Get-Date).AddHours(-5)
  $dopo = Rollout '01a1bbbb-0000-7000-8000-000000000002' (Get-Date).AddMinutes(-10)
  $segnale = Join-Path $radice 'avvii-in-corso\999999.json'
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $segnale) | Out-Null
  Set-Content -LiteralPath $segnale -Encoding ascii -Value ('{"pid":999999,"procStart":"1","avvio":"' + $avvio.ToString('yyyy-MM-ddTHH:mm:ss') + '"}')

  $testo = Esegui
  $copie = @(Get-ChildItem -LiteralPath $quar -Recurse -Filter 'rollout-*.jsonl' -ErrorAction SilentlyContinue)
  Write-Host 'avvio orfano'
  Atteso 'il rollout scritto dopo l''avvio e'' in quarantena, al percorso relativo' ($copie.Count -eq 1 -and $copie[0].Name -like '*01a1bbbb*' -and $copie[0].FullName -match '-codex-account9\\sessions\\2026\\11\\24\\')
  Atteso 'il rollout precedente all''avvio non e'' copiato' (-not ($copie | Where-Object { $_.Name -like '*01a1aaaa*' }))
  Atteso 'il segnale orfano sparisce' (-not (Test-Path -LiteralPath $segnale))
  Atteso 'la radice di quarantena porta il LEGGIMI' (Test-Path -LiteralPath (Join-Path $quar 'LEGGIMI.txt'))
  if ($copie.Count -ne 1) { Write-Host $testo }

  Remove-Item -LiteralPath $quar -Recurse -Force -ErrorAction SilentlyContinue
  $dopo2 = Rollout '01a1cccc-0000-7000-8000-000000000003' (Get-Date).AddMinutes(-5)
  $me = Get-CimInstance Win32_Process -Filter "ProcessId=$PID"
  $segnaleVivo = Join-Path $radice ("avvii-in-corso\{0}.json" -f $PID)
  Set-Content -LiteralPath $segnaleVivo -Encoding ascii -Value ('{"pid":' + $PID + ',"procStart":"' + $me.CreationDate.ToFileTimeUtc() + '","avvio":"' + $avvio.ToString('yyyy-MM-ddTHH:mm:ss') + '"}')
  $testo = Esegui
  Write-Host 'avvio vivo'
  Atteso 'con il processo del segnale vivo non si copia niente' (-not (Test-Path -LiteralPath $quar))
  Atteso 'il segnale di un avvio vivo resta' (Test-Path -LiteralPath $segnaleVivo)
}
finally { Remove-Item -LiteralPath $T -Recurse -Force -ErrorAction SilentlyContinue }
Write-Host ("test-pulisci-codex-quarantena: {0} casi, {1} falliti" -f $script:casi, $script:falliti)
if ($script:falliti -gt 0) { exit 1 } else { exit 0 }
