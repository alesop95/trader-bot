# ============================================================================
# latest-screenshot.ps1
# Stampa il percorso dell'immagine PIU RECENTE nella cartella di cattura
# (Screenpresso su Windows) e la sua eta in secondi. Serve all'agente per
# leggere lo screenshot che l'utente ha appena catturato per un passo manuale
# e visivo dello sviluppo. Vedi .claude/rules/manual-screenshots.md.
#
# Uso:
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/latest-screenshot.ps1
#   ... -Folder "<altra cartella>"   per una cartella di cattura diversa
#   ... -MaxAgeSeconds 180           pretende che lo screenshot sia recente
#                                    (default 0 = nessun limite di eta)
# Esce 0 se trova un'immagine valida, 1 altrimenti.
# ============================================================================
param(
  [string]$Folder = (Join-Path $env:USERPROFILE 'Pictures\Screenpresso'),
  [int]$MaxAgeSeconds = 0
)
if (-not (Test-Path -LiteralPath $Folder)) {
  Write-Output "ERRORE: cartella di cattura non trovata: $Folder"
  Write-Output "Rileva il percorso reale di Screenpresso e passalo con -Folder."
  exit 1
}
$img = Get-ChildItem -LiteralPath $Folder -File |
       Where-Object { $_.Extension -in '.png', '.jpg', '.jpeg', '.bmp', '.gif' } |
       Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $img) { Write-Output "ERRORE: nessuna immagine in $Folder"; exit 1 }

$age = [int]((Get-Date) - $img.LastWriteTime).TotalSeconds
if ($MaxAgeSeconds -gt 0 -and $age -gt $MaxAgeSeconds) {
  Write-Output ("ATTENZIONE: l'immagine piu recente ha {0}s, oltre il limite di {1}s: {2}" -f $age, $MaxAgeSeconds, $img.FullName)
  Write-Output "Probabilmente non e' lo screenshot appena catturato. Chiedi conferma all'utente."
  exit 1
}
Write-Output $img.FullName
Write-Output ("eta: {0}s; modificato: {1}" -f $age, $img.LastWriteTime)
exit 0
