# ITERATION_LOG.md

## 2026/07/05 11:01

- task type: research
- task goal: Initialize `video-language-pipeline` with first-stage research and project direction based on `github/xiaohu-video-translate/`.
- changes made: Created project docs for the skill goal, reference research, v0 skill direction, current progress, and initial architecture decision.
- files changed: `README.md`, `RESEARCH.md`, `SKILL.md`, `PROGRESS.md`, `DECISIONS.md`, `ITERATION_LOG.md`
- verification status: `rg --files 'self/Video Language Pipeline'` confirmed target files; `git diff --check` could not run because this directory is not a git repository; fallback `git diff --no-index --check` passed for all new Markdown files; `WORK_NOTES.md` was not created.
- status after task: First-stage docs created; implementation not started.
- rationale / 当时判断: 一条龙体验值得保留，但字幕稳定性需要靠阶段边界、结构化中间产物、术语一致性和校验门控解决，而不是继续加 prompt 约束。
- remaining issues: Concrete artifact schemas, helper scripts, model invocation, batching, validation, and burn-in commands are not designed yet.
- next step: Define the minimal segment artifact contract and one small validation path.
- major decision status: See `DECISIONS.md` entry at 2026/07/05 11:01.

## 2026/07/05 11:23

- task type: planning
- task goal: Integrate prior download experience into the current Phase 1 project plan.
- changes made: Updated project docs to define Phase 1 as orchestrator + download / media ingest; added historical download lessons, design constraints, explicit deferred capabilities, and next TODOs.
- files changed: `README.md`, `RESEARCH.md`, `SKILL.md`, `PROGRESS.md`, `DECISIONS.md`, `ITERATION_LOG.md`
- verification status: `rg --files 'self/Video Language Pipeline'` confirmed target files; `AGENTS.md` kept its original timestamp and was not part of the patch; `git diff --no-index --check` passed for modified Markdown files; manual reread confirmed Phase 1 excludes transcription, translation, subtitle polish, ASS/SRT, and burn-in.
- status after task: Phase 1 planning is narrowed to media ingest; implementation not started.
- rationale / 当时判断: 下载阶段已有真实风险，包括 cookies/profile、format probe、ffprobe 验证、输出目录、失败日志和本地文件 fallback；这些应先变成设计约束，再进入字幕/翻译阶段。
- remaining issues: `config.example.json`, manifest schema, output convention, downloader interface, URL/local dispatch, and failure-reporting format still need implementation design.
- next step: Define Phase 1 implementation contract, then implement the minimal downloader script in a separate task.
- major decision status: See `DECISIONS.md` entry at 2026/07/05 11:23.

## 2026/07/05 12:59

- task type: implementation
- task goal: Migrate `Video Language Pipeline` from root `SKILL.md` into a multi-skill suite scaffold.
- changes made: Removed root `SKILL.md`; created `vlp-orchestrator`, `vlp-video-download`, and `vlp-subtitle-polish` skill scaffolds; added suite/media/subtitle/manifest specs; added `config.example.json` and examples placeholder; updated root README, AGENTS, progress, research, and decision records.
- files changed: `AGENTS.md`, `README.md`, `RESEARCH.md`, `PROGRESS.md`, `DECISIONS.md`, `ITERATION_LOG.md`, `config.example.json`, `skills/vlp-orchestrator/SKILL.md`, `skills/vlp-video-download/SKILL.md`, `skills/vlp-video-download/scripts/README.md`, `skills/vlp-subtitle-polish/SKILL.md`, `specs/suite-contract.md`, `specs/media-ingest-contract.md`, `specs/subtitle-polish-contract.md`, `specs/job-manifest.schema.md`, `examples/README.md`, removed root `SKILL.md`
- verification status: `test ! -e 'self/Video Language Pipeline/SKILL.md'` passed; all three child `SKILL.md` files exist; `rg --files` confirmed the suite scaffold; AGENTS/README routing guidance is discoverable; `vlp-video-download` only mentions ASS/SRT/burn-in as non-responsibilities; `git diff --no-index --check` passed for Markdown/JSON files; no executable scripts were added.
- status after task: Multi-skill suite scaffold created; no feature logic implemented.
- rationale / 当时判断: 三个技能必须独立可用，root `SKILL.md` 会造成可调用入口歧义，因此采用 `skills/<skill-name>/SKILL.md` 的 suite layout。
- remaining issues: No downloader implementation, no transcription, no translation, no subtitle polish implementation, no ASS/SRT generation, no burn-in.
- next step: Define and implement the minimal `vlp-video-download` media-ingest script in a separate task.
- major decision status: See `DECISIONS.md` entry at 2026/07/05 12:59.

