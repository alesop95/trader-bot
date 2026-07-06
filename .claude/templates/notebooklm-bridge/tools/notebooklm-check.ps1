<#
.SYNOPSIS
  Verifica di disponibilita' di NotebookLM (piano gratuito) per il pacchetto notebooklm-bridge.

.DESCRIPTION
  Enumera i browser Chromium presenti sulla macchina (Chrome, Edge) e, per ciascuno, legge dal
  file "Local State" i profili configurati con nome ed email dell'account Google associato, cosi'
  da mostrare quali account sono candidati all'uso di NotebookLM. Segnala inoltre se esiste gia'
  un profilo persistito del server di automazione notebooklm-mcp (login assistito gia' fatto) e se
  nel .mcp.json del progetto risulta configurato un MCP di automazione del browser.

  Cosa NON puo' fare: dall'esterno del browser non e' possibile confermare che un account sia
  davvero loggato su NotebookLM e ne abbia accesso. Quella conferma e' visiva. Lo script quindi
  chiude indicando il passo manuale: uno screenshot di notebooklm.google.com loggato, che l'agente
  legge secondo la regola manual-screenshots.md.

  Piano gratuito tassativo: nessuna API Enterprise a pagamento e' coinvolta.

.NOTES
  Variante Windows. La variante Linux e' notebooklm-check.sh.
#>

$ErrorActionPreference = 'Stop'

function Read-ChromiumProfiles {
    param([string]$LocalStatePath, [string]$BrowserName)
    if (-not (Test-Path $LocalStatePath)) { return }
    try {
        $state = Get-Content -Raw -LiteralPath $LocalStatePath | ConvertFrom-Json
    } catch {
        Write-Host "  [$BrowserName] Local State presente ma non leggibile: $($_.Exception.Message)"
        return
    }
    $cache = $state.profile.info_cache
    if ($null -eq $cache) {
        Write-Host "  [$BrowserName] nessun profilo trovato nel Local State"
        return
    }
    Write-Host "  [$BrowserName]"
    foreach ($p in $cache.PSObject.Properties) {
        $info  = $p.Value
        $label = if ($info.name) { $info.name } else { $p.Name }
        $email = if ($info.user_name) { $info.user_name } else { '(nessun account Google collegato al profilo)' }
        Write-Host ("    - profilo '{0}'  ->  {1}" -f $label, $email)
    }
}

Write-Host ''
Write-Host '=== notebooklm-bridge: verifica di disponibilita (NotebookLM gratuito) ==='
Write-Host ''
Write-Host 'Account Google candidati (dai profili dei browser Chromium):'

$chromeLocalState = Join-Path $env:LOCALAPPDATA 'Google\Chrome\User Data\Local State'
$edgeLocalState   = Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\User Data\Local State'

$anyBrowser = $false
if (Test-Path $chromeLocalState) { $anyBrowser = $true; Read-ChromiumProfiles -LocalStatePath $chromeLocalState -BrowserName 'Chrome' }
if (Test-Path $edgeLocalState)   { $anyBrowser = $true; Read-ChromiumProfiles -LocalStatePath $edgeLocalState   -BrowserName 'Edge' }
if (-not $anyBrowser) {
    Write-Host '  nessun browser Chromium (Chrome/Edge) trovato: il modo manuale richiede un browser con un account Google loggato su NotebookLM'
}

Write-Host ''
Write-Host 'Modo assistito (opzionale, community, zona grigia dei ToS):'

$mcpProfile = Join-Path $env:APPDATA 'notebooklm-mcp\chrome_profile'
if (Test-Path $mcpProfile) {
    Write-Host "  - profilo notebooklm-mcp gia' presente: $mcpProfile (login assistito probabilmente gia' persistito)"
} else {
    Write-Host '  - nessun profilo notebooklm-mcp persistito'
}

$mcpConfig = '.mcp.json'
if (Test-Path $mcpConfig) {
    $raw = Get-Content -Raw -LiteralPath $mcpConfig
    if ($raw -match 'notebooklm') { Write-Host '  - .mcp.json contiene una voce notebooklm' }
    if ($raw -match 'playwright') { Write-Host '  - .mcp.json contiene una voce playwright' }
    if ($raw -notmatch 'notebooklm' -and $raw -notmatch 'playwright') {
        Write-Host '  - .mcp.json presente ma senza MCP di automazione del browser (notebooklm/playwright)'
    }
} else {
    Write-Host '  - nessun .mcp.json nel progetto: il modo assistito richiederebbe di connettere prima un MCP'
}

Write-Host ''
Write-Host 'Passo manuale di conferma (obbligatorio):'
Write-Host '  Lo stato di login non risulta verificabile da qui. Apri https://notebooklm.google.com'
Write-Host '  loggato con account scelto e fornisci uno screenshot: agente lo legge per confermare'
Write-Host '  account attivo prima di avviare il loop (regola manual-screenshots.md).'
Write-Host ''
