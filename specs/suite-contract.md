# Suite Contract

Updated: 2026/07/05 15:11

## Identity

`Video Language Pipeline` is an agent-first multi-skill suite, not a single root skill and not a CLI-first automation product.

There is intentionally no root `SKILL.md`. Callable skills live under `skills/<skill-name>/SKILL.md`.

`SKILL.md` files are the primary runtime interface for Codex / agents. The suite uses selective tooling: deterministic media operations may be script-heavy, while language judgment remains agent-first.

## Skills

| Skill | Role | Standalone |
|---|---|---:|
| `vlp-orchestrator` | Agent-reasoning-first intent routing, run planning, cross-skill orchestration | Yes |
| `vlp-video-download` | Script-heavy URL download, local media ingest, metadata, manifest/log | Yes |
| `vlp-speech-transcribe` | Tool-heavy future audio extraction and ASR transcription | Yes, later |
| `vlp-translation-polish` | Agent-first, tool-light translation and polish for text assets | Yes |

## Routing

- Complete or ambiguous workflow -> start with `vlp-orchestrator`.
- Download-only or media-ingest task -> use `vlp-video-download` directly or route to it.
- Local video/audio transcription -> use `vlp-speech-transcribe` once implemented.
- Existing text/transcript/subtitle/Markdown translation or polish -> use `vlp-translation-polish` directly; do not require an automated translation CLI.
- Unsupported or future-phase workflow -> return a clear status and missing capability list.

## Orchestrator Rules

- The orchestrator may select child skills and summarize outputs.
- The orchestrator must not implement child skill logic.
- The orchestrator must not copy download rules into itself.
- The orchestrator must not copy speech-transcribe rules into itself.
- The orchestrator must not copy translation-polish rules into itself.

## Child Skill Independence

- `vlp-video-download` must remain independently usable.
- `vlp-speech-transcribe` must remain independently usable.
- `vlp-translation-polish` must remain independently usable.
- Child skills must not depend on `vlp-orchestrator`.

## Pipeline Layers

```text
video / audio / subtitle / document input
        ↓
vlp-video-download
        ↓
vlp-speech-transcribe
        ↓
vlp-translation-polish
        ↓
future optional subtitle render / burn-in
```

## Handoff

All cross-skill handoff should use structured manifests. A skill may read a prior manifest, add its own outputs, and produce a new manifest or report.

Manifest handoff is important for multi-stage pipeline work. It is not required for small one-off pasted-text translation tasks.

## Script Boundary

- Deterministic media operations such as download, local ingest, metadata probing, audio extraction, speech transcription, and format conversion may be scripted.
- `vlp-video-download` is the current script-heavy layer.
- `vlp-speech-transcribe` may become tool-heavy when an ASR path is explicitly implemented.
- Translation, polishing, terminology explanation, bilingual phrasing, and faithful style preservation remain agent-guided unless a specific executable helper is requested later.