## 2026/07/05 13:14

- task type: implementation
- task goal: Implement the minimal usable `vlp-video-download` media-ingest module.
- changes made: Added `scripts/media_ingest.py` with URL/local dispatch, per-run output directories, `manifest.json`, `run.log`, clear `yt-dlp` missing-dependency failure, and local self-checks; updated the download skill docs and progress record.
- files changed: `skills/vlp-video-download/scripts/media_ingest.py`, `skills/vlp-video-download/SKILL.md`, `skills/vlp-video-download/scripts/README.md`, `PROGRESS.md`, `ITERATION_LOG.md`
- verification status: `python3 -m py_compile` passed; `python3 scripts/media_ingest.py --self-check` passed; missing local-file run returned failure with `manifest.json` and `run.log`; root `SKILL.md` remains absent; `--help` works; whitespace check passed for Markdown/JSON/Python files.
- status after task: Minimal `vlp-video-download` implementation exists; no transcription, translation, subtitle polish, ASS/SRT generation, burn-in, or orchestrator calling logic was added.
- rationale / 当时判断: 第一版只需要可运行、可记录、可追踪；本地文件登记不复制大文件，URL 下载仅依赖 `yt-dlp`，失败也尽量留下 manifest/log。
- remaining issues: No metadata probing, no format selection, no platform-specific adapter, no audio extraction.
- next step: Exercise with a real URL when the user provides one or approves a network download test.
- major decision status: Major decision: none

## 2026/07/05 13:32

- task type: implementation
- task goal: Optimize `vlp-video-download` against the download-only parts of `xiaohu-video-download`.
- changes made: Added H.264-first MP4 default format, `--format`, `--output-template`, `--force-cookies`, `--no-cookies-fallback`, retry/cookies fallback behavior, clean filename/retry/merge yt-dlp options, and richer manifest attempt metadata; updated download skill docs and progress record.
- files changed: `skills/vlp-video-download/scripts/media_ingest.py`, `skills/vlp-video-download/SKILL.md`, `skills/vlp-video-download/scripts/README.md`, `PROGRESS.md`, `ITERATION_LOG.md`
- verification status: `python3 -m py_compile` passed; `--self-check` passed; missing-file failure still writes `manifest.json` and `run.log`; CLI help shows new `--format`, `--output-template`, `--force-cookies`, and `--no-cookies-fallback`; root `SKILL.md` remains absent; scope grep shows Whisper/transcribe/translate/burn/ASS/SRT/subtitle only in non-responsibilities or deliberately excluded docs; whitespace check passed.
- status after task: `vlp-video-download` remains download-only and has reference-aligned retry/cookies/H.264 behavior; no real URL download was run.
- rationale / 当时判断: `xiaohu-video-download` 的可复用部分是下载策略和错误兜底，不是字幕、转写、翻译或烧录流程；本次只搬下载层约束。
- remaining issues: No metadata probing, no real URL smoke test, no platform-specific adapter, no audio extraction.
- next step: Run a real URL download test only after the user provides a URL or explicitly approves network testing.
- major decision status: Major decision: none

## 2026/07/05 13:40

- task type: implementation
- task goal: Localize skill-facing content to Chinese-first mixed language and split `vlp-video-download` Python code by responsibility.
- changes made: Rewrote the three child `SKILL.md` files in Chinese-first style; updated download scripts documentation; split the downloader implementation into CLI, common helpers, run record, local ingest, and URL download modules; localized user-facing CLI help and common error messages.
- files changed: `skills/vlp-orchestrator/SKILL.md`, `skills/vlp-video-download/SKILL.md`, `skills/vlp-subtitle-polish/SKILL.md`, `skills/vlp-video-download/scripts/README.md`, `skills/vlp-video-download/scripts/media_ingest.py`, `skills/vlp-video-download/scripts/common.py`, `skills/vlp-video-download/scripts/run_record.py`, `skills/vlp-video-download/scripts/local_ingest.py`, `skills/vlp-video-download/scripts/url_download.py`, `PROGRESS.md`, `ITERATION_LOG.md`
- verification status: `python3 -m py_compile` passed for all split Python modules; `--self-check` passed; missing local-file run returned failure and wrote `manifest.json` / `run.log`; root `SKILL.md` remains absent; CLI help is Chinese-first; scope grep confirms subtitle/translation/burn terms in `vlp-video-download` only appear as excluded/deferred scope; whitespace check passed for changed Markdown/Python files.
- status after task: `vlp-video-download` remains download-only, but its implementation is no longer a single catch-all script.
- rationale / 当时判断: 单脚本适合最小闭环，但继续扩展会模糊 media ingest、记录和下载调用边界；拆分后更适合作为后续转写、翻译、字幕处理的稳定输入层。
- remaining issues: No real URL smoke test, no metadata probing, no platform-specific adapter, no audio extraction.
- next step: Run verification, then implement metadata probing or real URL smoke test only in a separate task.
- major decision status: Major decision: none

