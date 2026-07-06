param(
    [string]$Target = (Join-Path $HOME ".codex\skills"),
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsSrc = Join-Path $RepoDir "skills"
$Skills = @(
    "vlp-orchestrator",
    "vlp-video-download",
    "vlp-speech-transcribe",
    "vlp-translation-polish"
)

function Test-Command {
    param([string]$Name)

    if (Get-Command $Name -ErrorAction SilentlyContinue) {
        Write-Host "  [OK] $Name"
        return $true
    }

    Write-Host "  [missing] $Name"
    return $false
}

function Copy-Skill {
    param([string]$Skill)

    $src = Join-Path $SkillsSrc $Skill
    $dst = Join-Path $Target $Skill

    if (Test-Path $dst) {
        Remove-Item $dst -Recurse -Force
    }

    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    Copy-Item -Path (Join-Path $src "*") -Destination $dst -Recurse -Force

    Get-ChildItem $dst -Recurse -Force -Filter "DEVELOPMENT_NOTES.md" | Remove-Item -Force
    Get-ChildItem $dst -Recurse -Force -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem $dst -Recurse -Force -Filter "*.pyc" | Remove-Item -Force
}

function Invoke-Python {
    param([string[]]$Args)

    $allArgs = @($pythonPrefix) + $Args
    & $pythonCmd @allArgs
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Write-Host "==> Checking required commands"
$missingRequired = $false
$pythonCmd = $null
$pythonPrefix = @()

if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "  [OK] python"
    $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    Write-Host "  [OK] py -3"
    $pythonCmd = "py"
    $pythonPrefix = @("-3")
} else {
    Write-Host "  [missing] python"
    $missingRequired = $true
}

if (-not (Test-Command "yt-dlp")) { $missingRequired = $true }
if (-not (Test-Command "ffmpeg")) { $missingRequired = $true }
if (-not (Test-Command "ffprobe")) { $missingRequired = $true }

Write-Host ""
Write-Host "==> Checking optional ASR engines"
if (-not $pythonCmd) {
    Write-Host "  [skip] Python ASR check requires python"
} else {
    $allArgs = @($pythonPrefix) + @("-c", "import mlx_whisper")
    & $pythonCmd @allArgs *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] mlx-whisper"
    } else {
        $allArgs = @($pythonPrefix) + @("-c", "import faster_whisper")
        & $pythonCmd @allArgs *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] faster-whisper"
        } else {
            Write-Host "  [missing] mlx-whisper or faster-whisper"
            Write-Host "            install one before using vlp-speech-transcribe"
        }
    }
}

if ($missingRequired) {
    Write-Host ""
    Write-Host "Install missing tools, for example:"
    Write-Host "  winget install Python.Python.3.12"
    Write-Host "  winget install Gyan.FFmpeg"
    Write-Host "  python -m pip install yt-dlp"
}

if ($CheckOnly) {
    Write-Host ""
    Write-Host "==> Check only; no files copied."
    if ($missingRequired) { exit 1 }
    exit 0
}

Write-Host ""
Write-Host "==> Installing skills to: $Target"
New-Item -ItemType Directory -Force -Path $Target | Out-Null

foreach ($skill in $Skills) {
    Write-Host "  copying $skill"
    Copy-Skill $skill
}

Write-Host ""
Write-Host "==> Running helper self-checks"
if (-not $pythonCmd) {
    Write-Host "  skipped: python is missing"
} else {
    Invoke-Python @((Join-Path $Target "vlp-video-download\scripts\media_ingest.py"), "--self-check")
    Invoke-Python @((Join-Path $Target "vlp-speech-transcribe\scripts\transcribe_srt.py"), "--self-check")
    Invoke-Python @((Join-Path $Target "vlp-translation-polish\scripts\validate_markdown_translation.py"), "--self-check")
    Invoke-Python @((Join-Path $Target "vlp-translation-polish\scripts\bilingual_ass.py"), "--self-check")
}

Write-Host ""
Write-Host "Installed Video Language Pipeline skills."
Write-Host "Restart Codex if it was already running."

if ($missingRequired) {
    Write-Host "Some required commands are still missing; install them before running media workflows."
    exit 1
}
