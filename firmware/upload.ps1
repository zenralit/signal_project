param(
    [Parameter(Mandatory = $false)]
    [ValidatePattern('^COM[0-9]+$')]
    [string]$Port,

    [Parameter(Mandatory = $false)]
    [switch]$ListPorts
)

$ErrorActionPreference = 'Stop'
$firmwareDir = $PSScriptRoot
$hexFile = Join-Path $firmwareDir 'build\signalscope.hex'

try {
    $availablePorts = [System.IO.Ports.SerialPort]::GetPortNames() | Sort-Object
}
catch {
    throw "Could not query Windows serial ports: $($_.Exception.Message)"
}

if ($ListPorts) {
    if ($availablePorts.Count -eq 0) {
        Write-Host 'Windows currently reports no serial COM ports.'
    }
    else {
        Write-Host 'COM ports currently reported by Windows:'
        $availablePorts | ForEach-Object { Write-Host "  $_" }
    }
    return
}

if (-not $Port) {
    throw 'Specify the board port, for example: .\upload.ps1 -Port COM5. Use .\upload.ps1 -ListPorts to list ports detected by Windows.'
}
if ($Port -notin $availablePorts) {
    $portList = if ($availablePorts.Count -gt 0) {
        $availablePorts -join ', '
    }
    else {
        'none'
    }
    throw "Windows does not currently report $Port. Available COM ports: $portList. Check the USB cable and Device Manager."
}

. (Join-Path $firmwareDir 'toolchain.ps1')
$avrdude = Resolve-AvrTool -Name 'avrdude' -Package 'avrdude'
if (-not $avrdude) {
    throw (Get-ToolchainInstallHint)
}

$buildScript = Join-Path $firmwareDir 'build.ps1'
& $buildScript
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $hexFile)) {
    throw 'Firmware build failed; upload was not started.'
}

$arguments = @('-c', 'arduino', '-p', 'm328p', '-P', $Port, '-b', '115200', '-D')
$avrdudeConfig = Resolve-AvrdudeConfig -AvrdudePath $avrdude
if ($avrdudeConfig) {
    $arguments += @('-C', $avrdudeConfig)
}
elseif ($avrdude -match '[\\/]Arduino15[\\/]packages[\\/]') {
    throw "Could not find avrdude.conf next to Arduino's avrdude installation: $avrdude"
}
$arguments += @('-U', "flash:w:${hexFile}:i")

$previousErrorActionPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    $avrdudeOutput = & $avrdude @arguments 2>&1
    $avrdudeExitCode = $LASTEXITCODE
}
catch {
    $avrdudeOutput = @($_.Exception.Message)
    $avrdudeExitCode = 1
}
finally {
    $ErrorActionPreference = $previousErrorActionPreference
}

$outputText = ($avrdudeOutput | ForEach-Object { "$_" }) -join "`n"
$avrdudeOutput | ForEach-Object { Write-Host "$_" }
if ($avrdudeExitCode -ne 0) {
    if ($outputText -match '(?i)cannot set com-state') {
        $driverDetails = ''
        $portDevice = Get-PnpDevice -PresentOnly |
            Where-Object { $_.Class -eq 'Ports' -and $_.FriendlyName -match "\($Port\)$" } |
            Select-Object -First 1
        if ($portDevice) {
            $driverVersion = (Get-PnpDeviceProperty -InstanceId $portDevice.InstanceId `
                -KeyName 'DEVPKEY_Device_DriverVersion' -ErrorAction SilentlyContinue).Data
            if ($driverVersion) {
                $driverDetails = "Detected adapter: $($portDevice.FriendlyName); driver version: $driverVersion."
            }
            else {
                $driverDetails = "Detected adapter: $($portDevice.FriendlyName)."
            }
        }
        throw @"
avrdude opened $Port, but Windows rejected the requested serial-port settings (SetCommState).
$driverDetails
This is a USB-serial driver/configuration issue, not a firmware compile error. Close Arduino Serial Monitor/Plotter and SignalScope, unplug/reconnect the board, and retry.
If it persists, open Device Manager > Ports > USB-SERIAL CH340 > Properties > Driver. Update or reinstall the official WCH CH340 driver; if the problem began after an update, try Roll Back Driver. Reconnect the board (or restart Windows), then retry.
You can test the same 8-N-1 settings with: mode ${Port}: BAUD=115200 PARITY=N DATA=8 STOP=1
"@
    }
    if ($outputText -match '(?i)(cannot open port|unable to open port|access is denied|access denied)') {
        throw @"
Could not open $Port (Windows access denied).
The port exists, but another application may have it open. Close SignalScope, Arduino Serial Monitor/Plotter, and any other serial terminal, then retry.
Check Windows Device Manager to confirm that $Port is the Uno's current port.
"@
    }
    throw "Firmware upload to $Port failed with avrdude exit code $avrdudeExitCode."
}

Write-Host "Firmware uploaded to $Port."
