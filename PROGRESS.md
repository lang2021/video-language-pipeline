# PROGRESS.md

Last updated: 2026/07/05 15:54

## Current Stage

Phase 0/1 architecture alignment: agent-first four-skill suite scaffold with selective tooling. `vlp-video-download` is active, and `vlp-speech-transcribe` now has a minimal local audio/video transcription path.

## Active Version / Mode

`Video Language Pipeline` four-skill suite scaffold.

## Recently Completed

- Read the existing project record rule file `AGENTS.md`.
- Studied `github/xiaohu-video-translate/` as the reference project.
- Initialized project-facing docs without modifying `AGENTS.md`.
- Integrated prior download lessons from `prior-download-experience-brief.md`.
- Narrowed Phase 1 to stable media ingest: URL/local input detection, downloader command interface, output directories, metadata, `job_manifest.json`, and `run.log`.
- Migrated the project from root `SKILL.md` to a multi-skill suite structure.
- Removed root `SKILL.md`.
- Scaffolded `vlp-orchestrator`, `vlp-video-download`, `vlp-speech-transcribe`, and `vlp-translation-polish`.
- Added suite, media ingest, speech transcribe, translation polish, and job manifest specs.
- Implemented `skills/vlp-video-download/scripts/media_ingest.py`.
- `vlp-video-download` now supports URL download through `yt-dlp` and local file registration.
- Each run creates a dedicated output directory with `manifest.json` and `run.log`.
- Optimized `vlp-video-download` against the download-only parts of `xiaohu-video-download`.
- URL downloads now use H.264-first MP4 preference, retry settings, clean filenames, and cookies fallback while staying download-only.
- Converted child skill instructions to Chinese-first mixed language while preserving English technical terms.
- Split `vlp-video-download` Python implementation by responsibility: CLI entry, common helpers, run record, local ingest, and URL download.
- Added site adapter boundaries for URL downloads: generic `yt-dlp` adapter, YouTube adapter, and a direct `youtube_download.py` entry.
- Removed current-state wording that framed the downloader as a single small loop; current design target is a stable download foundation with explicit adapter boundaries.
- Migrated the reference downloader's explicit platform set: YouTube, Bilibili, Douyin, and generic `yt-dlp`.
- Added YouTube/Bilibili explicit playlist-item support and Douyin login/list/video-download adapter design.
- Renamed the subtitle-focused polish scaffold to `vlp-translation-polish`.
- Added `vlp-speech-transcribe` scaffold between media ingest and translation polish.
- Copied `xiaohu-subtitle-polish` content into `vlp-translation-polish`, then rewrote the skill design around text assets instead of subtitle-only workflow.
- Added `vlp-translation-polish/gemini-extension.json`.
- Added and hardened `vlp-translation-polish/scripts/bilingual_ass.py` for bilingual SRT -> ASS text-asset conversion.
- Updated `translation-polish-contract.md` and README status to reflect the design-active state.
- Added optional `ffprobe` media probing to `vlp-video-download` success paths.
- Cleaned all production `skills/*/SKILL.md` files to remove development-state, reference-source, and migration-history content.
- Added `DEVELOPMENT_NOTES.md` under each skill directory for implementation status, reference learnings, exclusions, migration rationale, and next steps.
- Optimized `vlp-translation-polish` production instructions around input detection, mode selection, default translation policy, terminology/glossary, chunking, task context state, format preservation, output rendering, manifest, and optional debug diagnostics.
- Updated `translation-polish-contract.md` with the same runtime structure.
- Added `vlp-video-download --mode video|audio|subtitles|metadata`.
- Added audio-only URL download through `yt-dlp -x --audio-format mp3`.
- Added raw subtitle-only download through `yt-dlp --skip-download --write-subs --write-auto-subs`.
- Added best-effort raw subtitle download after successful YouTube/Bilibili/generic video downloads.
- Added Douyin audio mode when `aweme detail` exposes `audio_url`; Douyin subtitles mode now fails clearly as unsupported.
- Re-aligned project documentation around agent-first, not CLI-first, boundaries.
- Reframed `vlp-translation-polish` as agent-guided language work with optional helper scripts, not a mandatory executable translation product.
- Clarified selective tooling: `vlp-video-download` is script-heavy, `vlp-speech-transcribe` is future tool-heavy, and `vlp-translation-polish` is agent-first / tool-light.
- Added `vlp-translation-polish/scripts/validate_markdown_translation.py` to catch Markdown URL and structure drift after agent translation.
- Added `vlp-speech-transcribe/scripts/transcribe_srt.py` for local audio/video or media-ingest-manifest to SRT/TXT transcription.
- `vlp-speech-transcribe` now writes per-run `manifest.json` and `run.log`, extracts video audio with `ffmpeg`, and uses `mlx-whisper` with `faster-whisper` fallback.

