from __future__ import annotations

from pathlib import Path

from media_probe import probe_media
from run_record import RunRecord


def ingest_local(run: RunRecord) -> int:
    path = Path(run.args.input).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()

    run.log(f"local ingest start: {path}")
    if not path.exists():
        return run.fail("local_file_not_found", f"本地文件不存在：{path}")
    if not path.is_file():
        return run.fail("local_path_not_file", f"本地路径不是文件：{path}")

    run.outputs["source_path"] = str(path)
    run.outputs["output_file_path"] = str(path)
    run.outputs["file_size_bytes"] = path.stat().st_size
    probe_media(run, path)
    run.log("local ingest success")
    run.write_manifest("success")
    print(f"success: 已登记本地媒体 {path}")
    print(f"manifest: {run.manifest_path}")
    return 0