## 2026/07/05 13:47

- task type: correction
- task goal: Correct `vlp-video-download` design after comparing against reference site-specific downloader scripts.
- changes made: Added URL site adapter dispatch; added `site_downloaders/generic.py`, `site_downloaders/youtube.py`, adapter registry, and a direct `youtube_download.py` entry; updated current docs to remove the single-loop framing and make site adapter boundaries part of the download design.
- files changed: `AGENTS.md`, `README.md`, `RESEARCH.md`, `PROGRESS.md`, `DECISIONS.md`, `ITERATION_LOG.md`, `specs/media-ingest-contract.md`, `skills/vlp-video-download/SKILL.md`, `skills/vlp-video-download/scripts/README.md`, `skills/vlp-video-download/scripts/media_ingest.py`, `skills/vlp-video-download/scripts/url_download.py`, `skills/vlp-video-download/scripts/youtube_download.py`, `skills/vlp-video-download/scripts/site_downloaders/__init__.py`, `skills/vlp-video-download/scripts/site_downloaders/generic.py`, `skills/vlp-video-download/scripts/site_downloaders/youtube.py`
- verification status: `python3 -m py_compile` passed for the downloader scripts and adapters; `media_ingest.py --self-check` passed; `youtube_download.py --help` works; missing local-file run still writes `manifest.json` / `run.log`; adapter dispatch check maps YouTube URLs to `youtube` and other URLs to `generic`; root `SKILL.md` remains absent.
- status after task: `vlp-video-download` is still download-only, but URL handling now has explicit site adapter boundaries instead of one generic command path.
- rationale / 当时判断: 参考项目的可复用经验不只是 cookies fallback 和 H.264 format，也包括按网站拆开下载脚本；继续保留单一路径会影响后续 Douyin/Bilibili/X/Twitter 等平台扩展。
- remaining issues: No real URL smoke test, no `ffprobe` metadata probing, no Douyin/Bilibili/X/Twitter adapter, no playlist batch handling, no audio extraction.
- next step: Add the next site adapter only when a concrete platform target or failing URL appears; otherwise prioritize `ffprobe` metadata probing after download.
- major decision status: See `DECISIONS.md` entry at 2026/07/05 13:47.

## 2026/07/05 14:02

