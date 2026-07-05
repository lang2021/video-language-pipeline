# Speech Transcribe Contract

Updated: 2026/07/05 15:35

## Skill

`vlp-speech-transcribe`

## Tooling Position

`vlp-speech-transcribe` is a tool-heavy skill when implemented. Audio extraction and ASR transcription are suitable for scripts because they depend on external tools, file paths, timestamps, and reproducible execution.

## Status

Minimal local transcription path implemented.

## Inputs

- local video path
- local audio path
- optional media ingest manifest
- optional language hint
- optional transcription mode or quality preference
- optional output root
- optional output basename

## Outputs

- transcript text
- timestamped transcript
- SRT subtitle-like text asset
- transcription metadata
- run manifest / log

## Boundaries

`vlp-speech-transcribe` should not download video, handle remote URLs, translate, polish, render subtitles, or burn subtitles.

It should be callable directly with existing local media and should not depend on `vlp-orchestrator`.

## Script Interface

```bash
python3 scripts/transcribe_srt.py "<local-audio-or-video>"
python3 scripts/transcribe_srt.py "<local-media>" --engine auto --language en
python3 scripts/transcribe_srt.py "<media-ingest-manifest.json>"
python3 scripts/transcribe_srt.py --self-check
```

Missing `ffmpeg`, `mlx-whisper`, or `faster-whisper` must produce a failed manifest/log instead of auto-installing dependencies.
