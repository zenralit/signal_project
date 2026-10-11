function Get-ArduinoDataDirectories {
    $roots = @()
    if ($env:ARDUINO_DIRECTORIES_DATA) {
        $roots += $env:ARDUINO_DIRECTORIES_DATA
    }
    if ($env:LOCALAPPDATA) {
        $roots += (Join-Path $env:LOCALAPPDATA 'Arduino15')
    }
    if ($env:APPDATA) {
        $roots += (Join-Path $env:APPDATA 'Arduino15')
    }
    return @($roots | Select-Object -Unique | Where-Object { Test-Path $_ })
}

function Resolve-AvrTool {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Package
    )

    $fromPath = Get-Command $Name -ErrorAction SilentlyContinue
    if ($fromPath) {
        return $fromPath.Source
    }

    foreach ($dataDirectory in Get-ArduinoDataDirectories) {
        $toolRoot = Join-Path $dataDirectory "packages\arduino\tools\$Package"
        if (-not (Test-Path $toolRoot)) {
            continue
        }
        $versions = Get-ChildItem -Path $toolRoot -Directory |
            Sort-Object -Property Name -Descending
        foreach ($version in $versions) {
            $candidate = Join-Path $version.FullName "bin\$Name.exe"
            if (Test-Path $candidate) {
                return $candidate
            }
        }
    }
    return $null
}

function Resolve-AvrdudeConfig {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AvrdudePath
    )

    $toolDirectory = Split-Path -Parent (Split-Path -Parent $AvrdudePath)
    $candidates = @(
        (Join-Path $toolDirectory 'etc\avrdude.conf'),
        (Join-Path $toolDirectory 'bin\avrdude.conf'),
        (Join-Path $toolDirectory 'avrdude.conf')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    return $null
}

function Get-ToolchainInstallHint {
    return @"
AVR compiler tools are missing. Install Arduino IDE, then install the "Arduino AVR Boards" core from Boards Manager.
Alternatively, install Arduino CLI, then run:
  arduino-cli core update-index
  arduino-cli core install arduino:avr
The scripts automatically search Arduino's per-user Arduino15 package directory; adding AVR tools to PATH is not required.
"@
}
