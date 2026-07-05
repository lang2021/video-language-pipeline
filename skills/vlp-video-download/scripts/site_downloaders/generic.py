from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from common import DEFAULT_FORMAT, DEFAULT_OUTPUT_TEMPLATE, DEFAULT_PLAYLIST_OUTPUT_TEMPLATE, normalize_playlist_items
from media_probe import probe_media
from run_record import RunRecord


NAME = "generic"
DEFAULT_AUDIO_OUTPUT_TEMPLATE = "%(title).40s-audio.%(ext)s"
DEFAULT_SUBTITLE_OUTPUT_TEMPLATE = "%(title).40s.%(ext)s"


def downloaded_files(media_dir: Path) -> list[Path]:
    ignored_suffixes = {".part", ".ytdl"}
    files = [path for path in media_dir.iterdir() if path.is_file() and path.suffix not in ignored_suffixes]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def subtitle_files(media_dir: Path) -> list[Path]:
    suffixes = {".vtt", ".srt", ".ttml", ".srv1", ".srv2", ".srv3", ".json3"}
    files = [path for path in media_dir.iterdir() if path.is_file() and path.suffix.lower() in suffixes]
    return sorted(files, key=lambda p: p.name)


def _playlist_items(run: RunRecord) -> str | None:
    try:
        return normalize_playlist_items(getattr(run.args, "playlist_items", None))
    except ValueError as exc:
        run.fail("invalid_playlist_items", str(exc))
        return None


def build_base_command(run: RunRecord, extra_options: list[str] | None = None) -> list[str] | None:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        run.fail("missing_dependency", "系统未安装 yt-dlp。请先安装，例如：pipx install yt-dlp 或 brew install yt-dlp。")
        return None

    playlist_items = _playlist_items(run)
    if getattr(run.args, "playlist_items", None) and playlist_items is None:
        return None
    cookies_browser = run.args.cookies_browser or run.config.get("cookies_browser") or "chrome"
    proxy = run.args.proxy or run.config.get("proxy") or ""
    format_selector = run.args.format or run.config.get("format") or DEFAULT_FORMAT
    default_template = DEFAULT_PLAYLIST_OUTPUT_TEMPLATE if playlist_items else DEFAULT_OUTPUT_TEMPLATE
    output_template = str(run.media_dir / (run.args.output_template or default_template))

    cmd = [
        yt_dlp,
        "--continue",
        "--restrict-filenames",
        "--retries",
        "10",
        "--fragment-retries",
        "10",
        "--merge-output-format",
        "mp4",
    ]
    if playlist_items:
        if playlist_items != "all":
            cmd.extend(["--playlist-items", playlist_items])
    else:
        cmd.append("--no-playlist")
    if extra_options:
        cmd.extend(extra_options)
    cmd.extend(["-f", format_selector, "-o", output_template])
    if proxy:
        cmd.extend(["--proxy", proxy])

    run.outputs.update(
        {
            "cookies_browser": cookies_browser,
            "proxy": proxy,
            "format": format_selector,
            "output_template": output_template,
            "playlist_items": playlist_items or "",
        }
    )
    return cmd


def build_audio_command(run: RunRecord, extra_options: list[str] | None = None) -> list[str] | None:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        run.fail("missing_dependency", "系统未安装 yt-dlp。请先安装，例如：pipx install yt-dlp 或 brew install yt-dlp。")
        return None

    playlist_items = _playlist_items(run)
    if getattr(run.args, "playlist_items", None) and playlist_items is None:
        return None
    cookies_browser = run.args.cookies_browser or run.config.get("cookies_browser") or "chrome"
    proxy = run.args.proxy or run.config.get("proxy") or ""
    output_template = str(run.media_dir / (run.args.output_template or DEFAULT_AUDIO_OUTPUT_TEMPLATE))

    cmd = [
        yt_dlp,
        "--continue",
        "--restrict-filenames",
        "--retries",
        "10",
        "--fragment-retries",
        "10",
        "-x",
        "--audio-format",
        "mp3",
        "-o",
        output_template,
    ]
    if playlist_items:
        if playlist_items != "all":
            cmd.extend(["--playlist-items", playlist_items])
    else:
        cmd.append("--no-playlist")
    if extra_options:
        cmd.extend(extra_options)
    if proxy:
        cmd.extend(["--proxy", proxy])

    run.outputs.update(
        {
            "cookies_browser": cookies_browser,
            "proxy": proxy,
            "audio_format": "mp3",
            "output_template": output_template,
            "playlist_items": playlist_items or "",
        }
    )
    return cmd