## Current Limitations

- URL download depends on installed `yt-dlp`; the script does not install it.
- URL/local dispatch exists only in `vlp-video-download`.
- Site adapter dispatch currently covers YouTube, Bilibili, Douyin, and generic `yt-dlp`.
- Successful local ingest/download now records `outputs.media_probe` when `ffprobe` succeeds, or a non-fatal `ffprobe_*` warning when it does not.
- YouTube video download with automatic raw subtitle attempt has passed one real URL smoke test.
- Douyin requires local Chrome login state prepared by `douyin_login.py`.
- Subtitle mode saves only raw platform subtitle files; no cleaning, translation, bilingual layout, render, or burn-in exists here.
- No installer or global skill registration.
- `vlp-speech-transcribe` has a minimal local transcription script, but no real media smoke test has been run.
- `vlp-translation-polish` has agent-facing rules and a bilingual SRT -> ASS utility, but no automated translation CLI or model invocation exists by design.
- Markdown translation validation covers inline links/images, raw autolinks, front matter keys, heading levels, and fenced code block count; reference-style links are deferred until needed.
- No subtitle rendering, cleaned ASS/SRT generation, or burn-in has been implemented.

## Next Recommended Step

Continue hardening the Phase 1 download/media ingest track:

- run real URL smoke tests for Bilibili and Douyin when the user provides URLs
- run real URL smoke tests for YouTube audio-only and subtitles-only when the user provides URLs
- run a real local audio/video smoke test for `vlp-speech-transcribe` when a sample file is available
- decide whether to copy local files or continue registering them in place
- add a small fixture-based test script if the tool grows beyond the current self-check

Keep Phase 1 focused on media ingest. For `vlp-translation-polish`, only add executable helpers when a concrete user task proves they are worth the maintenance cost.

## Handoff Notes

- There is intentionally no root `SKILL.md`; do not recreate one.
- Callable skills live under `skills/<skill-name>/SKILL.md`.
- Current callable skills are `vlp-orchestrator`, `vlp-video-download`, `vlp-speech-transcribe`, and `vlp-translation-polish`.
- Treat `skills/*/SKILL.md` as production prompt files only.
- Treat this suite as agent-first, not CLI-first.
- Use selective tooling: deterministic media/transcription operations can be tool-heavy; translation and polish remain agent-first / tool-light.
- Put skill-specific development status, reference notes, and migration rationale in `skills/*/DEVELOPMENT_NOTES.md`.
- `vlp-translation-polish` may generate ASS only as a text-asset conversion utility; actual render / burn-in remains future-layer work.
- Do not copy code from `github/xiaohu-video-translate/`.
- Do not install or publish the skill globally without confirmation.
- Treat cookies, proxy, quality, and chunk size as configuration, not hardcoded constants.
- Always keep enough manifest/log evidence to diagnose failed downloads.
- Keep documents Chinese-first mixed language; keep file names, commands, APIs, and skill names in English.
