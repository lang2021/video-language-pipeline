# Reference Research: xiaohu-video-translate

Updated: 2026/07/05 15:11

## Research Scope

Reference project: `github/xiaohu-video-translate/`

Purpose: understand the workflow and design tradeoffs before creating `video-language-pipeline`. This research is for learning the shape of the pipeline, not copying implementation code.

## Actual Workflow

`xiaohu-video-translate` presents a one-stop video language workflow:

1. Accept a video URL or local video file.
2. Download video or audio when the input is a URL.
3. Extract audio with `ffmpeg`.
4. Transcribe with Whisper, preferring word-level timestamps.
5. Translate and polish subtitles through `xiaohu-subtitle-polish`.
6. Produce Chinese or bilingual subtitles.
7. Convert bilingual SRT to ASS for different Chinese / original-language font sizes.
8. Burn subtitles into video with `ffmpeg`.
9. Generate Markdown transcript / article output.

The most important product idea is the agent-facing "one sentence starts the whole pipeline" experience.

## Module Boundaries

The reference project uses three skills:

- `xiaohu-video-md`: orchestration, audio extraction, Whisper transcription, Markdown generation, subtitle burn-in flow.
- `xiaohu-subtitle-polish`: subtitle translation, correction, polish, line breaking, timestamp handling, bilingual subtitle rules.
- `xiaohu-video-download`: download-only or local-video subtitle workflows.

This split is useful because it separates "what workflow to run" from "how subtitles should read". The weakness is that subtitle translation, polish, segmentation, bilingual layout, and alignment still collapse into broad agent instructions inside the subtitle stage.

## Multi-Skill Suite Lesson

The useful reference-project lesson is the staged separation:

- orchestration
- video download / media ingest
- speech transcribe
- translation polish

`Video Language Pipeline` adopts that separation as an explicit agent-first multi-skill suite:

- `vlp-orchestrator`
- `vlp-video-download`
- `vlp-speech-transcribe`
- `vlp-translation-polish`

The new suite does not copy reference code. It makes independence and structured contracts more explicit: child skills must be independently usable, and cross-skill handoff should use manifests rather than hidden prompt state.

The suite is not CLI-first. `SKILL.md` files are the primary interface for Codex / agents. Scripts should support deterministic operations where they reduce friction; they should not replace agent judgment for translation, polish, terminology, or style decisions unless a specific executable helper is requested later.

The migration also avoids mixing download, transcription, translation/polish, alignment, and rendering into one uncontrolled step.

## Reusable Ideas

- Explicit `output_dir` is required before writing files.
- Use `tmp/` for intermediate files and `data/` for final outputs.
- Prefer wrapper scripts around fragile commands such as `yt-dlp`, especially to retry with `--cookies-from-browser`.
- Use Whisper word-level timestamps for subtitle workflows.
- Treat YouTube auto subtitles as useful for text-only drafts but risky for burned subtitle timing.
- Use ASS for bilingual subtitles; SRT plus `force_style` cannot express Chinese large / original small inside the same cue.
- Re-encode audio to AAC for wider social platform compatibility.
- Verify burned subtitles with frame extraction when layout or hard subtitle overlap matters.

## Main Risks

- Pipeline constraints are mostly prose instructions, not machine-checked contracts.
- The LLM can freely reshape output because translation, polish, sentence splitting, bilingual formatting, and timestamp handling are bundled together.
- There is no stable segmentation artifact that all later stages must preserve.
- Glossary and translation memory are not first-class inputs.
- Bilingual output depends on the model preserving line pairing and cue counts.
- Long-video translation can drift unless batching and validation are explicit.
- Markdown generation and subtitle generation have different needs but can be driven by the same loose transcript text.

## Implications For video-language-pipeline

The new skill suite should keep the reference project's agent-facing workflow ambition, but avoid over-automating language judgment:

- Stage boundaries must be explicit and documented in the skill.
- Deterministic media stages can use scripts and structured outputs.
- Translation should preserve segment identity and timing when those exist, but can remain agent-guided.
- Polish should improve language without changing meaning or timing unless the user explicitly asks.
- Subtitle layout should format already-approved text; it should not translate.
- Timeline validation should be a separate gate before subtitle export or burn-in.
- Burn-in should be optional and late in the workflow, after text and timing pass validation.

Implementation details such as concrete artifact schemas, model calls, and helper scripts are intentionally deferred until a concrete need appears. Do not build parser layers, automatic glossary extraction, automated translation CLIs, or quality report engines just to make language work look automated.

## Prior Download Lessons

Source brief: `/Users/marsdrifter/Documents/Codex/2026-06-16/concept-art-creature-design-codex/docs/prior-download-experience-brief.md`

### Verified / observed lessons

- `yt-dlp` was the main downloader used for YouTube videos and playlists.
- Format probing mattered when quality or codec mattered; visible "1080p" could mean different codec, FPS, or file size tradeoffs.
- High-quality YouTube media often required selecting separate video and audio streams, then merging to MP4.
- Browser cookies sometimes mattered; in an observed YouTube path, explicit `--cookies-from-browser "chrome:Default"` worked better than an unspecified Chrome cookie read.
- `ffprobe` was useful after download to confirm codec, resolution, audio stream, and MP4 compatibility.
- Output root confusion was a real issue; writing to `Downloads` instead of the project root was fixed by explicit `output_dir` and verifying `tmp/` / `data/`.
- Download failures and later subtitle/translation failures are different classes of problems; media ingest should stop after producing verified media artifacts and a manifest.

### Documented behavior from reference materials

- The reference download skill documents retries with browser cookies for YouTube 403 / SABR / PO Token style failures.
- The reference download skill keeps YouTube and Douyin logic in separate scripts rather than one shared command blob, and documents Bilibili via playlist/collection/multi-part `yt-dlp` behavior.
- Proxy support is documented as a download option, but not every prior run required it.
- Douyin support is documented as requiring browser login state, visible Chrome, persistent browser profile, and `aweme detail` capture before direct media download.
- Local file input is supported by the reference workflow and is important as a fallback when URL download is blocked.

### Design constraints for Phase 1

- Keep media ingest separate from transcription, translation, subtitle validation, and burn-in.
- Support URL input and local file input from the first implementation.
- Route URL download through site adapters; generic `yt-dlp` should be the fallback, not the place where every platform branch accumulates.
- Treat the reference downloader's explicit platform set as YouTube, Bilibili, Douyin, and generic `yt-dlp`.
- Treat cookies, proxy, output root, quality preference, and chunk size as config or job parameters.
- Always write `job_manifest.json` and `run.log`, including failed downloads.
- Log selected formats and final probed streams, not just requested resolution.
- Prefer boring checks over assumptions: use format probe when quality/codec matters and `ffprobe` after output.
- Keep platform adapters isolated; YouTube, Douyin, Reddit, browser-extension capture, and local file ingest should not become one tangled command path.

### Phase 1 recommendations

Include:

- Local video file ingest.
- Single URL download through a site adapter, with generic `yt-dlp` fallback.
- YouTube/Bilibili playlist or collection download only when explicitly requested with playlist items.
- Douyin resource listing and video download through a dedicated login-state adapter.
- Output root resolution with known `tmp/` and `data/` directories.
- Configurable cookies source, proxy, quality preference, and chunk size.
- H.264 MP4 preference when video output is requested.
- Final media verification with `ffprobe`.
- Job manifest and error log for every run.

Defer:

- Reddit / `v.redd.it` hosted video merging.
- Browser-extension download architecture.
- Douyin audio/both modes.
- Audio-only download.
- Transcription.
- Translation.
- Subtitle polishing.
- Subtitle burn-in.
- Windows/Linux font automation.
- Multi-agent translation control.

Open / not-yet-decided:

- Whether manifest should be JSON only or JSON plus a human-readable Markdown summary.
- Whether cookies/proxy config should be global only, per job only, or both.
- Whether local-file ingest should copy files into `data/` or register files in place.
