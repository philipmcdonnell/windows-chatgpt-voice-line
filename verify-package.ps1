$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$required = @(
    "README.md", "LICENSE", "ATTRIBUTION.md", "config.example.json",
    "setup.ps1", "run-voice-line.bat", "voice_line.py", "brain.py",
    "ears.py", "mouth.py", "ptt.py", "thinking_sound.py",
    "windows-voice-line-prompt-chatgpt.md"
)

foreach ($file in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $root $file))) {
        throw "Missing required package file: $file"
    }
}

$privatePatterns = @(
    "C:\\Users\\phil", "Promise Sanctuary", "Options Workstation",
    "Black Cat Technologies"
)
$sourceFiles = Get-ChildItem -LiteralPath $root -Recurse -File |
    Where-Object {
        $_.Name -ne "config.json" -and
        $_.Name -ne "verify-package.ps1" -and
        $_.Extension -notin @(".pyc", ".wav") -and
        $_.FullName -notmatch "\\.git\\|\\.venv\\|\\models\\|\\tools\\|\\__pycache__\\"
    }
foreach ($pattern in $privatePatterns) {
    $matches = $sourceFiles | Select-String -Pattern $pattern -SimpleMatch
    if ($matches) {
        throw "Private or machine-specific text found: $pattern"
    }
}

Write-Host "Package verification passed."
