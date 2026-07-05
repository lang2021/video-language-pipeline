from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from run_record import RunRecord


def _stream(streams: list[dict], codec_type: str) -> dict:
    for stream in streams:
        if stream.get("codec_type") == codec_type:
            return stream
    return {}


def _warn(run: RunRecord, code: str, message: str) -> None:
    run.warnings.append({"code": code, "message": message})
    run.log(f"WARNING {code}: {message}")


def probe_media(run: RunRecord, media_path: Path) -> None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        _warn(run, "ffprobe_missing", "系统未安装 ffprobe，已跳过媒体信息校验。")
        return

    cmd = [
        ffprobe,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(media_path),
    ]
    run.log(f"ffprobe: {' '.join(cmd)}")
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        summary = (proc.stderr or proc.stdout or "").strip().splitlines()
        message = summary[0] if summary else f"ffprobe exited with code {proc.returncode}"
        _warn(run, "ffprobe_failed", message[:300])
        return

    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        _warn(run, "ffprobe_parse_failed", f"ffprobe JSON 解析失败：{exc}")
        return

    streams = data.get("streams") or []
    fmt = data.get("format") or {}
    video = _stream(streams, "video")
    audio = _stream(streams, "audio")
    run.outputs["media_probe"] = {
        "duration": fmt.get("duration"),
        "format_name": fmt.get("format_name"),
        "video_codec": video.get("codec_name"),
        "audio_codec": audio.get("codec_name"),
        "width": video.get("width"),
        "height": video.get("height"),
        "has_video": bool(video),
        "has_audio": bool(audio),
    }
