from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4


SKILL_DIR = Path(__file__).resolve().parents[1]
SUITE_DIR = Path(__file__).resolve().parents[3]
DEFAULT_FORMAT = (
    "bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/"
    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
)
DEFAULT_OUTPUT_TEMPLATE = "%(title).40s-best.%(ext)s"
DEFAULT_PLAYLIST_OUTPUT_TEMPLATE = "%(title).40s-%(playlist_index)s.%(ext)s"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def make_job_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{uuid4().hex[:8]}"


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def load_config() -> dict:
    config_path = SUITE_DIR / "config.json"
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_playlist_items(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if value == "all":
        return value
    allowed = set("0123456789,:")
    if value and all(ch in allowed for ch in value):
        return value
    raise ValueError("--playlist-items 只支持 all、1:5 或 1,3,5 这类格式")


def resolve_output_root(args: argparse.Namespace, config: dict) -> Path:
    value = args.output_dir or config.get("output_dir") or str(SUITE_DIR / "runs")
    root = Path(value).expanduser()
    if not root.is_absolute():
        root = (Path.cwd() / root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root
