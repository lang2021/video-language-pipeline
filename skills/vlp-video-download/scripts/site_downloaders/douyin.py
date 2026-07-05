from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from common import SKILL_DIR
from media_probe import probe_media
from run_record import RunRecord


NAME = "douyin"
PROFILE_DIR = SKILL_DIR / "data" / "browser_state" / "douyin_profile"
REFERER = "https://www.douyin.com/"


def clean_filename(value: str) -> str:
    clean = re.sub(r"[^\w\u4e00-\u9fff]", "", value)[:15]
    return clean or "douyin_video"


def resolution_name(width: int, height: int) -> str:
    if width >= 3840:
        return "4K"
    if width >= 2560:
        return "2K"
    if width >= 1920:
        return "1080p"
    if width >= 1280:
        return "720p"
    if width >= 1024:
        return "540p"
    return "标清"


def standardize_url(url: str) -> str:
    parsed = urlparse(url)
    modal_id = parse_qs(parsed.query).get("modal_id", [None])[0]
    if modal_id:
        return f"https://www.douyin.com/video/{modal_id}"
    match = re.search(r"/video/(\d+)", url)
    if match:
        return f"https://www.douyin.com/video/{match.group(1)}"
    return url


def parse_video_info(data: dict) -> dict:
    detail = data.get("aweme_detail") or {}
    title = str(detail.get("desc") or "douyin_video")[:50]
    formats = []
    audio_url = None

    for candidate in detail.get("video", {}).get("bit_rate_audio", []):
        url_info = candidate.get("audio_meta", {}).get("url_list") or candidate.get("play_addr", {}).get("url_list") or []
        if not url_info:
            continue
        raw_url = url_info[0]
        audio_url = raw_url.get("main_url") if isinstance(raw_url, dict) else str(raw_url)
        if audio_url:
            break

    music = detail.get("music") or {}
    if not audio_url:
        for key in ("play_url", "play_url_song", "strong_beat_url"):
            url_info = (music.get(key) or {}).get("url_list") or []
            if not url_info:
                continue
            raw_url = url_info[0]
            audio_url = raw_url.get("main_url") if isinstance(raw_url, dict) else str(raw_url)
            if audio_url:
                break

    for item in detail.get("video", {}).get("bit_rate", []):
        play_addr = item.get("play_addr") or {}
        width = int(play_addr.get("width") or 0)
        height = int(play_addr.get("height") or 0)
        urls = play_addr.get("url_list") or []
        if not width or not height or not urls:
            continue
        raw_url = urls[0]
        video_url = raw_url.get("main_url") if isinstance(raw_url, dict) else str(raw_url)
        if not video_url:
            continue
        formats.append(
            {
                "width": width,
                "height": height,
                "resolution": f"{width}x{height}",
                "resolution_name": resolution_name(width, height),
                "size_mb": (item.get("data_size") or 0) / 1024 / 1024,
                "url": video_url,
            }
        )
    formats.sort(key=lambda item: item["width"] * item["height"], reverse=True)
    return {"title": title, "formats": formats, "audio_url": audio_url}


def select_format(formats: list[dict], resolution: str | None) -> dict | None:
    if not formats:
        return None
    if not resolution:
        return formats[0]
    wanted = resolution.lower()
    for item in formats:
        if wanted in item["resolution"].lower() or wanted in item["resolution_name"].lower():
            return item
    return None


def capture_aweme_detail(run: RunRecord) -> dict | None:
    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        run.fail("missing_dependency", "系统未安装 patchright。请先安装：pip install patchright。")
        return None

    if not PROFILE_DIR.exists():
        run.fail("douyin_login_required", f"未检测到 Douyin 登录状态，请先运行 scripts/douyin_login.py。profile: {PROFILE_DIR}")
        return None

    std_url = standardize_url(run.args.input)
    tmp_dir = run.run_dir / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    run.outputs.update(
        {
            "standardized_url": std_url,
            "douyin_profile_path": str(PROFILE_DIR),
            "aweme_detail_captured": False,
        }
    )

    browser_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                channel="chrome",
                no_viewport=True,
                ignore_default_args=["--enable-automation"],
                user_agent=user_agent,
                args=browser_args,
            )
            page = context.pages[0] if context.pages else context.new_page()
            try:
                page.goto(std_url, wait_until="domcontentloaded", timeout=60000)

                def is_detail(response) -> bool:
                    return "aweme/v1/web/aweme/detail" in response.url

                response = None
                try:
                    response = page.wait_for_event("response", is_detail, timeout=60000)
                except Exception:
                    run.log("Douyin detail first wait failed; retry after reload")
                    page.reload(wait_until="domcontentloaded", timeout=60000)
                    response = page.wait_for_event("response", is_detail, timeout=30000)

                data = response.json()
                detail_path = tmp_dir / "aweme_detail.json"
                detail_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                run.outputs["aweme_detail_captured"] = True
                run.outputs["aweme_detail_path"] = str(detail_path)
                return data
            finally:
                context.close()
    except Exception as exc:
        run.fail("douyin_capture_failed", f"Douyin aweme detail 抓取失败：{exc}")
        return None


