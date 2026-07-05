from __future__ import annotations

from run_record import RunRecord
from site_downloaders import choose_downloader


def ingest_url(run: RunRecord) -> int:
    downloader = choose_downloader(run.args.input)
    run.outputs["site_adapter"] = downloader.NAME
    run.log(f"url ingest start: {run.args.input}")
    run.log(f"site adapter: {downloader.NAME}")
    return downloader.download(run)
