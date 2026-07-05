from __future__ import annotations

import argparse
import json
import sys

from common import is_url, load_config, make_job_id, now_iso, resolve_output_root


class RunRecord:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.config = load_config()
        self.job_id = make_job_id()
        self.created_at = now_iso()
        self.output_root = resolve_output_root(args, self.config)
        self.run_dir = self.output_root / self.job_id
        self.media_dir = self.run_dir / "media"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.run_dir / "run.log"
        self.manifest_path = self.run_dir / "manifest.json"
        self.errors: list[dict] = []
        self.warnings: list[dict] = []
        self.outputs: dict = {
            "mode": getattr(args, "mode", "video"),
            "run_dir": str(self.run_dir),
            "media_dir": str(self.media_dir),
            "manifest_path": str(self.manifest_path),
            "log_path": str(self.log_path),
            "attempts": [],
        }

    def log(self, message: str) -> None:
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(f"[{now_iso()}] {message}\n")

    def manifest(self, status: str) -> dict:
        return {
            "job_id": self.job_id,
            "skill": "vlp-video-download",
            "status": status,
            "input": {
                "type": "url" if is_url(self.args.input) else "local",
                "value": self.args.input,
                "mode": getattr(self.args, "mode", "video"),
            },
            "outputs": self.outputs,
            "errors": self.errors,
            "warnings": self.warnings,
            "created_at": self.created_at,
            "completed_at": now_iso(),
        }

    def write_manifest(self, status: str) -> None:
        data = self.manifest(status)
        self.manifest_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def fail(self, code: str, message: str) -> int:
        self.errors.append({"code": code, "message": message})
        self.log(f"ERROR {code}: {message}")
        self.write_manifest("failed")
        print(f"failed: {message}", file=sys.stderr)
        print(f"manifest: {self.manifest_path}", file=sys.stderr)
        print(f"log: {self.log_path}", file=sys.stderr)
        return 1
