# Verifica i componenti prima di passare una directory a Remove-Item -Recurse.
function Test-TemporaneoLocale($percorso, $radice) {
  $radice = [IO.Path]::GetFullPath($radice).TrimEnd('\')
  $pieno = [IO.Path]::GetFullPath($percorso).TrimEnd('\')
  if ($pieno -ne $radice -and -not $pieno.StartsWith($radice + '\', 'OrdinalIgnoreCase')) { return $false }
  for ($p = $pieno; $p; $p = Split-Path -Parent $p) {
    $antenato = Get-Item -LiteralPath $p -Force -ErrorAction Stop
    if ($antenato.Attributes -band [IO.FileAttributes]::ReparsePoint) { return $false }
  }
  $visita = New-Object 'System.Collections.Generic.Stack[System.IO.FileSystemInfo]'
  $visita.Push((Get-Item -LiteralPath $pieno -Force -ErrorAction Stop))
  while ($visita.Count) {
    $item = $visita.Pop()
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { return $false }
    if ($item -is [IO.DirectoryInfo]) {
      foreach ($figlio in Get-ChildItem -LiteralPath $item.FullName -Force -ErrorAction Stop) { $visita.Push($figlio) }
    }
  }
  return $true
}
