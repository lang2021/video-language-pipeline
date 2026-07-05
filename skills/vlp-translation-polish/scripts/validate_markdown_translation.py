#!/usr/bin/env python3
"""Validate mechanical Markdown preservation after agent translation."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


INLINE_LINK_RE = re.compile(r"(!?\[[^\]\n]*\]\()([^)\s]+)(\))")
AUTOLINK_RE = re.compile(r"<(https?://[^>\s]+)>")
HEADING_RE = re.compile(r"^(#{1,6})\s+")
FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
FENCE_RE = re.compile(r"^[ \t]*(```|~~~)")


def strip_code(text: str) -> str:
    output: list[str] = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            output.append("\n")
            continue
        output.append("\n" if in_fence else line)
    return "".join(output)


def markdown_urls(text: str) -> list[str]:
    text = strip_code(text)
    matches: list[tuple[int, str]] = []
    matches.extend((match.start(), match.group(2)) for match in INLINE_LINK_RE.finditer(text))
    matches.extend((match.start(), match.group(1)) for match in AUTOLINK_RE.finditer(text))
    return [url for _start, url in sorted(matches)]


def front_matter_keys(text: str) -> list[str]:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return []
    keys: list[str] = []
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith((" ", "\t", "-")) and ":" in line:
            keys.append(line.split(":", 1)[0].strip())
    return keys


def heading_levels(text: str) -> list[int]:
    text = strip_code(text)
    return [len(match.group(1)) for line in text.splitlines() if (match := HEADING_RE.match(line))]


def fence_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if FENCE_RE.match(line))


def compare_list(name: str, source: list[str] | list[int], target: list[str] | list[int]) -> str | None:
    if len(source) != len(target):
        return f"{name} count mismatch: source={len(source)} target={len(target)}"
    for index, (left, right) in enumerate(zip(source, target), start=1):
        if left != right:
            return f"{name} mismatch at {index}: source={left!r} target={right!r}"
    return None


def validate(source_text: str, target_text: str) -> list[str]:
    errors: list[str] = []
    checks = [
        ("url", markdown_urls(source_text), markdown_urls(target_text)),
        ("front matter key", front_matter_keys(source_text), front_matter_keys(target_text)),
        ("heading level", heading_levels(source_text), heading_levels(target_text)),
    ]
    for name, source, target in checks:
        if error := compare_list(name, source, target):
            errors.append(error)

    source_fences = fence_count(source_text)
    target_fences = fence_count(target_text)
    if source_fences != target_fences:
        errors.append(f"fenced code block count mismatch: source={source_fences} target={target_fences}")
    return errors


def run_check(source_path: Path, target_path: Path) -> int:
    errors = validate(source_path.read_text(encoding="utf-8"), target_path.read_text(encoding="utf-8"))
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("ok")
    return 0


def self_check() -> int:
    source = """---
title: Original
date: 2026-07-05
---
# Title

![](https://substackcdn.com/image/fetch/$s_!VRfz!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F6c0f0fe7-5001-469c-aa90-45af51e325b6_1240x1032.png)

[site](https://example.com/path?q=1#frag)
<https://example.org/raw>

```bash
echo "not a [link](https://ignored.example)"
```
"""
    translated_ok = source.replace("Original", "译文").replace("# Title", "# 标题")
    bad_url = translated_ok.replace("6c0f0fe7", "0c0f0fe7")
    bad_heading = translated_ok.replace("# 标题", "## 标题")
    bad_fence = translated_ok.replace("```bash", "")
    front_matter_ok = translated_ok.replace("2026-07-05", "2026年7月5日")

    assert not validate(source, translated_ok)
    assert not validate(source, front_matter_ok)
    assert any("url mismatch" in error for error in validate(source, bad_url))
    assert any("heading level mismatch" in error for error in validate(source, bad_heading))
    assert any("fenced code block count mismatch" in error for error in validate(source, bad_fence))

    print("self-check ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Markdown translation structure and URLs.")
    parser.add_argument("source", nargs="?", help="Source Markdown file.")
    parser.add_argument("translated", nargs="?", help="Translated Markdown file.")
    parser.add_argument("--self-check", action="store_true", help="Run built-in validation checks.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    if not args.source or not args.translated:
        parser.error("source and translated are required unless --self-check is used")
    return run_check(Path(args.source), Path(args.translated))


if __name__ == "__main__":
    raise SystemExit(main())
