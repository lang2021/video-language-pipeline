# AGENTS.md V1.3

## Suite Architecture

This repository is an agent-first four-skill suite, not a CLI-first automation product.

`SKILL.md` is primary. It tells Codex / agents when to use a skill, what principles to follow, and where not to cross boundaries.

Use selective tooling. Deterministic media operations should be tool-heavy: video download, file registration, metadata extraction, audio extraction, and speech transcription are suitable for scripts because they depend on external tools, file paths, timestamps, and reproducible execution.

Language judgment tasks should be agent-first. Translation, polishing, terminology explanation, bilingual phrasing, and faithful style preservation should primarily rely on the agent's language ability and the rules written in `SKILL.md`. Scripts may reduce repetitive mechanical work, but they must not replace semantic judgment unless explicitly required later.

There is intentionally no root `SKILL.md`.

Callable skills live under:

- `skills/vlp-orchestrator/SKILL.md`
- `skills/vlp-video-download/SKILL.md`
- `skills/vlp-speech-transcribe/SKILL.md`
- `skills/vlp-translation-polish/SKILL.md`

Do not recreate a root `SKILL.md` unless explicitly instructed.

Rules:

- Do not collapse the four skills into one.
- Do not put download logic into `vlp-orchestrator`.
- Do not put transcription logic into `vlp-orchestrator`.
- Do not put translation or polish logic into `vlp-orchestrator`.
- Do not make `vlp-video-download` depend on `vlp-orchestrator`.
- Do not make `vlp-speech-transcribe` depend on `vlp-orchestrator`.
- Do not make `vlp-translation-polish` depend on `vlp-orchestrator`.
- Child skills must remain independently usable.
- Do not recreate language tasks as large automation frameworks by default.
- Keep `vlp-translation-polish` agent-guided unless a specific executable helper is requested later.
- Treat `vlp-orchestrator` as agent-reasoning-first.
- Treat `vlp-video-download` as script-heavy.
- Treat `vlp-speech-transcribe` as tool-heavy when implemented.
- Treat `vlp-translation-polish` as agent-first, tool-light.
- Phase 1 focuses on scaffold, orchestration planning, and media ingest foundation with explicit site adapter boundaries.

## Purpose

This document defines a general project record system for AI-assisted work.

The record system should preserve:

- current project state
- in-progress work notes
- completed task history
- major decisions
- handoff context for the next human or AI agent

Keep this document as a record rule file. Do not turn it into a project README.

## Core Model

```text
PROGRESS.md = 当前状态
WORK_NOTES.md = 开发过程笔记
ITERATION_LOG.md = 完成后的任务历史
DECISIONS.md = 重大决策
AGENTS.md = 记录规则
```

## Required Record Files

If the following files do not exist, create them when they are first needed:

```text
PROGRESS.md
WORK_NOTES.md
ITERATION_LOG.md
DECISIONS.md
```

`WORK_NOTES.md` is optional until there is meaningful in-progress work to preserve.

## Timestamp Rule

Use minute-level timestamps for all new record entries:

```text
YYYY/MM/DD HH:mm
```

Rules:

- Do not downgrade records to date-only timestamps.
- Do not omit hour and minute.
- Use the local timezone unless the repository explicitly specifies another timezone.
- For new record entries, use the current environment date/time directly. Do not scan existing logs just to determine the timestamp format.

## Document Read Order

Use the read order that matches the task.

### Ordinary Handoff / 日常接手

1. `AGENTS.md`
2. `PROGRESS.md`
3. `DECISIONS.md`
4. Recent `WORK_NOTES.md` entries only if the task appears mid-stream
5. Recent `ITERATION_LOG.md` entries only if needed

### Implementation Or Debugging / 实现或调试

1. `AGENTS.md`
2. `PROGRESS.md`
3. `DECISIONS.md`
4. Relevant source files and tests
5. Recent `WORK_NOTES.md` entries when continuing unfinished work
6. Recent `ITERATION_LOG.md` entries only when current context is unclear

### Retrospective Or Recovery / 复盘或项目恢复

1. `AGENTS.md`
2. `PROGRESS.md`
3. `DECISIONS.md`
4. Full `ITERATION_LOG.md`
5. Relevant `WORK_NOTES.md`
6. README / docs / source evidence as needed

### Public Release / 公开发布

1. `AGENTS.md`
2. `PROGRESS.md`
3. `DECISIONS.md`
4. README and public docs
5. `git ls-files`
6. Recent release-related `ITERATION_LOG.md` entries if needed

## PROGRESS.md

`PROGRESS.md` is the current project status board.

