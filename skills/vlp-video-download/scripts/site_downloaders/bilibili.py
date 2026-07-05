from __future__ import annotations

from run_record import RunRecord

from . import generic


NAME = "bilibili"


def download(run: RunRecord) -> int:
    return generic.download(run, prefix=NAME)
