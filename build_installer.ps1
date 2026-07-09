$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "== DELTA Gestor :: Build Windows =="

$Python = if ($env:DELTA_BUILD_PYTHON) { $env:DELTA_BUILD_PYTHON } else { "python" }

if (Test-Path ".\build") {
    Remove-Item ".\build" -Recurse -Force
}
if (Test-Path ".\dist\DeltaGestor") {
    Remove-Item ".\dist\DeltaGestor" -Recurse -Force
}

Write-Host "Rodando PyInstaller..."
& $Python -m PyInstaller ".\DeltaGestor.spec" --clean --noconfirm

$IsccCandidates = @(
    "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
)
$Iscc = $IsccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $Iscc) {
    Write-Warning "Inno Setup 6 nao encontrado. Instale o Inno Setup e execute: ISCC.exe .\installer\DeltaGestor.iss"
    exit 0
}

Write-Host "Gerando instalador Inno Setup..."
& $Iscc ".\installer\DeltaGestor.iss"

Write-Host "Build concluido."
