from __future__ import annotations

from run_record import RunRecord

from . import generic


NAME = "youtube"


def download(run: RunRecord) -> int:
    return generic.download(run, extra_options=["--concurrent-fragments", "1"], prefix=NAME)
