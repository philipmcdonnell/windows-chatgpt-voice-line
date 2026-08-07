[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$CodexWorkspace,

    [Parameter(Mandatory = $true)]
    [string]$UserName,

    [string]$AssistantName = "Alfred",
    [string]$Voice = "bm_george"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspace = (Resolve-Path -LiteralPath $CodexWorkspace).Path

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "Install uv from https://docs.astral.sh/uv/ and run setup.ps1 again."
    }
    winget install --id astral-sh.uv --exact --accept-package-agreements --accept-source-agreements
    $uvCandidate = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
    if (Test-Path -LiteralPath $uvCandidate) {
        $uv = $uvCandidate
    } else {
        throw "uv was installed, but this terminal cannot see it yet. Open a new PowerShell window and rerun setup.ps1."
    }
} else {
    $uv = (Get-Command uv).Source
}

& $uv python install 3.12
& $uv venv --python 3.12 (Join-Path $projectRoot ".venv")
& $uv pip install --python (Join-Path $projectRoot ".venv\Scripts\python.exe") -r (Join-Path $projectRoot "requirements.txt")

$whisperRoot = Join-Path $projectRoot "tools\whisper.cpp\v1.9.2"
$whisperServer = Join-Path $whisperRoot "Release\whisper-server.exe"
if (-not (Test-Path -LiteralPath $whisperServer)) {
    $archive = Join-Path $env:TEMP "whisper-bin-x64-v1.9.2.zip"
    New-Item -ItemType Directory -Force -Path $whisperRoot | Out-Null
    Invoke-WebRequest -Uri "https://github.com/ggml-org/whisper.cpp/releases/download/v1.9.2/whisper-bin-x64.zip" -OutFile $archive
    Expand-Archive -LiteralPath $archive -DestinationPath $whisperRoot -Force
    Remove-Item -LiteralPath $archive -Force
}

$modelsRoot = Join-Path $projectRoot "models"
$kokoroRoot = Join-Path $modelsRoot "kokoro"
New-Item -ItemType Directory -Force -Path $kokoroRoot | Out-Null

$downloads = @{
    (Join-Path $modelsRoot "ggml-base.en.bin") = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin"
    (Join-Path $kokoroRoot "kokoro-v1.0.onnx") = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
    (Join-Path $kokoroRoot "voices-v1.0.bin") = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
}
foreach ($destination in $downloads.Keys) {
    if (-not (Test-Path -LiteralPath $destination)) {
        Invoke-WebRequest -Uri $downloads[$destination] -OutFile $destination
    }
}

$configuration = [ordered]@{
    assistant_name = $AssistantName
    user_name = $UserName
    codex_workspace = $workspace
    voice = $Voice
    forms_of_address = @("sir", "kind sir")
}
$configuration | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $projectRoot "config.json") -Encoding utf8

& (Join-Path $projectRoot ".venv\Scripts\python.exe") -m compileall -q $projectRoot
& (Join-Path $projectRoot ".venv\Scripts\python.exe") -m unittest discover -s (Join-Path $projectRoot "tests") -v

Write-Host ""
Write-Host "Voice Line setup is complete."
Write-Host "Run run-voice-line.bat, then hold Right Ctrl while speaking."
