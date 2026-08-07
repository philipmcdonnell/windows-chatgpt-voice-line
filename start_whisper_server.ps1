$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$server = Join-Path $projectRoot "tools\whisper.cpp\v1.9.2\Release\whisper-server.exe"
$model = Join-Path $projectRoot "models\ggml-base.en.bin"
$stdout = Join-Path $projectRoot "whisper-server.stdout.log"
$stderr = Join-Path $projectRoot "whisper-server.stderr.log"

if (-not (Test-Path -LiteralPath $server)) {
    throw "Whisper server was not found at $server"
}
if (-not (Test-Path -LiteralPath $model)) {
    throw "Whisper model was not found at $model"
}

try {
    $existing = Invoke-WebRequest -Uri "http://127.0.0.1:2022/" -UseBasicParsing -TimeoutSec 1
} catch {
    $existing = $null
}
if ($existing -and $existing.StatusCode -eq 200) {
    Write-Output "Whisper server is already listening on port 2022."
    exit 0
}

$quotedModel = '"' + $model + '"'
$arguments = @(
    "--model", $quotedModel,
    "--host", "127.0.0.1",
    "--port", "2022",
    "--language", "en",
    "--threads", [Environment]::ProcessorCount,
    "--no-gpu",
    "--no-timestamps",
    "--suppress-nst"
)

$process = Start-Process `
    -FilePath $server `
    -ArgumentList $arguments `
    -WorkingDirectory (Split-Path -Parent $server) `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -WindowStyle Hidden `
    -PassThru

$deadline = (Get-Date).AddSeconds(30)
do {
    Start-Sleep -Milliseconds 250
    if ($process.HasExited) {
        throw "Whisper server exited during startup. See $stderr"
    }
    try {
        $ready = Invoke-WebRequest -Uri "http://127.0.0.1:2022/" -UseBasicParsing -TimeoutSec 1
    } catch {
        $ready = $null
    }
} until (($ready -and $ready.StatusCode -eq 200) -or (Get-Date) -ge $deadline)

if (-not $ready -or $ready.StatusCode -ne 200) {
    Stop-Process -Id $process.Id -ErrorAction SilentlyContinue
    throw "Whisper server did not listen on port 2022 within 30 seconds."
}

Write-Output "Whisper server started on http://127.0.0.1:2022/inference (PID $($process.Id))."