- task type: implementation
- task goal: Migrate the reference downloader's explicit platform set into `vlp-video-download`.
- changes made: Added Bilibili and Douyin site adapters; added Bilibili/Douyin direct entry scripts and Douyin login script; added `--playlist-items`, `--list`, and `--resolution`; updated docs, media-ingest contract, progress, research, decisions, and local ignore rules.
- files changed: `.gitignore`, `README.md`, `RESEARCH.md`, `PROGRESS.md`, `DECISIONS.md`, `ITERATION_LOG.md`, `specs/media-ingest-contract.md`, `skills/vlp-video-download/SKILL.md`, `skills/vlp-video-download/scripts/README.md`, `skills/vlp-video-download/scripts/common.py`, `skills/vlp-video-download/scripts/media_ingest.py`, `skills/vlp-video-download/scripts/bilibili_download.py`, `skills/vlp-video-download/scripts/douyin_download.py`, `skills/vlp-video-download/scripts/douyin_login.py`, `skills/vlp-video-download/scripts/site_downloaders/__init__.py`, `skills/vlp-video-download/scripts/site_downloaders/bilibili.py`, `skills/vlp-video-download/scripts/site_downloaders/douyin.py`, `skills/vlp-video-download/scripts/site_downloaders/generic.py`, `skills/vlp-video-download/scripts/site_downloaders/youtube.py`
- verification status: `python3 -m py_compile` passed via `find -print0`; `media_ingest.py --self-check` passed; direct script `--help` checks passed for YouTube, Bilibili, Douyin download, and Douyin login; playlist parser accepted `all`, `1:5`, `1,3,5` and rejected invalid examples; routing check maps YouTube/Bilibili/Douyin/generic hosts correctly; missing local file still writes `manifest.json` / `run.log`; missing Douyin profile fails cleanly with `douyin_login_required`; root `SKILL.md` remains absent.
- status after task: `vlp-video-download` supports the reference downloader's explicit platform set: YouTube, Bilibili, Douyin, and generic `yt-dlp`, while remaining download-only.
- rationale / 当时判断: 参考项目的网站设计不只是 Douyin；YouTube fallback、Bilibili playlist/合集/分P、Douyin 登录态抓取都应进入下载层，但字幕、转写、翻译、烧录仍然保持排除。
- remaining issues: No real network smoke test, no `ffprobe` metadata probing, no audio-only download, no Douyin audio/both mode, no subtitle/transcription/translation/burn-in.
- next step: Run real URL smoke tests when the user provides YouTube, Bilibili, and Douyin URLs; after that add `ffprobe` metadata probing.
- major decision status: See `DECISIONS.md` entry at 2026/07/05 13:56.

## 2026/07/05 14:08

- task type: refactor
- task goal: Reframe `Video Language Pipeline` as a four-skill suite.
- changes made: Renamed `vlp-subtitle-polish` to `vlp-translation-polish`; renamed the subtitle polish contract to translation polish; added `vlp-speech-transcribe` scaffold and speech transcribe contract; updated suite docs, routing rules, phase order, research, progress, and decisions.
- files changed: `AGENTS.md`, `README.md`, `RESEARCH.md`, `PROGRESS.md`, `DECISIONS.md`, `ITERATION_LOG.md`, `skills/vlp-orchestrator/SKILL.md`, `skills/vlp-speech-transcribe/SKILL.md`, `skills/vlp-speech-transcribe/scripts/README.md`, `skills/vlp-translation-polish/SKILL.md`, `skills/vlp-translation-polish/scripts/README.md`, `specs/suite-contract.md`, `specs/speech-transcribe-contract.md`, `specs/translation-polish-contract.md`, removed `skills/vlp-subtitle-polish/`, removed `specs/subtitle-polish-contract.md`
- verification status: Structure checks passed: no root `SKILL.md`, old subtitle-focused skill directory removed, new speech/translation skill files exist, new contracts exist; old exact skill/contract names now appear only in historical `ITERATION_LOG.md`; no Phase 2/3 implementation scripts were added; whitespace check passed for Markdown/JSON files; `rg --files` confirms the four-skill suite structure.
- status after task: The suite has four callable skills; Phase 1 still prioritizes `vlp-video-download`; Phase 2/3 behavior is scaffold-only.
- rationale / 当时判断: Speech transcription and text translation/polish are different layers. Keeping translation under a subtitle-only name would distort future routing and make Markdown/transcript workflows feel secondary.
- remaining issues: No Whisper / ASR implementation, no translation/polish implementation, no subtitle render/burn-in implementation.
- next step: Run structural and reference checks, then continue Phase 1 downloader hardening unless the user explicitly starts Phase 2.
- major decision status: See `DECISIONS.md` entry at 2026/07/05 14:08.

## 2026/07/05 14:21

