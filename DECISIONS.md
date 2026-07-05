# DECISIONS.md

## 2026/07/05 11:01

- decision: `video-language-pipeline` will learn from `xiaohu-video-translate` but will not copy its code.
- reason or context: The reference project proves the value of an end-to-end agent pipeline, but its subtitle instability comes from weak stage boundaries and prompt-only constraints.
- expected impact: Future implementation should prioritize stable segmentation, glossary / translation memory, structured intermediate artifacts, and validation gates before adding broad automation.
- status: active
- supersedes: none
- outcome: Project initialized as a staged, reproducible video language processing skill.

## 2026/07/05 11:23

- decision: Phase 1 will implement planning for orchestrator + download / media ingest first, and defer subtitle polish, transcription, translation, ASS/SRT generation, and burn-in.
- reason or context: Prior download experience showed that download failures, output-root mistakes, cookie/profile issues, format selection, and final media verification are already enough scope for a stable first phase. Subtitle polish is the least stable later stage and should not be mixed into media ingest.
- expected impact: The first implementation task should produce URL/local ingest, configurable download options, metadata, `job_manifest.json`, and `run.log` before any language-processing work begins.
- status: active
- supersedes: none
- outcome: Historical download lessons are now treated as Phase 1 design constraints.

## 2026/07/05 12:59

- decision: Use multi-skill suite architecture.
- reason or context: `Video Language Pipeline` is not one callable skill. It needs separate skills for orchestration, media ingest, and future subtitle polish so each part can be used and tested independently.
- expected impact: There is no root `SKILL.md`. Callable skills live at `skills/<skill-name>/SKILL.md`. The initial suite had orchestration, media ingest, and a subtitle-focused polish scaffold. Child skills must remain independently usable. `vlp-orchestrator` is orchestration-only. Phase 1 focuses on orchestrator + video-download foundation.
- status: active
- supersedes: none
- risk: Some agents may expect a root `SKILL.md`.
- mitigation: `AGENTS.md` and `README.md` explicitly state that there is intentionally no root `SKILL.md` and point to `skills/*/SKILL.md`.
- outcome: Root `SKILL.md` migrated into suite docs and child skill scaffolds, then removed.

## 2026/07/05 13:47

- decision: `vlp-video-download` will use site-specific downloader adapters instead of treating all URL downloads as one generic command path.
- reason or context: The reference `xiaohu-video-download` has separate scripts for YouTube and Douyin. The earlier `vlp-video-download` design absorbed retry/cookies/H.264 behavior but missed the site boundary, which would make future platform fixes harder.
- expected impact: URL ingest routes through `site_downloaders/`. Current adapters are `generic` and `youtube`; future Douyin, Bilibili, X/Twitter, Reddit, or other platform support should be added as separate adapters.
- status: active
- supersedes: The earlier current-state framing that treated `vlp-video-download` as a minimal single download loop.
- outcome: Added adapter dispatch, a YouTube adapter, a generic adapter, and a `youtube_download.py` entry while keeping transcription, translation, subtitles, and burn-in out of the download skill.

## 2026/07/05 13:56

- decision: Migrate the reference downloader's explicit platform set into `vlp-video-download`: YouTube, Bilibili, Douyin, and generic `yt-dlp`.
- reason or context: The reference `xiaohu-video-download` documents YouTube-specific fallback, Bilibili playlist/collection/multi-part behavior through `yt-dlp`, and Douyin login-state browser capture. Treating only Douyin as special would miss the broader site-boundary design.
- expected impact: `vlp-video-download` now routes YouTube, Bilibili, Douyin, and generic URLs through separate adapters. YouTube/Bilibili playlist behavior is explicit via `--playlist-items`; Douyin uses login-state browser capture and does not share the generic command path.
- status: active
- supersedes: none
- outcome: Added Bilibili and Douyin adapters, direct entry scripts, playlist/list/resolution CLI options, and local ignore rules for sensitive Douyin browser state.

## 2026/07/05 14:08

- decision: Use a four-skill suite architecture: `vlp-orchestrator`, `vlp-video-download`, `vlp-speech-transcribe`, and `vlp-translation-polish`.
- reason or context: The pipeline needs an explicit speech-to-text layer between media ingest and language work. The old subtitle-only naming was too narrow because the language layer will handle transcripts, Markdown, ordinary documents, and subtitle text.
- expected impact: Root `SKILL.md` remains absent. The subtitle-focused polish scaffold is renamed to `vlp-translation-polish`; `vlp-speech-transcribe` is added as a scaffold. Phase 1 still prioritizes `vlp-video-download`; transcription and translation/polish remain future phases.
- status: active
- supersedes: The 2026/07/05 12:59 initial three-skill suite shape.
- outcome: Suite architecture now reserves separate download, speech transcribe, and translation polish layers without implementing Phase 2/3 behavior.

## 2026/07/05 15:11

- decision: Keep Video Language Pipeline agent-first, not CLI-first.
- reason or context: The project is a skill suite for Codex / agent usage. Over-specifying every language task as an automated CLI runner creates unnecessary complexity and may reduce agent flexibility.
- expected impact: `SKILL.md` files are primary. The suite uses selective tooling: deterministic media operations may be script-heavy, `vlp-speech-transcribe` may become tool-heavy when implemented, and translation/polish remains agent-first and tool-light unless a specific helper is requested later. Do not over-engineer input detection, mode selection, parser layers, or debug reports at the current stage.
- status: active
- supersedes: none
- outcome: Documentation will frame scripts as helpers and keep `vlp-translation-polish` as an agent-guided language skill.
