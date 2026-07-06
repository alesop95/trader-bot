#requires -Version 5.1
<#
.SYNOPSIS
  Compila il documento LaTeX del progetto in modo riproducibile (Windows).
.DESCRIPTION
  Sezione 13 di .claude/PROJECT-SYSTEM.md. Trova latexmk nell'ambiente TinyTeX
  user-local (o sul PATH) e compila con l'engine pdflatex fissato in .latexmkrc.
  Invoca il binario per percorso: nessuna attivazione interattiva di shell.
.PARAMETER Main
  File .tex principale. Se omesso e nella radice c'e' un solo .tex, usa quello.
.PARAMETER Clean
  Rimuove i file ausiliari (latexmk -c) e termina.
.PARAMETER CleanAll
  Rimuove ausiliari e PDF (latexmk -C) e termina.
.PARAMETER TexDir
  Cartella di TinyTeX (default: $env:APPDATA\TinyTeX).
#>
[CmdletBinding()]
param(
    [string]$Main,
    [switch]$Clean,
    [switch]$CleanAll,
    [string]$TexDir
)

$ErrorActionPreference = 'Stop'
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
if (-not $TexDir) { $TexDir = Join-Path $env:APPDATA 'TinyTeX' }

function Find-Bin {
    param([string]$Name, [string]$Root)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($rel in @("bin\windows\$Name.exe", "bin\windows\$Name", "bin\win32\$Name.exe", "bin\win32\$Name")) {
        $p = Join-Path $Root $rel
        if (Test-Path $p) { return $p }
    }
    return $null
}

$latexmk = Find-Bin -Name 'latexmk' -Root $TexDir
if (-not $latexmk) {
    throw "[build] latexmk non trovato. Esegui prima scripts/setup-tex.ps1."
}

# Determina il file principale.
if (-not $Main) {
    $texFiles = Get-ChildItem -Path $ProjectRoot -Filter '*.tex' -File
    if ($texFiles.Count -eq 1) { $Main = $texFiles[0].Name }
    elseif ($texFiles.Count -eq 0) { throw "[build] Nessun .tex nella radice: specifica -Main." }
    else { throw "[build] Piu' .tex nella radice: specifica -Main <file.tex>." }
}

Push-Location $ProjectRoot
try {
    # -cd: latexmk cambia directory di lavoro in quella del file principale, cosi' il PDF e
    # gli ausiliari finiscono accanto al sorgente (es. docs/diploma.pdf) invece che nella
    # radice del progetto, dove pdflatex scriverebbe altrimenti per default quando $Main
    # e' in una sottocartella (osservato dal vivo nel pilota 2026-07-03).
    if ($Clean)    { & $latexmk -cd -c $Main; if ($LASTEXITCODE -ne 0) { throw "[build] latexmk -c fallito (exit $LASTEXITCODE)." }; return }
    if ($CleanAll) { & $latexmk -cd -C $Main; if ($LASTEXITCODE -ne 0) { throw "[build] latexmk -C fallito (exit $LASTEXITCODE)." }; return }
    Write-Host "[build] Compilo $Main con latexmk (pdflatex) ..."
    & $latexmk -cd -pdf $Main
    if ($LASTEXITCODE -ne 0) { throw "[build] Compilazione fallita (latexmk exit $LASTEXITCODE)." }
    $MainDir = Split-Path $Main -Parent
    $OutName = [System.IO.Path]::GetFileNameWithoutExtension($Main) + '.pdf'
    $OutPath = if ($MainDir) { Join-Path $MainDir $OutName } else { $OutName }
    Write-Host "[build] Fatto: $OutPath"
}
finally { Pop-Location }