- task type: planning
- task goal: Design `vlp-translation-polish` by copying `xiaohu-subtitle-polish` content, then adapting it to the four-skill architecture.
- changes made: Copied the reference skill's `SKILL.md`, `gemini-extension.json`, and `bilingual_ass.py`; rewrote `vlp-translation-polish/SKILL.md` as a text-asset translation/polish layer; updated extension metadata; hardened `bilingual_ass.py` with strict SRT parsing, timestamp validation, ASS special-character handling, `PlayResX/PlayResY`, and `--self-check`; updated scripts README, translation polish contract, root README, and progress record.
- files changed: `README.md`, `PROGRESS.md`, `ITERATION_LOG.md`, `specs/translation-polish-contract.md`, `skills/vlp-translation-polish/SKILL.md`, `skills/vlp-translation-polish/gemini-extension.json`, `skills/vlp-translation-polish/scripts/README.md`, `skills/vlp-translation-polish/scripts/bilingual_ass.py`
- verification status: `python3 -m py_compile` passed for `bilingual_ass.py`; `python3 scripts/bilingual_ass.py --self-check` passed; `--help` works; directory-level `find -print0 | xargs -0 python3 -m py_compile` passed; root `SKILL.md` remains absent; grep confirmed old ffmpeg/burn references only remain in non-responsibility/future-layer notes.
- status after task: `vlp-translation-polish` is no longer a pure placeholder. It has a designed responsibility boundary and one small subtitle text-asset utility, but still has no translation/polish runner or model invocation.
- rationale / 当时判断: `xiaohu-subtitle-polish` 的可复用价值在翻译润色规则、术语策略和双语字幕资产经验；Whisper、ffmpeg、下载联动和烧录流程不应进入 translation layer。
- remaining issues: No runnable translation/polish runner, no glossary or translation memory implementation, no Markdown/SRT/VTT parser runner, no manifest-writing implementation for this skill.
- next step: Define the smallest runnable text translation/polish runner for existing text assets, or return to Phase 1 downloader hardening if language processing remains deferred.
- major decision status: Major decision: none

## 2026/07/05 14:22

- task type: implementation
- task goal: Add optional `ffprobe` result validation to `vlp-video-download`.
- changes made: Added shared `media_probe.py`; called it after local ingest success, generic/YouTube/Bilibili download success, and Douyin download success; updated self-check to assert `media_probe` or `ffprobe_*` warning appears; updated download docs and manifest/media-ingest specs.
- files changed: `skills/vlp-video-download/scripts/media_probe.py`, `skills/vlp-video-download/scripts/local_ingest.py`, `skills/vlp-video-download/scripts/media_ingest.py`, `skills/vlp-video-download/scripts/site_downloaders/generic.py`, `skills/vlp-video-download/scripts/site_downloaders/douyin.py`, `skills/vlp-video-download/SKILL.md`, `skills/vlp-video-download/scripts/README.md`, `specs/media-ingest-contract.md`, `specs/job-manifest.schema.md`, `PROGRESS.md`, `ITERATION_LOG.md`
- verification status: `find ... -print0 | xargs -0 python3 -m py_compile` passed; `media_ingest.py --self-check` passed; local temp-file ingest wrote `manifest.json` / `run.log` and produced `ffprobe_failed` warning while keeping status success; scope grep found transcription/translation/burn terms only in non-responsibility docs; root `SKILL.md` remains absent; whitespace check passed for changed Markdown/Python files.
- status after task: Download/local ingest success paths attempt non-fatal media probing; `ffprobe` absence or failure only produces warnings.
- rationale / 当时判断: Media ingest needs a cheap diagnostic summary for downstream stages, but probing must not turn a successful download or local registration into a failed job.
- remaining issues: No real media URL smoke test, no automatic quality policy, no retry/redownload behavior, no independent metadata file.
- next step: Run verification, then test with a real media URL or real local media file when available.
- major decision status: Major decision: none

## 2026/07/05 14:31

- task type: correction
- task goal: Clean production `SKILL.md` files so development-state and migration notes do not pollute runtime skill prompts.
- changes made: Rewrote all four `skills/*/SKILL.md` files as production usage instructions; moved implementation status, reference learnings, exclusions, migration rationale, and next steps into per-skill `DEVELOPMENT_NOTES.md`; updated progress record.
- files changed: `PROGRESS.md`, `ITERATION_LOG.md`, `skills/vlp-orchestrator/SKILL.md`, `skills/vlp-orchestrator/DEVELOPMENT_NOTES.md`, `skills/vlp-video-download/SKILL.md`, `skills/vlp-video-download/DEVELOPMENT_NOTES.md`, `skills/vlp-speech-transcribe/SKILL.md`, `skills/vlp-speech-transcribe/DEVELOPMENT_NOTES.md`, `skills/vlp-translation-polish/SKILL.md`, `skills/vlp-translation-polish/DEVELOPMENT_NOTES.md`
- verification status: `rg -n "当前状态|继承自|不继承|从参考项目|Phase 1|Phase 2|scaffold|xiaohu" skills/*/SKILL.md` returned no matches; each skill directory has `DEVELOPMENT_NOTES.md`; root `SKILL.md` remains absent; `find skills -name '*.py' -print0 | xargs -0 python3 -m py_compile` passed; `bilingual_ass.py --self-check` passed; generated `__pycache__` directories were removed.
- status after task: Production skill prompts are clean runtime instructions. Development and migration context is preserved outside production prompts.
- rationale / 当时判断: `SKILL.md` is production prompt material and should not contain project-history explanations. Reference-source and phase/status details remain useful, but belong in development notes and project records.
- remaining issues: No translation/polish runner, no ASR runner, no real URL smoke test.
- next step: Continue with the next implementation task using `SKILL.md` for runtime behavior and `DEVELOPMENT_NOTES.md` for design context.
- major decision status: Major decision: none

