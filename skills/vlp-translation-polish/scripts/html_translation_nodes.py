#!/usr/bin/env python3
"""Extract and merge translatable text from a finalized static HTML mirror."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

from validate_html_translation import (
    PROTECTED_TEXT_TAGS,
    VOID_TAGS,
    is_translatable_attribute,
    print_semantic_summary,
    rewrite_local_resources,
    semantic_lint,
    validate,
    write_semantic_report,
)


SCHEMA_VERSION = 1
BUNDLE_KEYS = {"schema_version", "source_name", "source_sha256", "target_lang", "units"}
UNIT_KEYS = {"id", "kind", "context", "source", "target"}


@dataclass(frozen=True)
class RawSpan:
    kind: str
    context: str
    source: str
    start: int
    end: int
    prefix: str = ""
    suffix: str = ""
    quote: str | None = None


@dataclass(frozen=True)
class UnitSpan:
    id: str
    kind: str
    context: str
    source: str
    start: int
    end: int
    prefix: str
    suffix: str
    quote: str | None


@dataclass(frozen=True)
class AttributeToken:
    name: str
    value: str | None
    value_start: int | None
    value_end: int | None
    quote: str | None


def split_outer_whitespace(value: str) -> tuple[str, str, str]:
    left = 0
    while left < len(value) and value[left].isspace():
        left += 1
    right = len(value)
    while right > left and value[right - 1].isspace():
        right -= 1
    return value[:left], value[left:right], value[right:]


def scan_attributes(raw_tag: str) -> list[AttributeToken]:
    position = 1
    while position < len(raw_tag) and raw_tag[position].isspace():
        position += 1
    while position < len(raw_tag) and not raw_tag[position].isspace() and raw_tag[position] not in "/>":
        position += 1

    tokens: list[AttributeToken] = []
    while position < len(raw_tag):
        while position < len(raw_tag) and raw_tag[position].isspace():
            position += 1
        if position >= len(raw_tag) or raw_tag[position] in "/>":
            break

        name_start = position
        while position < len(raw_tag) and not raw_tag[position].isspace() and raw_tag[position] not in "=/>":
            position += 1
        name = raw_tag[name_start:position].lower()
        while position < len(raw_tag) and raw_tag[position].isspace():
            position += 1
        if position >= len(raw_tag) or raw_tag[position] != "=":
            tokens.append(AttributeToken(name, None, None, None, None))
            continue

        position += 1
        while position < len(raw_tag) and raw_tag[position].isspace():
            position += 1
        if position >= len(raw_tag):
            tokens.append(AttributeToken(name, "", position, position, None))
            break

        quote = raw_tag[position] if raw_tag[position] in "\"'" else None
        if quote:
            position += 1
            value_start = position
            value_end = raw_tag.find(quote, position)
            if value_end < 0:
                raise ValueError(f"unterminated quoted attribute {name!r}")
            position = value_end + 1
        else:
            value_start = position
            while position < len(raw_tag) and not raw_tag[position].isspace() and raw_tag[position] != ">":
                if raw_tag[position] == "/" and position + 1 < len(raw_tag) and raw_tag[position + 1] == ">":
                    break
                position += 1
            value_end = position
        tokens.append(AttributeToken(name, raw_tag[value_start:value_end], value_start, value_end, quote))
    return tokens


class TranslationSpanParser(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=False)
        self.source = source
        self.line_starts = [0]
        for index, character in enumerate(source):
            if character == "\n":
                self.line_starts.append(index + 1)
        self.cursor = 0
        self.stack: list[str] = []
        self.spans: list[RawSpan] = []
        self.lang_span: RawSpan | None = None

    def source_offset(self) -> int:
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def context(self, tag: str | None = None, attribute: str | None = None) -> str:
        parts = [*self.stack]
        if tag:
            parts.append(tag)
        value = "/".join(parts) or "document"
        return f"{value}@{attribute}" if attribute else value

    def flush_text(self, end: int) -> None:
        if end < self.cursor:
            raise ValueError("HTML parser offsets moved backwards")
        raw = self.source[self.cursor:end]
        if raw and not any(tag in PROTECTED_TEXT_TAGS for tag in self.stack):
            prefix, core, suffix = split_outer_whitespace(html.unescape(raw))
            if core:
                self.spans.append(RawSpan("text", self.context(), core, self.cursor, end, prefix, suffix))

    def consume(self, start: int, end: int) -> None:
        self.flush_text(start)
        self.cursor = end

    def markup_end(self, start: int, terminator: str) -> int:
        found = self.source.find(terminator, start)
        if found < 0:
            raise ValueError(f"unterminated HTML markup near offset {start}")
        return found + len(terminator)

    def add_attributes(self, tag: str, attrs: list[tuple[str, str | None]], raw: str, start: int) -> None:
        attr_values = dict(attrs)
        for token in scan_attributes(raw):
            if token.value is None or token.value_start is None or token.value_end is None:
                continue
            decoded = html.unescape(token.value)
            absolute_start = start + token.value_start
            absolute_end = start + token.value_end
            prefix, core, suffix = split_outer_whitespace(decoded)
            if tag == "html" and token.name == "lang":
                if self.lang_span is not None:
                    raise ValueError("multiple html lang attributes are not supported")
                self.lang_span = RawSpan("lang", "html@lang", core, absolute_start, absolute_end, prefix, suffix, token.quote)
            elif core and is_translatable_attribute(tag, attr_values, token.name):
                self.spans.append(
                    RawSpan(
                        "attribute",
                        self.context(tag, token.name),
                        core,
                        absolute_start,
                        absolute_end,
                        prefix,
                        suffix,
                        token.quote,
                    )
                )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        start = self.source_offset()
        raw = self.get_starttag_text()
        self.consume(start, start + len(raw))
        self.add_attributes(tag, attrs, raw, start)
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        start = self.source_offset()
        raw = self.get_starttag_text()
        self.consume(start, start + len(raw))
        self.add_attributes(tag, attrs, raw, start)

    def handle_endtag(self, tag: str) -> None:
        start = self.source_offset()
        self.consume(start, self.markup_end(start, ">"))
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index] == tag:
                del self.stack[index:]
                break

    def handle_comment(self, data: str) -> None:
        start = self.source_offset()
        self.consume(start, self.markup_end(start, "-->"))

    def handle_decl(self, decl: str) -> None:
        start = self.source_offset()
        self.consume(start, self.markup_end(start, ">"))

    def handle_pi(self, data: str) -> None:
        start = self.source_offset()
        self.consume(start, self.markup_end(start, ">"))

    def unknown_decl(self, data: str) -> None:
        start = self.source_offset()
        self.consume(start, self.markup_end(start, "]>"))

    def handle_data(self, data: str) -> None:
        pass

    def handle_entityref(self, name: str) -> None:
        pass

    def handle_charref(self, name: str) -> None:
        pass

    def finish(self) -> None:
        self.flush_text(len(self.source))
        self.cursor = len(self.source)


def parse_spans(source_html: str) -> tuple[list[UnitSpan], RawSpan]:
    parser = TranslationSpanParser(source_html)
    parser.feed(source_html)
    parser.close()
    parser.finish()
    if parser.lang_span is None:
        raise ValueError("source <html> must have a lang attribute")

    units = [
        UnitSpan(
            f"u{index:05d}",
            span.kind,
            span.context,
            span.source,
            span.start,
            span.end,
            span.prefix,
            span.suffix,
            span.quote,
        )
        for index, span in enumerate(sorted(parser.spans, key=lambda item: (item.start, item.end)), start=1)
    ]
    return units, parser.lang_span


def source_sha256(source: Path) -> str:
    return hashlib.sha256(source.read_bytes()).hexdigest()


def unit_record(unit: UnitSpan) -> dict[str, str]:
    return {
        "id": unit.id,
        "kind": unit.kind,
        "context": unit.context,
        "source": unit.source,
        "target": "",
    }


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        temporary.replace(path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def check_bundle_path(source: Path, bundle: Path) -> None:
    reserved = {source.resolve(), source.with_name("index.zh.html").resolve()}
    if bundle.resolve() in reserved:
        raise ValueError("bundle path cannot replace index.html or index.zh.html")


def extract_bundle(source: Path, bundle: Path, target_lang: str, force: bool = False) -> int:
    if source.name != "index.html":
        raise ValueError(f"source must be index.html, got {source.name!r}")
    if not source.is_file():
        raise ValueError(f"source does not exist: {source}")
    check_bundle_path(source, bundle)
    if bundle.exists() and not force:
        raise ValueError(f"bundle already exists; use --force to replace it: {bundle}")
    if not target_lang.strip():
        raise ValueError("target language cannot be empty")

    units, _ = parse_spans(source.read_text(encoding="utf-8"))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source_name": source.name,
        "source_sha256": source_sha256(source),
        "target_lang": target_lang,
        "units": [unit_record(unit) for unit in units],
    }
    atomic_write(bundle, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return len(units)


def load_bundle(bundle: Path) -> dict[str, object]:
    if not bundle.is_file():
        raise ValueError(f"bundle does not exist: {bundle}")
    payload = json.loads(bundle.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != BUNDLE_KEYS:
        raise ValueError("bundle top-level fields changed")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"unsupported bundle schema: {payload['schema_version']!r}")
    if not isinstance(payload["units"], list):
        raise ValueError("bundle units must be a list")
    return payload


def verified_targets(source: Path, payload: dict[str, object], units: list[UnitSpan]) -> list[str]:
    if payload["source_name"] != source.name:
        raise ValueError("bundle source name changed")
    if payload["source_sha256"] != source_sha256(source):
        raise ValueError("source changed after bundle extraction")
    if not isinstance(payload["target_lang"], str) or not payload["target_lang"].strip():
        raise ValueError("bundle target language is invalid")

    records = payload["units"]
    assert isinstance(records, list)
    if len(records) != len(units):
        raise ValueError(f"translation unit count changed: expected={len(units)} actual={len(records)}")

    targets: list[str] = []
    for unit, record in zip(units, records):
        if not isinstance(record, dict) or set(record) != UNIT_KEYS:
            raise ValueError(f"translation unit fields changed near {unit.id}")
        expected = unit_record(unit)
        for key in ("id", "kind", "context", "source"):
            if record[key] != expected[key]:
                raise ValueError(f"translation unit {unit.id} changed protected field {key!r}")
        target = record["target"]
        if not isinstance(target, str) or not target.strip():
            raise ValueError(f"translation unit {unit.id} has an empty target")
        targets.append(target)
    return targets


def render_translation(source_html: str, units: list[UnitSpan], targets: list[str], lang_span: RawSpan, target_lang: str) -> str:
    replacements: list[tuple[int, int, str]] = []
    for unit, target in zip(units, targets):
        escaped = html.escape(f"{unit.prefix}{target}{unit.suffix}", quote=unit.kind == "attribute")
        if unit.kind == "attribute" and unit.quote is None:
            escaped = f'"{escaped}"'
        replacements.append((unit.start, unit.end, escaped))
    escaped_lang = html.escape(f"{lang_span.prefix}{target_lang}{lang_span.suffix}", quote=True)
    if lang_span.quote is None:
        escaped_lang = f'"{escaped_lang}"'
    replacements.append(
        (
            lang_span.start,
            lang_span.end,
            escaped_lang,
        )
    )

    result = source_html
    for start, end, replacement in sorted(replacements, reverse=True):
        result = result[:start] + replacement + result[end:]
    return result


def merge_bundle(
    source: Path,
    bundle: Path,
    force: bool = False,
    semantic_report: Path | None = None,
    output: Path | None = None,
    asset_root: Path | None = None,
) -> Path:
    if source.name != "index.html":
        raise ValueError(f"source must be index.html, got {source.name!r}")
    if not source.is_file():
        raise ValueError(f"source does not exist: {source}")
    check_bundle_path(source, bundle)
    target = output or source.with_name("index.zh.html")
    if target.name != "index.zh.html":
        raise ValueError(f"target must be index.zh.html, got {target.name!r}")
    if target.resolve() == source.resolve():
        raise ValueError("target cannot replace source index.html")
    if target.exists() and not force:
        raise ValueError(f"target already exists; use --force to replace it: {target}")
    if semantic_report and semantic_report.resolve() in {source.resolve(), target.resolve()}:
        raise ValueError("semantic report cannot replace source or target HTML")

    payload = load_bundle(bundle)
    source_html = source.read_text(encoding="utf-8")
    units, lang_span = parse_spans(source_html)
    targets = verified_targets(source, payload, units)
    target_lang = payload["target_lang"]
    assert isinstance(target_lang, str)
    rendered = render_translation(source_html, units, targets, lang_span, target_lang)
    asset_root = (asset_root or source.parent).resolve()
    if not asset_root.is_dir():
        raise ValueError(f"asset root does not exist: {asset_root}")
    if source.parent.resolve() != target.parent.resolve():
        rendered = rewrite_local_resources(rendered, asset_root, target.parent.resolve(), asset_root)

    temporary: Path | None = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=".index.zh.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(rendered)
            temporary = Path(handle.name)
        errors = validate(source, temporary, target_lang, enforce_target_name=False, asset_root=asset_root)
        if errors:
            raise ValueError("generated translation failed validation:\n- " + "\n- ".join(errors))
        temporary.replace(target)
        temporary = None
        semantic_payload = semantic_lint(source, target)
        if semantic_report:
            write_semantic_report(semantic_report, semantic_payload)
        print_semantic_summary(semantic_payload)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    return target


def self_check() -> int:
    source_html = """<!doctype html><html lang=en><head><title>Source &amp; Notes</title><meta name="description" content="Source description"><link rel="stylesheet" href="mirror_assets/site.css"><style>.box { color: black; }</style><script>window.ready = true;</script></head><body><p>Hello&nbsp;world &amp; friends</p><img alt="Cover image" src="mirror_assets/cover.jpg"><pre>npm run build</pre><input type="submit" value=Subscribe placeholder="Email"></body></html>"""
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        assets = root / "mirror_assets"
        assets.mkdir()
        (assets / "site.css").write_text("body {}", encoding="utf-8")
        (assets / "cover.jpg").write_bytes(b"asset")
        source = root / "index.html"
        bundle = root / "translation.json"
        source.write_text(source_html, encoding="utf-8")

        for reserved in (source, source.with_name("index.zh.html")):
            try:
                extract_bundle(source, reserved, "zh-CN", force=True)
            except ValueError as error:
                assert "bundle path cannot replace" in str(error)
            else:
                raise AssertionError("reserved HTML path was accepted as a bundle")
        assert source.read_text(encoding="utf-8") == source_html

        count = extract_bundle(source, bundle, "zh-CN")
        payload = load_bundle(bundle)
        assert count == len(payload["units"])
        for record in payload["units"]:
            record["target"] = f"Translated: {record['source']}"
        bundle.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        target = merge_bundle(source, bundle)
        target_html = target.read_text(encoding="utf-8")
        assert "lang=\"zh-CN\"" in target_html
        assert "window.ready = true;" in target_html
        assert "npm run build" in target_html
        assert "mirror_assets/cover.jpg" in target_html
        assert not validate(source, target, "zh-CN")

        try:
            merge_bundle(source, bundle)
        except ValueError as error:
            assert "target already exists" in str(error)
        else:
            raise AssertionError("existing target was overwritten without --force")

        unchanged_target = target.read_text(encoding="utf-8")
        source.write_text(source_html + " ", encoding="utf-8")
        try:
            merge_bundle(source, bundle, force=True)
        except ValueError as error:
            assert "source changed" in str(error)
        else:
            raise AssertionError("source hash drift was accepted")
        assert target.read_text(encoding="utf-8") == unchanged_target
        source.write_text(source_html, encoding="utf-8")

        reordered = load_bundle(bundle)
        reordered["units"] = list(reversed(reordered["units"]))
        bundle.write_text(json.dumps(reordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            merge_bundle(source, bundle, force=True)
        except ValueError as error:
            assert "protected field" in str(error)
        else:
            raise AssertionError("reordered translation units were accepted")

        incomplete = payload
        incomplete["units"][0]["target"] = ""
        bundle.write_text(json.dumps(incomplete, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            merge_bundle(source, bundle, force=True)
        except ValueError as error:
            assert "empty target" in str(error)
        else:
            raise AssertionError("empty translation target was accepted")

        (assets / "cover.jpg").unlink()
        assert any("missing local resource" in error for error in validate(source, target, "zh-CN"))
        (assets / "cover.jpg").write_bytes(b"asset")
        target.write_text(target_html.replace("window.ready = true", "window.ready = false"), encoding="utf-8")
        assert any("protected code/script/style text changed" in error for error in validate(source, target, "zh-CN"))

        repaired = load_bundle(bundle)
        for record in repaired["units"]:
            assert isinstance(record, dict)
            record["target"] = f"Translated: {record['source']}"
        bundle.write_text(json.dumps(repaired, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        independent = root / "derived" / "index.zh.html"
        independent.parent.mkdir()
        target = merge_bundle(source, bundle, output=independent, asset_root=root)
        assert "../mirror_assets/cover.jpg" in target.read_text(encoding="utf-8")
        assert not validate(source, target, "zh-CN", asset_root=root)

    print("self-check ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract and merge translatable nodes from a static HTML mirror.")
    parser.add_argument("--self-check", action="store_true", help="Run built-in extraction and merge checks.")
    subparsers = parser.add_subparsers(dest="command")

    extract = subparsers.add_parser("extract", help="Create a JSON translation bundle from index.html.")
    extract.add_argument("source", help="Source index.html.")
    extract.add_argument("--bundle", required=True, help="JSON bundle to create.")
    extract.add_argument("--target-lang", default="zh-CN", help="Target HTML language.")
    extract.add_argument("--force", action="store_true", help="Replace an existing bundle.")

    merge = subparsers.add_parser("merge", help="Merge a completed JSON bundle into index.zh.html.")
    merge.add_argument("source", help="Source index.html.")
    merge.add_argument("--bundle", required=True, help="Completed JSON translation bundle.")
    merge.add_argument("--force", action="store_true", help="Replace an existing index.zh.html after validation.")
    merge.add_argument("--semantic-report", help="Optional JSON report path for semantic lint warnings.")
    merge.add_argument("--output", help="Optional independent index.zh.html output path.")
    merge.add_argument("--asset-root", help="Shared local asset root; defaults to the source directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    if args.command is None:
        parser.error("a command is required unless --self-check is used")
    try:
        if args.command == "extract":
            count = extract_bundle(Path(args.source), Path(args.bundle), args.target_lang, args.force)
            print(f"extracted {count} translation units -> {args.bundle}")
        else:
            target = merge_bundle(
                Path(args.source),
                Path(args.bundle),
                args.force,
                Path(args.semantic_report) if args.semantic_report else None,
                Path(args.output) if args.output else None,
                Path(args.asset_root) if args.asset_root else None,
            )
            print(f"merged and validated -> {target}")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
