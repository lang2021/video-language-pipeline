from __future__ import annotations

from urllib.parse import urlparse

from . import bilibili, douyin, generic, youtube


def choose_downloader(url: str):
    host = urlparse(url).netloc.lower()
    if host.endswith("douyin.com") or host in {"v.douyin.com", "www.iesdouyin.com"}:
        return douyin
    if host.endswith("bilibili.com") or host == "b23.tv":
        return bilibili
    if host in {"youtu.be", "www.youtu.be"} or host.endswith("youtube.com"):
        return youtube
    return generic