## 2026/07/05 15:54

- task type: implementation
- task goal: Implement the minimal usable `vlp-speech-transcribe` local transcription layer.
- changes made: Added `scripts/transcribe_srt.py` for local audio/video or media ingest manifest input; implemented per-run `manifest.json` / `run.log`; added video audio extraction through `ffmpeg`; added `mlx-whisper` then `faster-whisper` ASR selection; added SRT/TXT output; updated production skill instructions, development notes, scripts README, speech transcribe contract, root README, and progress record.
- files changed: `README.md`, `PROGRESS.md`, `ITERATION_LOG.md`, `specs/speech-transcribe-contract.md`, `skills/vlp-speech-transcribe/SKILL.md`, `skills/vlp-speech-transcribe/DEVELOPMENT_NOTES.md`, `skills/vlp-speech-transcribe/scripts/README.md`, `skills/vlp-speech-transcribe/scripts/transcribe_srt.py`
- verification status: `transcribe_srt.py --self-check` passed without Whisper/ffmpeg; `python3 -m py_compile` passed; missing input test returned failure and wrote failed `manifest.json` / `run.log`; ASR dependency probe found both `mlx_whisper` and `faster_whisper` importable locally, so the missing-ASR test was not run to avoid triggering model/runtime paths; no real media transcription smoke test was run.
- status after task: `vlp-speech-transcribe` has a minimal independent local transcription path and remains separated from download, translation, rendering, and burn-in.
- rationale / 当时判断: The reference project's useful part is word-level timestamp transcription and SRT segmentation, not mixing transcription into download or video rendering.
- remaining issues: No real media smoke test, no `whisper-cli` fallback, no auto-install, no Markdown generation.
- next step: Run a real local audio/video smoke test when a sample file is available.
- major decision status: Major decision: none

## 2026/07/05 14:52

- task type: planning
- task goal: Optimize `vlp-translation-polish` structure as a unified text-language processing skill.
- changes made: Reworked the production `vlp-translation-polish/SKILL.md` around input detection, mode selection, default translation policy, terminology/glossary, chunking, task context state, format preservation, translation/polish pass, output rendering, manifest, and optional debug diagnostics; updated `translation-polish-contract.md`; updated `vlp-translation-polish/DEVELOPMENT_NOTES.md`; updated progress record.
- files changed: `PROGRESS.md`, `ITERATION_LOG.md`, `specs/translation-polish-contract.md`, `skills/vlp-translation-polish/SKILL.md`, `skills/vlp-translation-polish/DEVELOPMENT_NOTES.md`
- verification status: Production `SKILL.md` grep for development-state/reference terms returned no matches; manual reread confirmed the skill handles text assets only and keeps video/audio/ASR/burn-in out of scope.
- status after task: `vlp-translation-polish` is documented as a unified text-language processing skill rather than a subtitle-only translator.
- rationale / 当时判断: The skill needs a stable runtime structure for translation behavior, terminology consistency, format preservation, task-local context, traceable outputs, and non-default diagnostics.
- remaining issues: No runnable input detector, mode selector, parser/preservation helpers, glossary implementation, manifest writer, or translation/polish runner exists yet.
- next step: Implement the smallest input detection + mode selection layer before adding translation execution.
- major decision status: Major decision: none

## 2026/07/05 14:56