def download_with_ytdlp(run: RunRecord, url: str, output_file: Path) -> subprocess.CompletedProcess | None:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        run.fail("missing_dependency", "系统未安装 yt-dlp。请先安装，例如：pipx install yt-dlp 或 brew install yt-dlp。")
        return None
    cmd = [yt_dlp, "--add-header", f"Referer:{REFERER}", "--no-warnings", "-o", str(output_file), url]
    run.outputs["attempts"].append({"label": "douyin_direct_url", "command": " ".join(cmd)})
    run.log(f"attempt douyin_direct_url: {' '.join(cmd)}")
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    run.outputs["attempts"][-1]["returncode"] = proc.returncode
    with run.log_path.open("a", encoding="utf-8") as f:
        f.write(proc.stdout or "")
        if proc.stdout and not proc.stdout.endswith("\n"):
            f.write("\n")
    return proc


def download_audio_with_ytdlp(run: RunRecord, url: str, output_template: Path) -> subprocess.CompletedProcess | None:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        run.fail("missing_dependency", "系统未安装 yt-dlp。请先安装，例如：pipx install yt-dlp 或 brew install yt-dlp。")
        return None
    cmd = [
        yt_dlp,
        "--add-header",
        f"Referer:{REFERER}",
        "--no-warnings",
        "-x",
        "--audio-format",
        "mp3",
        "-o",
        str(output_template),
        url,
    ]
    run.outputs["attempts"].append({"label": "douyin_audio_url", "command": " ".join(cmd)})
    run.log(f"attempt douyin_audio_url: {' '.join(cmd)}")
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    run.outputs["attempts"][-1]["returncode"] = proc.returncode
    with run.log_path.open("a", encoding="utf-8") as f:
        f.write(proc.stdout or "")
        if proc.stdout and not proc.stdout.endswith("\n"):
            f.write("\n")
    return proc


def newest_media_file(media_dir: Path) -> Path | None:
    ignored_suffixes = {".part", ".ytdl"}
    files = [path for path in media_dir.iterdir() if path.is_file() and path.suffix not in ignored_suffixes]
    if not files:
        return None
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def finish_list(run: RunRecord, info: dict) -> int:
    run.outputs["list_only"] = True
    run.outputs["douyin_title"] = info["title"]
    run.outputs["douyin_formats"] = [{k: v for k, v in item.items() if k != "url"} for item in info["formats"]]
    run.outputs["douyin_audio_available"] = bool(info.get("audio_url"))
    run.write_manifest("success")
    print(f"success: 已列出 Douyin 资源，详见 manifest {run.manifest_path}")
    return 0


def download(run: RunRecord) -> int:
    mode = getattr(run.args, "mode", "video")
    if mode == "subtitles":
        return run.fail("unsupported_mode", "Douyin adapter 暂不支持字幕下载；请使用 YouTube/Bilibili/generic 字幕下载路径。")

    data = capture_aweme_detail(run)
    if data is None:
        return 1

    info = parse_video_info(data)
    if getattr(run.args, "list", False) or mode == "metadata":
        if mode == "metadata":
            run.outputs["metadata_only"] = True
        return finish_list(run, info)

    if mode == "audio":
        run.outputs["douyin_title"] = info["title"]
        run.outputs["douyin_audio_available"] = bool(info.get("audio_url"))
        audio_url = info.get("audio_url")
        if not audio_url:
            return run.fail("douyin_audio_missing", "Douyin aweme detail 中没有可下载的 audio_url。")

        output_template = run.media_dir / f"{clean_filename(info['title'])}-audio.%(ext)s"
        proc = download_audio_with_ytdlp(run, audio_url, output_template)
        if proc is None or proc.returncode != 0:
            code = proc.returncode if proc else "no-attempt"
            return run.fail("douyin_audio_download_failed", f"Douyin 音频下载失败，yt-dlp 退出码为 {code}")

        media_path = newest_media_file(run.media_dir)
        if media_path is None:
            return run.fail("download_output_missing", "Douyin 音频下载完成，但未找到输出文件。")

        run.outputs["audio_format"] = "mp3"
        run.outputs["output_file_path"] = str(media_path)
        run.outputs["file_size_bytes"] = media_path.stat().st_size
        probe_media(run, media_path)
        run.write_manifest("success")
        print(f"success: 已下载 Douyin 音频 {media_path}")
        print(f"manifest: {run.manifest_path}")
        return 0

    selected = select_format(info["formats"], getattr(run.args, "resolution", None))
    if selected is None:
        available = [item["resolution"] for item in info["formats"]]
        return run.fail("douyin_resolution_missing", f"未找到指定分辨率。可用分辨率：{available}")

    filename = f"{clean_filename(info['title'])}-{selected['resolution']}.mp4"
    output_file = run.media_dir / filename
    run.outputs["douyin_title"] = info["title"]
    run.outputs["douyin_formats"] = [{k: v for k, v in item.items() if k != "url"} for item in info["formats"]]
    run.outputs["selected_resolution"] = selected["resolution"]

    proc = download_with_ytdlp(run, selected["url"], output_file)
    if proc is None or proc.returncode != 0:
        code = proc.returncode if proc else "no-attempt"
        return run.fail("douyin_download_failed", f"Douyin 直链下载失败，yt-dlp 退出码为 {code}")
    if not output_file.exists():
        return run.fail("download_output_missing", f"Douyin 下载完成，但未找到输出文件：{output_file}")

    run.outputs["output_file_path"] = str(output_file)
    run.outputs["file_size_bytes"] = output_file.stat().st_size
    probe_media(run, output_file)
    run.write_manifest("success")
    print(f"success: 已下载 Douyin 视频 {output_file}")
    print(f"manifest: {run.manifest_path}")
    return 0