def build_subtitle_command(run: RunRecord, extra_options: list[str] | None = None) -> list[str] | None:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        run.fail("missing_dependency", "系统未安装 yt-dlp。请先安装，例如：pipx install yt-dlp 或 brew install yt-dlp。")
        return None

    playlist_items = _playlist_items(run)
    if getattr(run.args, "playlist_items", None) and playlist_items is None:
        return None
    cookies_browser = run.args.cookies_browser or run.config.get("cookies_browser") or "chrome"
    proxy = run.args.proxy or run.config.get("proxy") or ""
    sub_langs = getattr(run.args, "sub_langs", None) or run.config.get("sub_langs") or "zh-Hans,zh-CN,en,ja"
    output_template = str(run.media_dir / (run.args.output_template or DEFAULT_SUBTITLE_OUTPUT_TEMPLATE))

    cmd = [
        yt_dlp,
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs",
        sub_langs,
        "--restrict-filenames",
        "--retries",
        "10",
        "--fragment-retries",
        "10",
        "-o",
        output_template,
    ]
    if playlist_items:
        if playlist_items != "all":
            cmd.extend(["--playlist-items", playlist_items])
    else:
        cmd.append("--no-playlist")
    if extra_options:
        cmd.extend(extra_options)
    if proxy:
        cmd.extend(["--proxy", proxy])

    output_data = {
        "cookies_browser": cookies_browser,
        "proxy": proxy,
        "sub_langs": sub_langs,
        "subtitle_output_template": output_template,
        "playlist_items": playlist_items or "",
    }
    if getattr(run.args, "mode", "video") == "subtitles":
        output_data["output_template"] = output_template
    run.outputs.update(output_data)
    return cmd


def build_list_command(run: RunRecord, extra_options: list[str] | None = None) -> list[str] | None:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        run.fail("missing_dependency", "系统未安装 yt-dlp。请先安装，例如：pipx install yt-dlp 或 brew install yt-dlp。")
        return None

    playlist_items = _playlist_items(run)
    if getattr(run.args, "playlist_items", None) and playlist_items is None:
        return None
    cookies_browser = run.args.cookies_browser or run.config.get("cookies_browser") or "chrome"
    proxy = run.args.proxy or run.config.get("proxy") or ""
    cmd = [yt_dlp, "--dump-single-json", "--flat-playlist"]
    if playlist_items and playlist_items != "all":
        cmd.extend(["--playlist-items", playlist_items])
    elif not playlist_items:
        cmd.append("--no-playlist")
    if extra_options:
        cmd.extend(extra_options)
    if proxy:
        cmd.extend(["--proxy", proxy])
    run.outputs.update(
        {
            "cookies_browser": cookies_browser,
            "proxy": proxy,
            "playlist_items": playlist_items or "",
            "list_only": True,
        }
    )
    return cmd


def build_attempts(run: RunRecord, base_cmd: list[str], prefix: str = NAME) -> list[tuple[str, list[str]]]:
    cookies_browser = run.outputs["cookies_browser"]
    if run.args.force_cookies:
        return [(f"{prefix}_cookies", base_cmd + ["--cookies-from-browser", cookies_browser, run.args.input])]

    attempts = [(f"{prefix}_no_cookies", base_cmd + [run.args.input])]
    if not run.args.no_cookies_fallback:
        attempts.append((f"{prefix}_cookies", base_cmd + ["--cookies-from-browser", cookies_browser, run.args.input]))
    return attempts


def run_attempts(run: RunRecord, attempts: list[tuple[str, list[str]]]) -> subprocess.CompletedProcess | None:
    proc = None
    for label, cmd in attempts:
        run.outputs["attempts"].append({"label": label, "command": " ".join(cmd)})
        run.log(f"attempt {label}: {' '.join(cmd)}")
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        run.outputs["attempts"][-1]["returncode"] = proc.returncode
        run.log(f"yt-dlp output start ({label})")
        with run.log_path.open("a", encoding="utf-8") as f:
            f.write(proc.stdout or "")
            if proc.stdout and not proc.stdout.endswith("\n"):
                f.write("\n")
        run.log(f"yt-dlp output end ({label})")
        if proc.returncode == 0:
            break
    run.outputs["retry_count"] = max(0, len(run.outputs["attempts"]) - 1)
    return proc


def finish_download(run: RunRecord, proc: subprocess.CompletedProcess | None) -> int:
    if proc is None or proc.returncode != 0:
        code = proc.returncode if proc else "no-attempt"
        return run.fail("download_failed", f"yt-dlp 退出码为 {code}")

    files = downloaded_files(run.media_dir)
    if not files:
        return run.fail("download_output_missing", "yt-dlp 已完成，但没有在 media 目录找到媒体文件。")

    media_path = files[0]
    run.outputs["output_file_path"] = str(media_path)
    run.outputs["file_size_bytes"] = media_path.stat().st_size
    probe_media(run, media_path)
    if getattr(run.args, "mode", "video") == "video":
        try_subtitle_download_after_video(run)
    run.log(f"url ingest success: {media_path}")
    run.write_manifest("success")
    print(f"success: 已下载媒体 {media_path}")
    print(f"manifest: {run.manifest_path}")
    return 0


