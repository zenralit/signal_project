$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$srcDir = Join-Path $root 'firmware\src'
$includeDir = Join-Path $root 'firmware\include'
$buildDir = Join-Path $root 'firmware\build'

. (Join-Path $PSScriptRoot 'toolchain.ps1')
$avrGcc = Resolve-AvrTool -Name 'avr-gcc' -Package 'avr-gcc'
$avrObjcopy = Resolve-AvrTool -Name 'avr-objcopy' -Package 'avr-gcc'
if (-not $avrGcc -or -not $avrObjcopy) {
    throw (Get-ToolchainInstallHint)
}

New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

$srcFiles = Get-ChildItem -Path $srcDir -Filter '*.c' | Sort-Object Name
foreach ($src in $srcFiles) {
    $obj = Join-Path $buildDir ($src.BaseName + '.o')
    & $avrGcc -Wall -Wextra -Os -mmcu=atmega328p -DF_CPU=16000000UL "-I$includeDir" -c $src.FullName -o $obj
    if ($LASTEXITCODE -ne 0) { throw "Compilation failed for $($src.FullName)" }
}

$objects = Get-ChildItem -Path $buildDir -Filter '*.o' | Sort-Object Name | ForEach-Object { $_.FullName }
& $avrGcc -mmcu=atmega328p $objects -o (Join-Path $buildDir 'signalscope.elf')
if ($LASTEXITCODE -ne 0) { throw 'Linking failed.' }

& $avrObjcopy -O ihex -R .eeprom (Join-Path $buildDir 'signalscope.elf') (Join-Path $buildDir 'signalscope.hex')
if ($LASTEXITCODE -ne 0) { throw 'objcopy failed.' }

Write-Host "Firmware build complete: $(Join-Path $buildDir 'signalscope.hex')"
