#!/usr/bin/env bash
#
# Install Video Language Pipeline skills for local Codex use.
#
# Usage:
#   bash install.sh
#   bash install.sh --target "$HOME/.codex/skills"
#   bash install.sh --check-only
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
TARGET_DIR="${HOME}/.codex/skills"
CHECK_ONLY=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      TARGET_DIR="${2:-}"
      if [ -z "$TARGET_DIR" ]; then
        echo "error: --target requires a directory" >&2
        exit 2
      fi
      shift 2
      ;;
    --check-only)
      CHECK_ONLY=1
      shift
      ;;
    -h|--help)
      sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

skills=(
  vlp-orchestrator
  vlp-video-download
  vlp-speech-transcribe
  vlp-translation-polish
)

check_bin() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "  [OK] $1"
  else
    echo "  [missing] $1"
    return 1
  fi
}

copy_skill() {
  local skill="$1"
  local src="$SKILLS_SRC/$skill"
  local dst="$TARGET_DIR/$skill"

  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --exclude 'DEVELOPMENT_NOTES.md' \
      --exclude '__pycache__/' \
      --exclude '*.pyc' \
      "$src/" "$dst/"
  else
    rm -rf "$dst"
    mkdir -p "$dst"
    (cd "$src" && tar --exclude='DEVELOPMENT_NOTES.md' --exclude='__pycache__' --exclude='*.pyc' -cf - .) | (cd "$dst" && tar -xf -)
  fi
}

echo "==> Checking required commands"
missing_required=0
has_python=1
check_bin python3 || { missing_required=1; has_python=0; }
check_bin yt-dlp || missing_required=1
check_bin ffmpeg || missing_required=1
check_bin ffprobe || missing_required=1

echo ""
echo "==> Checking optional ASR engines"
if [ "$has_python" -eq 0 ]; then
  echo "  [skip] Python ASR check requires python3"
elif python3 -c 'import mlx_whisper' >/dev/null 2>&1; then
  echo "  [OK] mlx-whisper"
elif python3 -c 'import faster_whisper' >/dev/null 2>&1; then
  echo "  [OK] faster-whisper"
else
  echo "  [missing] mlx-whisper or faster-whisper"
  echo "            install one before using vlp-speech-transcribe"
fi

if [ "$missing_required" -ne 0 ]; then
  echo ""
  case "$(uname -s)" in
    Darwin)
      echo "Install missing tools with Homebrew, for example:"
      echo "  brew install yt-dlp ffmpeg"
      ;;
    Linux)
      echo "Install missing tools, for example:"
      echo "  sudo apt install ffmpeg"
      echo "  python3 -m pip install yt-dlp"
      ;;
    *)
      echo "Install the missing commands for your platform, then rerun this script."
      ;;
  esac
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
  echo ""
  echo "==> Check only; no files copied."
  exit "$missing_required"
fi

echo ""
echo "==> Installing skills to: $TARGET_DIR"
mkdir -p "$TARGET_DIR"

for skill in "${skills[@]}"; do
  echo "  copying $skill"
  copy_skill "$skill"
done

echo ""
echo "==> Running helper self-checks"
if [ "$has_python" -eq 0 ]; then
  echo "  skipped: python3 is missing"
else
  python3 "$TARGET_DIR/vlp-video-download/scripts/media_ingest.py" --self-check
  python3 "$TARGET_DIR/vlp-speech-transcribe/scripts/transcribe_srt.py" --self-check
  python3 "$TARGET_DIR/vlp-translation-polish/scripts/validate_markdown_translation.py" --self-check
  python3 "$TARGET_DIR/vlp-translation-polish/scripts/bilingual_ass.py" --self-check
fi

echo ""
echo "Installed Video Language Pipeline skills."
echo "Restart Codex if it was already running."

if [ "$missing_required" -ne 0 ]; then
  echo "Some required commands are still missing; install them before running media workflows."
  exit 1
fi
