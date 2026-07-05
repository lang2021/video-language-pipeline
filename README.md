# Video Language Pipeline

`Video Language Pipeline` is an agent-first multi-skill suite for video language workflows.

It is not CLI-first, not a single root skill, not a simple video downloader, not a simple subtitle translator, and not a complete automated video translation product. The primary interface is the set of `SKILL.md` files that Codex / agents read and follow.

The suite uses selective tooling. Deterministic media operations should be tool-heavy: video download, file registration, metadata extraction, audio extraction, and speech transcription are suitable for scripts because they depend on external tools, file paths, timestamps, and reproducible execution. Language judgment tasks stay agent-first: translation, polishing, terminology explanation, bilingual phrasing, and faithful style preservation should primarily rely on the agent's language ability and the rules written in `SKILL.md`.

Scripts may be added when they reduce repetitive mechanical work, but scripts should not replace the agent's semantic judgment unless explicitly required later.

## Current Phase

Current phase: Phase 1 - video download foundation plus minimal local speech transcription.

Phase 1 includes:

- multi-skill structure
- documentation migration
- orchestrator positioning
- download skill positioning
- minimal speech transcribe implementation
- translation polish skill positioning
- site-specific downloader adapter boundaries
- manifest contract
- media ingest / speech transcribe / translation polish contracts

Phase 1 does not include:

- translation implementation
- translation polish implementation
- bilingual subtitle rendering
- ASS/SRT generation
- subtitle burn-in
- full video translation pipeline

## Skill Overview

| Skill | Status | Can be used standalone? | Responsibility |
|---|---|---:|---|
| `vlp-orchestrator` | Agent-reasoning-first | Yes, as full pipeline entry | Intent routing, run planning, skill orchestration |
| `vlp-video-download` | Script-heavy / Phase 1 active | Yes | Video URL download, local media ingest, site adapters, metadata, manifest |
| `vlp-speech-transcribe` | Tool-heavy / minimal active | Yes | Audio extraction, ASR transcription, transcript assets |
| `vlp-translation-polish` | Agent-first, tool-light | Yes | Translation and polish for text assets, terminology consistency, format preservation |

Callable skills live under:

- `skills/vlp-orchestrator/SKILL.md`
- `skills/vlp-video-download/SKILL.md`
- `skills/vlp-speech-transcribe/SKILL.md`
- `skills/vlp-translation-polish/SKILL.md`

There is intentionally no root `SKILL.md`.

## Usage Routing

Use `vlp-orchestrator` for complete or ambiguous workflows.

Use `vlp-video-download` for download-only tasks and local media ingest.

Use `vlp-speech-transcribe` for local video/audio transcription.

Use `vlp-translation-polish` for existing text, transcript, subtitle text, pasted text, or Markdown translation/polish. This skill is agent-guided; it does not require an automated translation CLI.

## Reference Direction

The reference project `github/xiaohu-video-translate/` has a useful three-part split:

- orchestration
- video download / media ingest
- speech transcribe
- translation polish

This suite learns from that separation, including the reference downloader's site-specific script boundary, but does not copy reference code. It makes child skill independence and structured handoff contracts explicit from the start.

## Phase 1 Design Principles

- Agent-first: `SKILL.md` files are the primary runtime interface.
- Use selective tooling: media ingest and transcription can be tool-heavy; translation and polish stay agent-first.
- 下载是 media ingest，不是翻译流程的一部分。
- URL 下载和本地文件输入必须分开处理。
- 网站差异必须进入 site adapter，不要堆进一个通用下载脚本。
- 每次运行都必须生成可追踪记录，即使失败也写 manifest / log。
- `output_dir`, cookies, proxy, quality, chunk size must be configuration or job options.
- Deterministic media operations may be scripted; language judgment should remain agent-guided unless a specific executable helper is requested later.
- Do not put download, transcription, translation polish, alignment, and rendering into one uncontrolled step.
- Phase 1 prioritizes stable downloader architecture and diagnosability over broad platform coverage.

## Suite Specs

- `specs/suite-contract.md`
- `specs/media-ingest-contract.md`
- `specs/speech-transcribe-contract.md`
- `specs/translation-polish-contract.md`
- `specs/job-manifest.schema.md`

## Current Status

The suite scaffold exists. `vlp-video-download` has functional local ingest and site adapters for generic `yt-dlp`, YouTube, Bilibili, and Douyin. `vlp-speech-transcribe` has a minimal local audio/video -> SRT/TXT transcription script. `vlp-translation-polish` has agent-facing instructions and a bilingual SRT -> ASS text-asset utility; it is not an automated translation product. Subtitle rendering and burn-in logic have not been implemented.