- task type: implementation
- task goal: Add audio-only and raw subtitle-only download modes to `vlp-video-download` while keeping the skill inside media ingest scope.
- changes made: Added `--mode video|audio|subtitles|metadata` and `--sub-langs`; implemented audio-only download with `yt-dlp -x --audio-format mp3`; implemented raw subtitle-only download with `yt-dlp --skip-download --write-subs --write-auto-subs`; routed YouTube/Bilibili through the shared generic mode implementation; added Douyin audio mode when `audio_url` is available and clear unsupported failure for Douyin subtitles.
- files changed: `skills/vlp-video-download/scripts/media_ingest.py`, `skills/vlp-video-download/scripts/run_record.py`, `skills/vlp-video-download/scripts/site_downloaders/generic.py`, `skills/vlp-video-download/scripts/site_downloaders/youtube.py`, `skills/vlp-video-download/scripts/site_downloaders/bilibili.py`, `skills/vlp-video-download/scripts/site_downloaders/douyin.py`, `skills/vlp-video-download/SKILL.md`, `skills/vlp-video-download/DEVELOPMENT_NOTES.md`, `skills/vlp-video-download/scripts/README.md`, `specs/media-ingest-contract.md`, `specs/job-manifest.schema.md`, `PROGRESS.md`, `ITERATION_LOG.md`
- verification status: `find ... -name '*.py' -print0 | xargs -0 python3 -m py_compile` passed; `media_ingest.py --help` shows `--mode` and `--sub-langs`; `media_ingest.py --self-check` passed with local registration, missing-file failure, metadata mode, manifest/log generation, and ffprobe warning/probe assertion.
- status after task: `vlp-video-download` supports video, audio, subtitles, and metadata ingest modes. It still does not perform transcription, translation, subtitle polish, subtitle render, or burn-in.
- rationale / 当时判断: Audio and raw subtitle download are still media ingest responsibilities when they only fetch source assets and preserve traceable manifests. Language processing remains in `vlp-speech-transcribe` and `vlp-translation-polish`.
- remaining issues: No real URL smoke test was run because no concrete URL was provided; Douyin audio support depends on `aweme detail` exposing `audio_url`; subtitle availability depends on platform metadata.
- next step: Run real URL smoke tests for video/audio/subtitles when the user provides specific YouTube/Bilibili/Douyin URLs.
- major decision status: Major decision: none

## 2026/07/05 15:06

- task type: implementation
- task goal: Make `vlp-video-download` automatically attempt raw subtitle download after a successful video download.
- changes made: Reused the existing raw subtitle `yt-dlp --skip-download --write-subs --write-auto-subs` path as a best-effort post-video step for YouTube/Bilibili/generic adapters; preserved video success when subtitles fail or return no files; added manifest fields for subtitle attempt status, return code, retry count, output template, language request, and subtitle files; updated skill docs and media-ingest specs.
- files changed: `skills/vlp-video-download/scripts/site_downloaders/generic.py`, `skills/vlp-video-download/SKILL.md`, `skills/vlp-video-download/scripts/README.md`, `specs/media-ingest-contract.md`, `specs/job-manifest.schema.md`, `PROGRESS.md`, `ITERATION_LOG.md`
- verification status: `find skills/vlp-video-download/scripts -name '*.py' -print0 | xargs -0 python3 -m py_compile` passed; `media_ingest.py --self-check` passed; real YouTube smoke test on `https://www.youtube.com/watch?v=jNQXAC9IVRw` downloaded the video and then generated `jNQXAC9IVRw.en.vtt` through the automatic subtitle attempt; manifest status stayed `success` and recorded `subtitle_attempted_after_video`, subtitle attempts, and `subtitle_files`.
- status after task: Default video mode now downloads video first and then tries raw platform subtitles for yt-dlp adapters. `subtitles` mode remains available for subtitle-only runs.
- rationale / 当时判断: This mirrors the useful part of the reference workflow while keeping subtitle download inside media ingest and keeping translation, cleaning, bilingual layout, render, and burn-in out of this skill.
- remaining issues: Douyin subtitles remain unsupported; Bilibili/generic auto-subtitle behavior still needs real URL smoke tests; subtitle availability depends on platform metadata and language selection.
- next step: Add a config/documented switch if users need to disable automatic subtitle attempts, or continue with Bilibili/Douyin smoke tests.
- major decision status: Major decision: none

## 2026/07/05 15:11

