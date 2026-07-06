# Video Language Pipeline

Language: English | [简体中文](README.zh-CN.md)

Video Language Pipeline is an agent-first multi-skill suite for video language workflows.

It is not a single CLI product. The primary interface is the set of `SKILL.md` files that Codex or another agent reads and follows. Scripts are included only where deterministic tooling is useful, such as media ingest, transcription, and subtitle-format helpers.

## What It Does

- Download or register video/audio assets.
- Generate local SRT/TXT transcripts from media.
- Translate and polish text assets, transcripts, SRT/VTT subtitles, Markdown, and pasted text.
- Produce translated or bilingual subtitle text assets.
- Preserve handoff evidence through manifests, logs, and explicit file paths.

The suite stops at text assets. It does not render or burn subtitles into video.

## Skills

| Skill | Role |
|---|---|
| `vlp-orchestrator` | Routes complete workflows and coordinates handoff between skills. |
| `vlp-video-download` | Downloads URLs, registers local media, writes manifests and logs. |
| `vlp-speech-transcribe` | Converts local audio/video into SRT/TXT transcript assets. |
| `vlp-translation-polish` | Performs agent-guided translation, subtitle polish, terminology consistency, and format preservation. |

Callable skills live under:

```text
skills/<skill-name>/SKILL.md
```

There is intentionally no root `SKILL.md`.

## Default Workflow

For a complete video-to-bilingual-subtitles task, start with `vlp-orchestrator`:

```text
vlp-video-download
  -> vlp-speech-transcribe
  -> vlp-translation-polish
  -> translated or bilingual SRT/VTT
```

Bilingual subtitle requests such as “download bilingual subtitles” or “generate bilingual SRT” are treated as full pipeline requests, not raw platform-subtitle downloads.

If a video has no platform subtitles and ASR output contains no useful speech content, the orchestrator should stop safely instead of fabricating subtitles.

## Install

Install directly into the local Codex agent skills directory.

macOS:

```bash
bash install.sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Check dependencies without copying files.

macOS:

```bash
bash install.sh --check-only
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -CheckOnly
```

Use a custom skills directory.

macOS:

```bash
bash install.sh --target "$HOME/.codex/skills"
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target "$HOME\.codex\skills"
```

The installers copy only the four production skill folders, run helper self-checks, and report missing external commands. They do not install system tools automatically.

## Command Helpers

Run commands from the relevant skill directory.

Media ingest:

```bash
python3 scripts/media_ingest.py "<video-url-or-local-file>"
python3 scripts/media_ingest.py "<video-url>" --mode audio
python3 scripts/media_ingest.py "<video-url>" --mode subtitles --sub-langs "en,zh-Hans"
python3 scripts/media_ingest.py --self-check
```

Speech transcription:

```bash
python3 scripts/transcribe_srt.py "<local-audio-or-video>"
python3 scripts/transcribe_srt.py "<media-ingest-manifest.json>"
python3 scripts/transcribe_srt.py --self-check
```

Translation helpers:

```bash
python3 scripts/validate_markdown_translation.py <source.md> <translated.md>
python3 scripts/bilingual_ass.py <bilingual.srt>
```

## Requirements

- Python 3.
- `yt-dlp` for URL downloads.
- `ffmpeg` and `ffprobe` for media probing and audio extraction.
- `mlx-whisper` or `faster-whisper` for local ASR transcription.

The scripts do not install external tools automatically.

## Boundaries

- `vlp-video-download` does not transcribe, translate, polish, render, or burn subtitles.
- `vlp-speech-transcribe` does not download remote URLs or translate text.
- `vlp-translation-polish` is agent-guided and does not provide a full automated translation runner.
- `vlp-orchestrator` coordinates child skills but does not duplicate their internal logic.

Generated runs, logs, local agent records, and development notes are intentionally kept out of the public release.
