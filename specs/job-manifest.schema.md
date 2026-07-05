# Job Manifest Schema

Updated: 2026/07/05 14:56

## Status

Minimal Phase 1 schema. It may evolve as implementation starts.

## Minimal Shape

```json
{
  "job_id": "",
  "skill": "",
  "status": "success|failed|partial",
  "input": {},
  "outputs": {},
  "errors": [],
  "warnings": [],
  "created_at": "",
  "completed_at": ""
}
```

## Field Notes

- `job_id`: stable identifier for one run.
- `skill`: skill that produced the manifest.
- `status`: one of `success`, `failed`, or `partial`.
- `input`: structured input summary.
- `outputs`: structured output paths and metadata.
- `errors`: machine-readable or human-readable error entries.
- `warnings`: non-fatal issues.
- `created_at`: run creation timestamp.
- `completed_at`: completion timestamp when available.

## `vlp-video-download` Media Probe

Successful local ingest or download may add `outputs.media_probe`:

```json
{
  "duration": "",
  "format_name": "",
  "video_codec": "",
  "audio_codec": "",
  "width": 0,
  "height": 0,
  "has_video": true,
  "has_audio": true
}
```

If `ffprobe` is missing or fails, the run should stay successful and add a warning such as `ffprobe_missing`, `ffprobe_failed`, or `ffprobe_parse_failed`.

## `vlp-video-download` Mode Outputs

`outputs.mode` records the selected ingest mode:

```json
{
  "mode": "video|audio|subtitles|metadata"
}
```

Video and audio downloads should record:

```json
{
  "output_file_path": "",
  "file_size_bytes": 0,
  "attempts": []
}
```

Video mode may also record a best-effort raw subtitle attempt:

```json
{
  "subtitle_attempted_after_video": true,
  "sub_langs": "zh-Hans,zh-CN,en,ja",
  "subtitle_output_template": "",
  "subtitle_attempt_returncode": 0,
  "subtitle_retry_count": 0,
  "subtitle_files": []
}
```

If the post-video subtitle attempt fails or returns no files, the video run should stay successful and include a warning such as `subtitle_auto_download_failed` or `subtitle_files_missing_after_video`.

Audio mode may also record:

```json
{
  "audio_format": "mp3"
}
```

Subtitle mode should record:

```json
{
  "sub_langs": "zh-Hans,zh-CN,en,ja",
  "subtitle_files": [],
  "attempts": []
}
```

If no subtitles are available, the downloader must not invent files. It should preserve command output in `run.log` and write a clear error or empty-result record.

## Suite Handoff

Child skills should preserve prior manifest references when one skill hands off to another. The orchestrator should summarize manifests rather than hiding details in prose only.