def try_subtitle_download_after_video(run: RunRecord) -> None:
    run.outputs["subtitle_attempted_after_video"] = True
    base_cmd = build_subtitle_command(run)
    if base_cmd is None:
        run.warnings.append(
            {
                "code": "subtitle_auto_attempt_skipped",
                "message": "视频已下载，但自动字幕下载命令无法构建。详见 run.log。",
            }
        )
        run.log("WARNING subtitle_auto_attempt_skipped: subtitle command could not be built")
        return

    adapter = run.outputs.get("site_adapter") or NAME
    video_retry_count = run.outputs.get("retry_count", 0)
    attempt_count_before = len(run.outputs["attempts"])
    proc = run_attempts(run, build_attempts(run, base_cmd, prefix=f"{adapter}_subtitles"))
    subtitle_attempt_count = len(run.outputs["attempts"]) - attempt_count_before
    run.outputs["video_retry_count"] = video_retry_count
    run.outputs["retry_count"] = video_retry_count
    run.outputs["subtitle_retry_count"] = max(0, subtitle_attempt_count - 1)
    run.outputs["subtitle_attempt_returncode"] = proc.returncode if proc else "no-attempt"

    if proc is None or proc.returncode != 0:
        code = proc.returncode if proc else "no-attempt"
        run.warnings.append(
            {
                "code": "subtitle_auto_download_failed",
                "message": f"视频已下载，但自动字幕下载失败，yt-dlp 退出码为 {code}。",
            }
        )
        run.log(f"WARNING subtitle_auto_download_failed: yt-dlp exit code {code}")
        return

    files = subtitle_files(run.media_dir)
    run.outputs["subtitle_files"] = [str(path) for path in files]
    if not files:
        run.warnings.append(
            {
                "code": "subtitle_files_missing_after_video",
                "message": "视频已下载，自动字幕下载命令已完成，但未生成字幕文件。",
            }
        )
        run.log("WARNING subtitle_files_missing_after_video: no subtitle files found")
        return

    run.log(f"subtitle auto ingest success after video: {len(files)} file(s)")


def finish_subtitles(run: RunRecord, proc: subprocess.CompletedProcess | None) -> int:
    if proc is None or proc.returncode != 0:
        code = proc.returncode if proc else "no-attempt"
        return run.fail("subtitle_download_failed", f"yt-dlp 字幕下载退出码为 {code}")

    files = subtitle_files(run.media_dir)
    run.outputs["subtitle_files"] = [str(path) for path in files]
    if not files:
        return run.fail("subtitle_files_missing", "yt-dlp 已完成，但没有在 media 目录找到字幕文件。")

    run.log(f"subtitle ingest success: {len(files)} file(s)")
    run.write_manifest("success")
    print(f"success: 已下载字幕 {len(files)} 个文件")
    print(f"manifest: {run.manifest_path}")
    return 0


def finish_list(run: RunRecord, proc: subprocess.CompletedProcess | None) -> int:
    if proc is None or proc.returncode != 0:
        code = proc.returncode if proc else "no-attempt"
        return run.fail("list_failed", f"yt-dlp list 退出码为 {code}")
    run.log("list success")
    run.write_manifest("success")
    print(f"success: 已列出资源信息，详见 log {run.log_path}")
    print(f"manifest: {run.manifest_path}")
    return 0


def download(run: RunRecord, extra_options: list[str] | None = None, prefix: str = NAME) -> int:
    mode = getattr(run.args, "mode", "video")
    if getattr(run.args, "list", False) or mode == "metadata":
        base_cmd = build_list_command(run, extra_options=extra_options)
        if base_cmd is None:
            return 1
        if mode == "metadata":
            run.outputs["metadata_only"] = True
        proc = run_attempts(run, build_attempts(run, base_cmd, prefix=prefix))
        return finish_list(run, proc)

    if mode == "audio":
        base_cmd = build_audio_command(run, extra_options=extra_options)
        if base_cmd is None:
            return 1
        proc = run_attempts(run, build_attempts(run, base_cmd, prefix=prefix))
        return finish_download(run, proc)

    if mode == "subtitles":
        base_cmd = build_subtitle_command(run, extra_options=extra_options)
        if base_cmd is None:
            return 1
        proc = run_attempts(run, build_attempts(run, base_cmd, prefix=prefix))
        return finish_subtitles(run, proc)

    base_cmd = build_base_command(run, extra_options=extra_options)
    if base_cmd is None:
        return 1
    proc = run_attempts(run, build_attempts(run, base_cmd, prefix=prefix))
    return finish_download(run, proc)
