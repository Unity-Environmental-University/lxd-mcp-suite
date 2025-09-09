param(
  [Parameter(Mandatory=$true)][string]$Server,
  [switch]$InitOnly,
  [string]$PayloadFile,
  [string]$PayloadInline,
  [string]$Tool,
  [string]$ArgsJson = '{}'
)

$ErrorActionPreference = 'Stop'

# If inline payload provided, write to temp file without BOM to avoid JSON decode errors
if ($PayloadInline) {
  $PayloadFile = Join-Path $env:TEMP ("mcp_payload_" + [System.Guid]::NewGuid().ToString('N') + ".json")
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($PayloadFile, $PayloadInline, $utf8NoBom)
}

# Resolve Python client path relative to this script
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$pyClient = Join-Path (Split-Path -Parent $here) 'python/mcp_call.py'
if (-not (Test-Path $pyClient)) {
  throw "Python client not found at: $pyClient"
}

$argsList = @('--server', $Server)
if ($InitOnly) { $argsList += '--init-only' }
if ($PayloadFile) { $argsList += @('--payload-file', $PayloadFile) }
if ($Tool) { $argsList += @('--tool', $Tool, '--args', $ArgsJson) }

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'python'
$psi.ArgumentList.Add($pyClient)
foreach ($a in $argsList) { $psi.ArgumentList.Add($a) }
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false

$p = New-Object System.Diagnostics.Process
$p.StartInfo = $psi
$p.Start() | Out-Null
$stdout = $p.StandardOutput.ReadToEnd()
$stderr = $p.StandardError.ReadToEnd()
$p.WaitForExit()

if ($p.ExitCode -ne 0) { Write-Error $stderr; exit $p.ExitCode }
Write-Output $stdout.Trim()

