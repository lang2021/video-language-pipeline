#!/usr/bin/env python3
"""vlp-video-download 的 CLI 入口。"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from common import is_url
from local_ingest import ingest_local
from run_record import RunRecord
from site_downloaders import choose_downloader
from url_download import ingest_url


def run_ingest(args: argparse.Namespace) -> int:
    run = RunRecord(args)
    run.log("run created")
    run.log(f"run_dir: {run.run_dir}")
    run.log(f"input: {args.input}")
    if is_url(args.input):
        return ingest_url(run)
    return ingest_local(run)


def self_check() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        sample = root / "sample.mp4"
        sample.write_bytes(b"not a real video; local ingest only checks file presence\n")

        ok_args = argparse.Namespace(
            input=str(sample),
            output_dir=str(root / "runs"),
            mode="video",
            sub_langs="zh-Hans,zh-CN,en,ja",
            cookies_browser="",
            proxy="",
            format=None,
            output_template=None,
            force_cookies=False,
            no_cookies_fallback=False,
            playlist_items=None,
            list=False,
            resolution=None,
        )
        if run_ingest(ok_args) != 0:
            return 1

        bad_args = argparse.Namespace(
            input=str(root / "missing.mp4"),
            output_dir=str(root / "runs"),
            mode="video",
            sub_langs="zh-Hans,zh-CN,en,ja",
            cookies_browser="",
            proxy="",
            format=None,
            output_template=None,
            force_cookies=False,
            no_cookies_fallback=False,
            playlist_items=None,
            list=False,
            resolution=None,
        )
        if run_ingest(bad_args) == 0:
            return 1

        metadata_args = argparse.Namespace(
            input=str(sample),
            output_dir=str(root / "runs"),
            mode="metadata",
            sub_langs="zh-Hans,zh-CN,en,ja",
            cookies_browser="",
            proxy="",
            format=None,
            output_template=None,
            force_cookies=False,
            no_cookies_fallback=False,
            playlist_items=None,
            list=False,
            resolution=None,
        )
        if run_ingest(metadata_args) != 0:
            return 1

        manifests = list((root / "runs").glob("*/manifest.json"))
        logs = list((root / "runs").glob("*/run.log"))
        assert len(manifests) == 3
        assert len(logs) == 3
        data = [json.loads(p.read_text(encoding="utf-8")) for p in manifests]
        assert {d["status"] for d in data} == {"success", "failed"}
        success_manifest = next(d for d in data if d["status"] == "success" and d["outputs"]["mode"] == "video")
        warning_codes = {
            w.get("code")
            for w in success_manifest.get("warnings", [])
            if isinstance(w, dict)
        }
        assert "media_probe" in success_manifest["outputs"] or any(
            code in warning_codes for code in {"ffprobe_missing", "ffprobe_failed", "ffprobe_parse_failed"}
        )
        assert choose_downloader("https://youtu.be/example").NAME == "youtube"
        assert choose_downloader("https://www.bilibili.com/video/BV1xx411c7mD").NAME == "bilibili"
        assert choose_downloader("https://b23.tv/example").NAME == "bilibili"
        assert choose_downloader("https://www.douyin.com/video/123").NAME == "douyin"
        assert choose_downloader("https://example.com/video").NAME == "generic"
    print("self-check ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="vlp-video-download 的 media ingest CLI。")
    parser.add_argument("input", nargs="?", help="视频 URL 或本地媒体文件路径。")
    parser.add_argument("--mode", choices=["video", "audio", "subtitles", "metadata"], default="video", help="URL 下载模式：video、audio、subtitles 或 metadata。")
    parser.add_argument("--sub-langs", default="zh-Hans,zh-CN,en,ja", help="字幕下载语言列表，传给 yt-dlp --sub-langs。")
    parser.add_argument("--output-dir", help="每次运行输出目录的根目录。")
    parser.add_argument("--cookies-browser", help='可选 yt-dlp cookies 来源，例如 "chrome:Default"。')
    parser.add_argument("--proxy", help="传给 yt-dlp 的可选 proxy。")
    parser.add_argument("--format", help="可选 yt-dlp format selector。")
    parser.add_argument("--output-template", help="run media 目录内的可选 yt-dlp output template。")
    parser.add_argument("--playlist-items", help="YouTube/Bilibili playlist 范围：all、1:5 或 1,3,5。")
    parser.add_argument("--list", action="store_true", help="列出资源信息，不下载媒体文件。")
    parser.add_argument("--resolution", help="Douyin 视频分辨率，例如 1080p。")
    parser.add_argument("--force-cookies", action="store_true", help="跳过无 cookies 的首次尝试。")
    parser.add_argument("--no-cookies-fallback", action="store_true", help="失败后不使用 browser cookies retry。")
    parser.add_argument("--self-check", action="store_true", help="运行不需要网络的本地自检。")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    if not args.input:
        parser.error("除非使用 --self-check，否则必须提供 input")
    return run_ingest(args)


if __name__ == "__main__":
    raise SystemExit(main())