- task type: correction
- task goal: Re-align `Video Language Pipeline` as an agent-first skill suite, not a CLI-first automation product.
- changes made: Updated suite docs to make `SKILL.md` the primary runtime interface; framed scripts as optional helpers for deterministic work; simplified `vlp-translation-polish` away from mandatory automated runner language; updated translation/suite/speech contracts, research notes, progress, and translation polish development notes; added an agent-first decision entry.
- files changed: `README.md`, `AGENTS.md`, `DECISIONS.md`, `RESEARCH.md`, `PROGRESS.md`, `ITERATION_LOG.md`, `specs/suite-contract.md`, `specs/speech-transcribe-contract.md`, `specs/translation-polish-contract.md`, `skills/vlp-speech-transcribe/SKILL.md`, `skills/vlp-speech-transcribe/DEVELOPMENT_NOTES.md`, `skills/vlp-translation-polish/SKILL.md`, `skills/vlp-translation-polish/DEVELOPMENT_NOTES.md`
- verification status: Docs-only change; no Python code was added or modified. Planned grep checks confirm agent-first framing and show automation terms only in negative/deferred boundary language; root `SKILL.md` remains absent; existing helper script set is unchanged.
- status after task: The project boundary is documented as agent-first. `vlp-video-download` remains the main scriptable Phase 1 layer; `vlp-translation-polish` remains agent-guided with optional helpers.
- rationale / 当时判断: Language translation and polish benefit from agent judgment. Turning every language step into CLI automation now would add complexity and reduce flexibility.
- remaining issues: No ASR automation path, no translation/polish CLI, no render/burn-in layer.
- next step: Continue media ingest hardening, or add only narrowly scoped helpers when a concrete task requires them.
- major decision status: See `DECISIONS.md` entry at 2026/07/05 15:11.

## 2026/07/05 15:20

- task type: correction
- task goal: Clarify agent-first with selective tooling across the suite.
- changes made: Updated README, AGENTS, suite contract, speech contract, decision wording, progress, and translation polish development notes to distinguish tool-heavy deterministic media/transcription work from agent-first language judgment work.
- files changed: `README.md`, `AGENTS.md`, `DECISIONS.md`, `PROGRESS.md`, `ITERATION_LOG.md`, `specs/suite-contract.md`, `specs/speech-transcribe-contract.md`, `skills/vlp-translation-polish/DEVELOPMENT_NOTES.md`
- verification status: Docs-only change; no implementation code added. Manual checks confirmed the suite now states `vlp-orchestrator` is agent-reasoning-first, `vlp-video-download` is script-heavy, `vlp-speech-transcribe` is future tool-heavy, and `vlp-translation-polish` is agent-first/tool-light.
- status after task: The project boundary is agent-first with selective tooling, not tool-minimal and not CLI-first.
- rationale / 当时判断: The right boundary is not to avoid scripts broadly. It is to script deterministic media operations while preserving agent semantic judgment for translation and polish.
- remaining issues: No ASR automation path, no translation/polish CLI, no render/burn-in layer.
- next step: Keep Phase 1 focused on media ingest; add speech automation only when that layer starts, and keep language tooling limited to small deterministic helpers unless explicitly requested.
- major decision status: Updated wording for `DECISIONS.md` entry at 2026/07/05 15:11.

## 2026/07/05 15:36

- task type: implementation
- task goal: Add a small deterministic Markdown translation validator for URL and structure preservation.
- changes made: Added `validate_markdown_translation.py`; documented mandatory Markdown validation in `vlp-translation-polish/SKILL.md`; updated scripts README, translation polish contract, progress, and development notes.
- files changed: `PROGRESS.md`, `ITERATION_LOG.md`, `specs/translation-polish-contract.md`, `skills/vlp-translation-polish/SKILL.md`, `skills/vlp-translation-polish/DEVELOPMENT_NOTES.md`, `skills/vlp-translation-polish/scripts/README.md`, `skills/vlp-translation-polish/scripts/validate_markdown_translation.py`
- verification status: `validate_markdown_translation.py --self-check` passed; `py_compile` passed; manual positive Markdown URL test passed; manual negative Substack URL mutation test failed with exit code 1 and reported the changed URL; root `SKILL.md` remains absent.
- status after task: Markdown translation now has a lightweight mechanical guard for URL and basic structure preservation. No translation runner or parser framework was added.
- rationale / 当时判断: URL and Markdown structure preservation is deterministic and cheap to validate with a helper. Translation and polish remain agent-guided.
- remaining issues: Reference-style Markdown links are not supported by the validator yet; add only when a real failing case appears.
- next step: Use the validator after Markdown translations and fix any URL/structure mismatch before delivery.
- major decision status: Major decision: none