It should be updated after status-changing work, not appended as a historical timeline.

It should answer:

- last updated
- current stage
- active version / mode
- recently completed work
- current limitations
- next recommended step
- handoff notes

Do not use `PROGRESS.md` as a project introduction. Project introduction belongs in `README.md`.

## WORK_NOTES.md

`WORK_NOTES.md` is an append-only scratch history for in-progress work.

Use it for:

- live observations
- failed attempts
- temporary hypotheses
- partial verification
- debugging traces
- useful mid-task context that should not be lost

Entries should be short and timestamped. They do not need the full `ITERATION_LOG.md` template.

Use concise Chinese-first mixed language. Keep commands, selectors, file paths, APIs, error names, function names, and technical terms in English.

Do not mechanically duplicate every note in both Chinese and English. Use full bilingual wording only when a note is likely to be reused in public docs or formal handoff.

Do not rewrite or clean up old `WORK_NOTES.md` entries unless the user explicitly asks.

Suggested entry shape: timestamp, context, observation, tried, result, next.

## ITERATION_LOG.md

`ITERATION_LOG.md` is the canonical completed-task ledger.

Append one new entry after file changes, release/publication actions, major verification, or analysis that changes the project status or next direction. Pure discussion, rule explanation, and lightweight document review do not require record updates unless the user asks to save them.

At task completion, summarize only the final outcome, key rationale, verification, and remaining issues from `WORK_NOTES.md` into `ITERATION_LOG.md`.

Do not add mid-task progress entries to `ITERATION_LOG.md`; use `WORK_NOTES.md` or chat updates for temporary state.

Keep entries in chronological append order. If a late entry must describe earlier work, use the current timestamp and mention the earlier work in the task goal.

Use the standard entry template consistently. Do not switch between full-section and compact bullet formats.

Do not rewrite old entries unless explicitly requested.

Each entry should include:

- timestamp
- task type
- task goal
- changes made
- files changed
- verification status
- status after task
- rationale / 当时判断
- remaining issues
- next step
- major decision status

If no major decision was made, write:

```text
Major decision: none
```

If verification is pending, explain why. Do not write `pending` when a quick check can still be run.

### Task Types

Use one of:

```text
research
planning
implementation
content
correction
refactor
test
release
archive
retrospective
```

## DECISIONS.md

`DECISIONS.md` is the major decision index.

Append only when a major product, workflow, or technical decision is made.

Each decision entry should include:

- timestamp
- decision
- reason or context
- expected impact
- status: `active` / `superseded` / `archived`
- supersedes: optional
- outcome: optional

Major decisions include project direction, major features, technical approach, record system, data source strategy, safety boundary, dependencies/permissions, or archive/freeze decisions.

If no major decision was made, do not append to `DECISIONS.md`.
Instead, write `Major decision: none` in the `ITERATION_LOG.md` entry.

## Documentation Language

Use Chinese-first mixed language for project documents by default.

Keep technical identifiers, commands, API names, file paths, code terms, error names, and domain-specific terms in English when that is clearer or matches the code.

Write status, rationale, tradeoffs, handoff notes, and user-facing explanations primarily in Chinese, with English terms embedded as needed.

Avoid mechanically duplicating every sentence in both languages. Use full bilingual sections only for public-facing README/release docs or when the user asks.

## Public README Language

For public GitHub repositories, use English as the primary `README.md` language.

When Chinese documentation is useful, add `README.zh-CN.md` as a separate Simplified Chinese version.

Add language switch links at the top of each README:

```text
README.md:
Language: English | [简体中文](README.zh-CN.md)

README.zh-CN.md:
语言：[English](README.md) | 简体中文
```

Do not duplicate long English and Chinese sections inside one README unless the README is very short.

Keep code blocks, commands, file paths, API names, and config keys consistent across language versions.

## Engineering Rules

Before building a substantial custom solution, check whether this repo, the platform, or a reputable existing library already solves the problem.

Use an existing solution only when it clearly fits the project constraints and reduces total maintenance cost.

For small, project-specific fixes, prefer existing local code and simple platform APIs over adding dependencies or doing broad research.

When analyzing bugs, start from first principles before choosing a fix. Trace the real flow, identify the root cause, then apply the smallest fitting fix.

## Public Release Boundary

Before any public push, release, or GitHub snapshot, run `git ls-files` and confirm the tracked file set.

Keep agent records, progress logs, decision logs, internal specs, and test-operation guides local-only unless the user explicitly approves publishing them.

## General Rules

- Records should be concise and factual.
- Prefer reusable record structure over project-specific wording.
- Preserve why a decision was made, not only what changed.
