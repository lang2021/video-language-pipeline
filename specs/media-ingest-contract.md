# Media Ingest Contract

Updated: 2026/07/05 15:06

## Skill

`vlp-video-download`

## Status

Phase 1 active. `vlp-video-download` implements local file registration and URL download through site adapters.

## Inputs

- URL input, such as a single video URL.
- Local file input, such as an existing video or audio path.
- `output_dir` from configuration or job options.
- Optional `cookies_browser`.
- Optional `proxy`.
- Optional quality or format preference.
- Optional `mode`: `video`, `audio`, `subtitles`, or `metadata`.
- Optional `sub_langs` for raw subtitle download.
- Optional `playlist_items` for YouTube/Bilibili playlist, collection, or multi-part downloads.
- Optional `list` mode for resource inspection without media download.
- Optional `resolution` for Douyin video selection.
- Optional chunk-size setting in a future implementation.

## Outputs

- downloaded video path when URL video download succeeds.
- downloaded audio path when URL audio mode succeeds.
- downloaded raw subtitle files when subtitle mode succeeds.
- raw subtitle files or subtitle warning metadata when URL video mode performs the best-effort subtitle attempt.
- registered local file path when input is local.
- metadata path.
- `outputs.media_probe` summary when `ffprobe` succeeds.
- job manifest path.
- error log path / run log path.

## Output Directory Convention

The implementation should resolve `output_dir` before writing. Known subdirectories should be used for generated artifacts, such as:

- `tmp/` for intermediate files.
- `data/` for media outputs.
- `runs/<job_id>/` for manifests and logs.

Exact directory names may be refined during implementation, but silent writes to the current directory are not allowed.

## Metadata

Media ingest should record basic media metadata when possible:

- codec information
- width / height
- duration
- audio stream presence
- selected download formats
- selected ingest mode
- subtitle language request when subtitle mode is used
- raw subtitle file paths when subtitle mode succeeds
- whether video mode attempted raw subtitle download after the video succeeded
- subtitle attempt return code and warning details when the automatic subtitle attempt fails or returns no files
- selected site adapter
- playlist parameters when used
- Douyin profile/detail metadata when Douyin is used

`media_probe` should include duration, format/container name, video codec, audio codec, width, height, `has_video`, and `has_audio`.

## Failure Behavior

- Failed runs must still produce a manifest or equivalent failure record.
- Raw command output should be retained in `run.log`.
- User-facing summaries should include error summary and log path.
- Missing or failed `ffprobe` must produce a warning only; it must not turn a successful download/local ingest into a failed run.
- Subtitle mode must not fabricate subtitle files. If the platform returns none, the run should keep the command output and report a clear missing-subtitles failure or empty-result state.
- Video mode may perform a best-effort raw subtitle attempt after the video succeeds. This attempt must not turn a successful video download into a failed run; failures or empty results should be recorded as warnings with command output preserved in `run.log`.
- Douyin subtitle download is currently unsupported and should fail clearly before attempting unrelated work.

## Configuration

Cookies, proxy, output directory, quality preference, and chunk size must be configuration or job options. They must not be hidden hardcoded values.

## Site Adapter Boundary

URL download must route through a site adapter:

- `generic`: default `yt-dlp` path for sites without custom handling.
- `youtube`: YouTube-specific path for retry/cookies behavior and future YouTube-only fixes.
- `bilibili`: Bilibili-specific path for single video and explicit playlist/collection/multi-part downloads.
- `douyin`: Douyin-specific path for login-state browser capture, resource listing, and video download.

## Mode Boundary

- `video`: download video media, then best-effort raw platform subtitles for YouTube/Bilibili/generic `yt-dlp` adapters.
- `audio`: download audio media only; no Whisper / ASR work.
- `subtitles`: download raw platform subtitles only; no translation, cleaning, bilingual layout, render, or burn-in.
- `metadata`: inspect/list resource metadata only; no media download.

X/Twitter is currently only an H.264 compatibility target, not a downloader adapter. Reddit / `v.redd.it` is not part of the reference downloader's explicit platform set and is not included in this phase.
