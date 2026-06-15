#requires -Version 5.1
<#
.SYNOPSIS
  Bootstrap dell'ambiente LaTeX (TinyTeX) per Windows, guidato dal manifesto.
.DESCRIPTION
  Sezione 13 di .claude/PROJECT-SYSTEM.md. Localizza TinyTeX (installazione
  user-local condivisa fra i progetti), e se assente lo installa; poi installa i
  pacchetti elencati in tex-packages.txt con tlmgr, e verifica con una compilazione
  minima. Non attiva shell interattive: invoca i binari dell'ambiente per percorso,
  cosi' il comportamento e' identico in locale e in CI.
.PARAMETER Reinstall
  Rimuove l'installazione TinyTeX esistente e la ricrea da zero.
.PARAMETER TexDir
  Forza la cartella di installazione di TinyTeX (default: $env:APPDATA\TinyTeX).
.PARAMETER SkipPackages
  Salta l'installazione dei pacchetti dal manifesto (solo bootstrap della distribuzione).
.PARAMETER Manifest
  Percorso del manifesto dei pacchetti (default: tex-packages.txt nella radice del progetto).
.EXAMPLE
  pwsh scripts/setup-tex.ps1
.EXAMPLE
  pwsh scripts/setup-tex.ps1 -Reinstall
#>
[CmdletBinding()]
param(
    [switch]$Reinstall,
    [string]$TexDir,
    [switch]$SkipPackages,
    [string]$Manifest
)

$ErrorActionPreference = 'Stop'

# --- Percorsi -------------------------------------------------------------------
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
if (-not $Manifest) { $Manifest = Join-Path $ProjectRoot 'tex-packages.txt' }
# Installazione user-local condivisa: default standard di TinyTeX su Windows.
if (-not $TexDir)   { $TexDir   = Join-Path $env:APPDATA 'TinyTeX' }

function Find-Tlmgr {
    param([string]$Root)
    # 1) gia' sul PATH
    $cmd = Get-Command tlmgr -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    # 2) dentro la root TinyTeX (le versioni recenti usano bin\windows, le vecchie bin\win32)
    foreach ($rel in @('bin\windows\tlmgr.bat', 'bin\win32\tlmgr.bat')) {
        $p = Join-Path $Root $rel
        if (Test-Path $p) { return $p }
    }
    return $null
}

# --- Reinstallazione su richiesta ----------------------------------------------
if ($Reinstall -and (Test-Path $TexDir)) {
    Write-Host "[setup-tex] Rimuovo l'installazione esistente: $TexDir"
    Remove-Item -Recurse -Force $TexDir
}

# --- Localizza o installa TinyTeX ----------------------------------------------
$tlmgr = Find-Tlmgr -Root $TexDir
if (-not $tlmgr) {
    Write-Host "[setup-tex] TinyTeX non trovato. Installazione in: $TexDir"
    # Windows PowerShell 5.1 non abilita TLS 1.2 di default: necessario per il download.
    [Net.ServicePointManager]::SecurityProtocol =
        [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    # L'installer ufficiale crea la sottocartella TinyTeX dentro TINYTEX_DIR, quindi gli si
    # passa la cartella PADRE di $TexDir; il nome finale di $TexDir deve essere "TinyTeX".
    if ((Split-Path -Leaf $TexDir) -ne 'TinyTeX') {
        throw "[setup-tex] -TexDir deve terminare con 'TinyTeX' (l'installer crea quella sottocartella). Valore: $TexDir"
    }
    $env:TINYTEX_DIR = Split-Path -Parent $TexDir
    # Si scarica l'installer PowerShell ufficiale con Invoke-WebRequest (gestisce TLS e il
    # salvataggio del file) e lo si esegue in un processo figlio con policy Bypass. Non si usa
    # il batch ufficiale, che nel suo interno invoca curl con apici singoli e fallisce su cmd.
    $installer = Join-Path $env:TEMP 'install-tinytex.ps1'
    Invoke-WebRequest -UseBasicParsing 'https://tinytex.yihui.org/install-bin-windows.ps1' -OutFile $installer
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer
    $tlmgr = Find-Tlmgr -Root $TexDir
    if (-not $tlmgr) {
        throw "[setup-tex] Installazione di TinyTeX fallita: tlmgr non trovato sotto $TexDir o sul PATH."
    }
}
Write-Host "[setup-tex] tlmgr: $tlmgr"
$TexBin = Split-Path -Parent $tlmgr

# --- Aggiorna tlmgr e installa i pacchetti dal manifesto ------------------------
Write-Host "[setup-tex] Aggiorno tlmgr ..."
& $tlmgr update --self

if (-not $SkipPackages) {
    if (-not (Test-Path $Manifest)) { throw "[setup-tex] Manifesto non trovato: $Manifest" }
    # Una voce per riga; si rimuovono i commenti inline (# ...) e gli spazi, come nello script .sh.
    $pkgs = Get-Content $Manifest |
        ForEach-Object { ($_ -replace '#.*$', '').Trim() } |
        Where-Object { $_ }
    if ($pkgs.Count -gt 0) {
        Write-Host "[setup-tex] Installo $($pkgs.Count) pacchetti dal manifesto ..."
        & $tlmgr install @pkgs
    }
}

# --- Verifica con una compilazione minima --------------------------------------
$pdflatex = Join-Path $TexBin 'pdflatex.exe'
if (-not (Test-Path $pdflatex)) { $pdflatex = Join-Path $TexBin 'pdflatex' }
Write-Host "[setup-tex] Verifica: compilo un documento di prova ..."
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("texcheck_" + [System.IO.Path]::GetRandomFileName().Replace('.', ''))
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$probe = Join-Path $tmp 'probe.tex'
@'
\documentclass{article}
\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}
\usepackage[italian]{babel}\usepackage{siunitx}\usepackage{circuitikz}
\begin{document}Prova \SI{600}{\ohm}.\end{document}
'@ | Set-Content -Encoding utf8 $probe
& $pdflatex -interaction=nonstopmode -halt-on-error -output-directory $tmp $probe | Out-Null
$ok = (Test-Path (Join-Path $tmp 'probe.pdf'))
Remove-Item -Recurse -Force $tmp
if (-not $ok) { throw "[setup-tex] Verifica fallita: il documento di prova non ha prodotto un PDF." }

Write-Host "[setup-tex] OK. Ambiente LaTeX pronto."
Write-Host "[setup-tex] Per compilare il progetto: scripts/build.ps1"
Write-Host "[setup-tex] Nota: aggiungi '$TexBin' al PATH per usare pdflatex/latexmk a mano."
