# Translation Polish Contract

Updated: 2026/07/05 15:36

## Skill

`vlp-translation-polish`

## Role

Agent-guided language conversion and polish for text-shaped assets.

Handles:

- Markdown
- plain text
- transcript
- SRT / VTT subtitles
- subtitle snippets
- pasted text

Does not handle video download, audio extraction, Whisper / ASR, video encoding, or subtitle burn-in.

## Agent-First Boundary

`SKILL.md` is primary. The agent may inspect input shape and user intent directly, then apply the skill rules.

Do not require a full automated translation CLI, parser layer, automatic glossary extractor, or quality review tool for this skill at the current stage. Those may be added later only when a concrete need is requested.

Scripts are optional helpers. `scripts/bilingual_ass.py` remains valid because bilingual SRT -> ASS is deterministic text-asset conversion. `scripts/validate_markdown_translation.py` remains valid because Markdown URL and structure validation is deterministic mechanical work.

## Expected Agent Behavior

- Identify whether the input is document, transcript, subtitle, snippet, or pasted text.
- Translate faithfully and completely.
- Preserve structure and formatting.
- Keep terminology consistent within the task.
- Preserve key English terms when appropriate.
- Add Chinese parenthetical explanations for key English terms when useful.
- Avoid unrequested summary, compression, or literary rewriting.
- Treat task context as local to the current request, not long-term memory.

## Format Preservation

- Markdown: preserve headings, lists, links, images, code blocks, tables, and front matter.
- SRT: preserve index, timestamp, and cue structure.
- VTT: preserve `WEBVTT` header, cue blocks, and timestamps.
- Plain text: preserve paragraphs, blank lines, and order.

For Markdown file translation, link/image URLs and raw autolinks must be preserved exactly. After translation, run:

```bash
python3 scripts/validate_markdown_translation.py <source.md> <translated.md>
```

Validation failure means the output is not acceptable until the URL or structure mismatch is fixed.

## Outputs

Possible outputs:

- translated Markdown
- bilingual Markdown
- translated text
- translated SRT / VTT
- bilingual SRT / VTT
- task-local glossary notes
- optional bilingual ASS asset from an existing bilingual SRT

ASS generation is allowed only as helper text-asset conversion. Actual render / burn-in belongs to a future layer.

## Manifest

Manifest is useful for agent / pipeline handoff, but it is not mandatory for small pasted-text tasks.

When used, it should record:

- input type
- input path or input summary
- target language
- output paths
- status
- errors
- warnings

## Debug Diagnostics

Debug diagnostics are optional and should not be default user-facing output.

Examples:

- `run.log`
- `polish_report.md`
- `quality_report.md`

Normal agent use should avoid producing reports unless the user asks, the task is a test/review task, or a failure needs diagnosis.
