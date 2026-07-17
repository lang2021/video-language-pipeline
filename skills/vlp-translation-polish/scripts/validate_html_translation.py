#!/usr/bin/env python3
"""Validate mechanical preservation for a translated static HTML mirror."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit


PROTECTED_TEXT_TAGS = {"code", "pre", "script", "style", "template", "textarea"}
RESOURCE_LINK_RELS = {"icon", "mask-icon", "preload", "stylesheet"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


@dataclass(frozen=True)
class StartTag:
    kind: str
    tag: str
    attrs: tuple[tuple[str, str | None], ...]


@dataclass(frozen=True)
class SemanticUnit:
    kind: str
    context: str
    text: str


@dataclass(frozen=True)
class ResourceReference:
    label: str
    value: str
    start: int
    end: int
    css: bool = False


class MirrorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.tag_events: list[tuple[str, str]] = []
        self.start_tags: list[StartTag] = []
        self.protected_text: list[tuple[tuple[str, ...], str]] = []
        self.stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tag_events.append(("start", tag))
        self.start_tags.append(StartTag("start", tag, tuple(attrs)))
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tag_events.append(("void", tag))
        self.start_tags.append(StartTag("void", tag, tuple(attrs)))

    def handle_endtag(self, tag: str) -> None:
        self.tag_events.append(("end", tag))
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        protected = tuple(tag for tag in self.stack if tag in PROTECTED_TEXT_TAGS)
        if protected:
            self.protected_text.append((protected, data))

    def handle_entityref(self, name: str) -> None:
        self.handle_data(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.handle_data(f"&#{name};")


class SemanticParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.units: list[SemanticUnit] = []

    def context(self, tag: str | None = None, attribute: str | None = None) -> str:
        parts = [*self.stack]
        if tag:
            parts.append(tag)
        value = "/".join(parts) or "document"
        return f"{value}@{attribute}" if attribute else value

    def add_attributes(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_values = dict(attrs)
        for key, value in attrs:
            if value and is_translatable_attribute(tag, attr_values, key) and not (tag == "html" and key == "lang"):
                self.units.append(SemanticUnit("attribute", self.context(tag, key), value.strip()))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.add_attributes(tag, attrs)
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.add_attributes(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if any(tag in PROTECTED_TEXT_TAGS for tag in self.stack):
            return
        text = data.strip()
        if text:
            self.units.append(SemanticUnit("text", self.context(), text))


class ResourceParser(HTMLParser):
    """Find only local-resource value spans so independent outputs can rebase them."""

    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=False)
        self.source = source
        self.line_starts = [0]
        for index, character in enumerate(source):
            if character == "\n":
                self.line_starts.append(index + 1)
        self.stack: list[str] = []
        self.references: list[ResourceReference] = []

    def source_offset(self) -> int:
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def add_css(self, label: str, value: str, offset: int) -> None:
        for start, end in css_url_spans(value):
            self.references.append(ResourceReference(label, html_unescape(value[start:end]), offset + start, offset + end, True))

    def add_attributes(self, tag: str, attrs: list[tuple[str, str | None]], raw: str, start: int) -> None:
        attr_values = dict(attrs)
        for name, raw_value, value_start, value_end in scan_attributes(raw):
            if raw_value is None or value_start is None or value_end is None:
                continue
            value = html_unescape(raw_value)
            offset = start + value_start
            if name == "style":
                self.add_css(f"{tag}[style]", value, offset)
            elif resource_attribute(tag, attr_values, name):
                if name == "srcset":
                    for candidate_start, candidate_end in srcset_url_spans(value):
                        self.references.append(
                            ResourceReference(f"{tag}[srcset]", value[candidate_start:candidate_end], offset + candidate_start, offset + candidate_end)
                        )
                else:
                    self.references.append(ResourceReference(f"{tag}[{name}]", value, offset, offset + len(raw_value)))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        start = self.source_offset()
        raw = self.get_starttag_text()
        self.add_attributes(tag, attrs, raw, start)
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        start = self.source_offset()
        self.add_attributes(tag, attrs, self.get_starttag_text(), start)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if "style" in self.stack:
            self.add_css("style[url]", data, self.source_offset())


def html_unescape(value: str) -> str:
    return value.replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'")


def scan_attributes(raw_tag: str) -> list[tuple[str, str | None, int | None, int | None]]:
    """Return lower-case attribute names plus raw value offsets within one start tag."""
    position = 1
    while position < len(raw_tag) and raw_tag[position].isspace():
        position += 1
    while position < len(raw_tag) and not raw_tag[position].isspace() and raw_tag[position] not in "/>":
        position += 1
    tokens: list[tuple[str, str | None, int | None, int | None]] = []
    while position < len(raw_tag):
        while position < len(raw_tag) and raw_tag[position].isspace():
            position += 1
        if position >= len(raw_tag) or raw_tag[position] in "/>":
            break
        start = position
        while position < len(raw_tag) and not raw_tag[position].isspace() and raw_tag[position] not in "=/>":
            position += 1
        name = raw_tag[start:position].lower()
        while position < len(raw_tag) and raw_tag[position].isspace():
            position += 1
        if position >= len(raw_tag) or raw_tag[position] != "=":
            tokens.append((name, None, None, None))
            continue
        position += 1
        while position < len(raw_tag) and raw_tag[position].isspace():
            position += 1
        quote_char = raw_tag[position] if position < len(raw_tag) and raw_tag[position] in "\"'" else None
        if quote_char:
            position += 1
            value_start = position
            value_end = raw_tag.find(quote_char, position)
            if value_end < 0:
                raise ValueError(f"unterminated quoted attribute {name!r}")
            position = value_end + 1
        else:
            value_start = position
            while position < len(raw_tag) and not raw_tag[position].isspace() and raw_tag[position] != ">":
                position += 1
            value_end = position
        tokens.append((name, raw_tag[value_start:value_end], value_start, value_end))
    return tokens


def resource_attribute(tag: str, attrs: dict[str, str | None], key: str) -> bool:
    if key in {"src", "srcset"}:
        return True
    if key == "poster" and tag == "video":
        return True
    if key == "href" and tag == "link":
        return bool(set((attrs.get("rel") or "").lower().split()) & RESOURCE_LINK_RELS)
    if key == "href" and tag in {"image", "use"}:
        return True
    return key == "data" and tag == "object"


def srcset_url_spans(value: str) -> list[tuple[int, int]]:
    # ponytail: mirrors use comma-separated candidates; use a full srcset parser only for a real data-URL failure.
    spans: list[tuple[int, int]] = []
    position = 0
    for candidate in value.split(","):
        leading = len(candidate) - len(candidate.lstrip())
        url = candidate.lstrip().split(None, 1)[0] if candidate.strip() else ""
        if url:
            start = position + leading
            spans.append((start, start + len(url)))
        position += len(candidate) + 1
    return spans


def css_url_spans(value: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    index = 0
    while index < len(value):
        if value.startswith("/*", index):
            end = value.find("*/", index + 2)
            index = len(value) if end < 0 else end + 2
            continue
        match = re.match(r"url\(\s*", value[index:], flags=re.IGNORECASE)
        if not match:
            index += 1
            continue
        start = index + match.end()
        quote_char = value[start] if start < len(value) and value[start] in "\"'" else None
        if quote_char:
            start += 1
            end = value.find(quote_char, start)
        else:
            end = value.find(")", start)
            while end > start and value[end - 1].isspace():
                end -= 1
        if end < 0:
            break
        if start < end:
            spans.append((start, end))
        close = value.find(")", end + 1 if quote_char else end)
        index = len(value) if close < 0 else close + 1
    return spans


def parse_html(path: Path) -> MirrorParser:
    parser = MirrorParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


def parse_semantic_units(path: Path) -> list[SemanticUnit]:
    parser = SemanticParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser.units


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def english_word_count(value: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:['’\-][A-Za-z]+)?", value))


def effective_length(value: str) -> int:
    return len(re.sub(r"[\W_]+", "", value, flags=re.UNICODE))


def semantic_lint(source: Path, target: Path) -> dict[str, object]:
    source_units = parse_semantic_units(source)
    target_units = parse_semantic_units(target)
    warnings: list[dict[str, object]] = []
    if len(source_units) != len(target_units):
        warnings.append(
            {
                "code": "visible_text_unit_count_mismatch",
                "source_count": len(source_units),
                "target_count": len(target_units),
            }
        )

    for index, (left, right) in enumerate(zip(source_units, target_units), start=1):
        source_text = normalized_text(left.text)
        target_text = normalized_text(right.text)
        base = {
            "unit_id": f"u{index:05d}",
            "context": left.context,
            "source": source_text,
            "target": target_text,
        }
        if source_text == target_text and english_word_count(source_text) >= 8:
            warnings.append({"code": "long_english_unchanged", **base})
        source_length = effective_length(source_text)
        target_length = effective_length(target_text)
        if source_length <= 24 and target_length >= 32 and target_length >= source_length * 3:
            warnings.append({"code": "short_source_length_expansion", **base})
        if source_length >= 120 and target_length <= 32 and source_length >= target_length * 3:
            warnings.append({"code": "long_source_length_contraction", **base})

    translated_characters = sum(effective_length(unit.text) for unit in target_units)
    source_characters = sum(effective_length(unit.text) for unit in source_units)
    chinese_characters = sum(len(re.findall(r"[\u3400-\u9fff]", unit.text)) for unit in target_units)

    return {
        "schema_version": 1,
        "source": str(source),
        "translated": str(target),
        "source_unit_count": len(source_units),
        "translated_unit_count": len(target_units),
        "source_effective_length": source_characters,
        "translated_effective_length": translated_characters,
        "source_target_length_ratio": round(translated_characters / source_characters, 4) if source_characters else 0.0,
        "chinese_coverage_ratio": round(chinese_characters / translated_characters, 4) if translated_characters else 0.0,
        "warning_count": len(warnings),
        "warning_code_counts": dict(sorted(Counter(str(item["code"]) for item in warnings).items())),
        "warnings": warnings,
    }


def write_semantic_report(report: Path, payload: dict[str, object]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_semantic_summary(payload: dict[str, object]) -> None:
    print(
        "semantic lint: "
        f"units={payload['source_unit_count']}/{payload['translated_unit_count']} "
        f"warnings={payload['warning_count']} "
        f"zh_coverage={payload['chinese_coverage_ratio']}",
        file=sys.stderr,
    )
    warnings = payload["warnings"]
    assert isinstance(warnings, list)
    for warning in warnings:
        assert isinstance(warning, dict)
        suffix = f" {warning['unit_id']}" if "unit_id" in warning else ""
        print(f"warning: {warning['code']}{suffix}", file=sys.stderr)


def is_translatable_attribute(tag: str, attrs: dict[str, str | None], key: str) -> bool:
    if tag == "html" and key == "lang":
        return True
    if key in {"alt", "aria-label", "placeholder", "title"}:
        return True
    if tag == "input" and key == "value" and (attrs.get("type") or "").lower() in {"button", "reset", "submit"}:
        return True
    if tag == "meta" and key == "content":
        marker = (attrs.get("name") or attrs.get("property") or "").lower()
        return marker in {"description", "og:description", "og:title", "twitter:description", "twitter:title"}
    return False


def compare_start_tags(source: list[StartTag], target: list[StartTag], allow_resource_rewrite: bool = False) -> list[str]:
    if len(source) != len(target):
        return [f"start tag count mismatch: source={len(source)} target={len(target)}"]

    errors: list[str] = []
    for index, (left, right) in enumerate(zip(source, target), start=1):
        if (left.kind, left.tag) != (right.kind, right.tag):
            errors.append(f"start tag mismatch at {index}: source={left.kind}:{left.tag} target={right.kind}:{right.tag}")
            continue
        if len(left.attrs) != len(right.attrs):
            errors.append(f"attribute count mismatch at {index} for <{left.tag}>")
            continue
        source_attrs = dict(left.attrs)
        for (source_key, source_value), (target_key, target_value) in zip(left.attrs, right.attrs):
            if source_key != target_key:
                errors.append(f"attribute name mismatch at {index} for <{left.tag}>: {source_key!r} != {target_key!r}")
            elif (
                source_value != target_value
                and not is_translatable_attribute(left.tag, source_attrs, source_key)
                and not (allow_resource_rewrite and resource_attribute(left.tag, source_attrs, source_key))
                and not (allow_resource_rewrite and source_key == "style")
            ):
                errors.append(f"protected attribute changed at {index} for <{left.tag}>[{source_key}]")
    return errors


def split_srcset(value: str) -> list[str]:
    # ponytail: finalized mirrors separate candidates with comma+whitespace; add a full parser only for a real compact-srcset failure.
    return [candidate for candidate in re.split(r",\s+", value.strip()) if candidate]


def resource_references(path: Path) -> list[ResourceReference]:
    parser = ResourceParser(path.read_text(encoding="utf-8"))
    parser.feed(parser.source)
    parser.close()
    return parser.references


def local_resource_path(value: str, base: Path, asset_root: Path) -> Path | None:
    parsed = urlsplit(value.strip())
    if not parsed.path or parsed.scheme or parsed.netloc or value.lstrip().startswith(("#", "data:")):
        return None
    if parsed.path.startswith("/"):
        raise ValueError(f"non-local resource path: {value!r}")
    asset_root = asset_root.resolve()
    candidate = (base / unquote(parsed.path)).resolve()
    try:
        candidate.relative_to(asset_root)
    except ValueError as error:
        raise ValueError(f"resource escapes asset root: {value!r}") from error
    if not candidate.is_file() or candidate.stat().st_size == 0:
        raise ValueError(f"missing local resource: {value!r}")
    return candidate


def resource_signature(references: list[ResourceReference], base: Path, asset_root: Path) -> tuple[list[tuple[str, str]], list[str]]:
    signatures: list[tuple[str, str]] = []
    errors: list[str] = []
    for reference in references:
        try:
            candidate = local_resource_path(reference.value, base, asset_root)
        except ValueError as error:
            errors.append(f"{reference.label}: {error}")
            continue
        signatures.append((reference.label, str(candidate) if candidate else reference.value))
    return signatures, errors


def rebased_resource_url(value: str, source_base: Path, output_base: Path, asset_root: Path) -> str:
    candidate = local_resource_path(value, source_base, asset_root)
    if candidate is None:
        return value
    parsed = urlsplit(value)
    relative = Path(os.path.relpath(candidate, output_base.resolve())).as_posix()
    return urlunsplit(("", "", quote(relative, safe="/%"), parsed.query, parsed.fragment))


def rewrite_local_resources(source_html: str, source_base: Path, output_base: Path, asset_root: Path) -> str:
    """Rebase only local resource URLs; all visible text and ordinary links stay untouched."""
    parser = ResourceParser(source_html)
    parser.feed(source_html)
    parser.close()
    replacements: list[tuple[int, int, str]] = []
    for reference in parser.references:
        replacement = rebased_resource_url(reference.value, source_base, output_base, asset_root)
        if replacement == reference.value:
            continue
        if not reference.css:
            replacement = replacement.replace("&", "&amp;")
        replacements.append((reference.start, reference.end, replacement))
    result = source_html
    for start, end, replacement in sorted(replacements, reverse=True):
        result = result[:start] + replacement + result[end:]
    return result


def css_equivalent(source_css: str, target_css: str, source_base: Path, target_base: Path, asset_root: Path) -> bool:
    source_spans = css_url_spans(source_css)
    target_spans = css_url_spans(target_css)
    if len(source_spans) != len(target_spans):
        return False
    source_cursor = target_cursor = 0
    for (source_start, source_end), (target_start, target_end) in zip(source_spans, target_spans):
        if source_css[source_cursor:source_start] != target_css[target_cursor:target_start]:
            return False
        try:
            source_value = source_css[source_start:source_end]
            target_value = target_css[target_start:target_end]
            source_path = local_resource_path(source_value, source_base, asset_root)
            target_path = local_resource_path(target_value, target_base, asset_root)
        except ValueError:
            return False
        if source_path is None or target_path is None:
            if source_value != target_value:
                return False
        elif source_path != target_path:
            return False
        source_cursor, target_cursor = source_end, target_end
    return source_css[source_cursor:] == target_css[target_cursor:]


def style_changes(source_html: MirrorParser, target_html: MirrorParser, source_base: Path, target_base: Path, asset_root: Path) -> list[str]:
    errors: list[str] = []
    for index, (left, right) in enumerate(zip(source_html.start_tags, target_html.start_tags), start=1):
        if left.tag != right.tag:
            continue
        source_style = dict(left.attrs).get("style")
        target_style = dict(right.attrs).get("style")
        if source_style != target_style and not css_equivalent(source_style or "", target_style or "", source_base, target_base, asset_root):
            errors.append(f"non-resource CSS changed at {index} for <{left.tag}>[style]")
    for index, ((source_context, source_text), (target_context, target_text)) in enumerate(
        zip(source_html.protected_text, target_html.protected_text), start=1
    ):
        if source_context != target_context:
            continue
        if "style" in source_context and source_text != target_text and not css_equivalent(source_text, target_text, source_base, target_base, asset_root):
            errors.append(f"non-resource CSS changed in <style> block {index}")
    return errors


def html_lang(start_tags: list[StartTag]) -> str | None:
    for item in start_tags:
        if item.tag == "html":
            return dict(item.attrs).get("lang")
    return None


def validate(
    source: Path,
    target: Path,
    target_lang: str,
    enforce_target_name: bool = True,
    asset_root: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if source.name != "index.html":
        errors.append(f"source must be index.html, got {source.name!r}")
    if enforce_target_name and target.name != "index.zh.html":
        errors.append(f"target must be index.zh.html, got {target.name!r}")
    if errors:
        return errors

    asset_root = (asset_root or source.parent).resolve()
    independent_output = source.parent.resolve() != target.parent.resolve()
    if not asset_root.is_dir():
        return [f"asset root does not exist: {asset_root}"]

    source_html = parse_html(source)
    target_html = parse_html(target)
    if source_html.tag_events != target_html.tag_events:
        errors.append("HTML tag sequence changed")
    errors.extend(compare_start_tags(source_html.start_tags, target_html.start_tags, independent_output))
    if source_html.protected_text != target_html.protected_text and not independent_output:
        errors.append("protected code/script/style text changed")
    if html_lang(target_html.start_tags) != target_lang:
        errors.append(f"target html lang must be {target_lang!r}")
    source_refs = resource_references(source)
    target_refs = resource_references(target)
    if not independent_output:
        if [(item.label, item.value) for item in source_refs] != [(item.label, item.value) for item in target_refs]:
            errors.append("resource references changed")
        _, target_errors = resource_signature(target_refs, target.parent.resolve(), target.parent.resolve())
        errors.extend(target_errors)
    else:
        source_signature, source_errors = resource_signature(source_refs, asset_root, asset_root)
        target_signature, target_errors = resource_signature(target_refs, target.parent.resolve(), asset_root)
        errors.extend(source_errors)
        errors.extend(target_errors)
        if source_signature != target_signature:
            errors.append("resource references resolve to different files")
        errors.extend(style_changes(source_html, target_html, asset_root, target.parent.resolve(), asset_root))
        if source_html.protected_text != target_html.protected_text:
            source_protected = [(context, text) for context, text in source_html.protected_text if "style" not in context]
            target_protected = [(context, text) for context, text in target_html.protected_text if "style" not in context]
            if source_protected != target_protected:
                errors.append("protected code/script/style text changed")
    return errors


def run_check(source: Path, target: Path, target_lang: str, asset_root: Path | None = None) -> int:
    errors = validate(source, target, target_lang, asset_root=asset_root)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("ok")
    return 0


def run_semantic_lint(source: Path, target: Path, report: Path | None = None) -> int:
    if report and report.resolve() in {source.resolve(), target.resolve()}:
        raise ValueError("semantic report cannot replace source or translated HTML")
    payload = semantic_lint(source, target)
    if report:
        write_semantic_report(report, payload)
    print_semantic_summary(payload)
    return 0


def self_check() -> int:
    source_html = """<!doctype html><html lang=\"en\"><head><title>Source</title><link rel=\"stylesheet\" href=\"mirror_assets/site.css\"><style>.box { color: black; background: url('mirror_assets/bg.jpg'); }</style><script>window.ready = true;</script></head><body><a href=\"/about\">About</a><p>Hello</p><img alt=\"Cover\" src=\"mirror_assets/cover.jpg\" srcset=\"mirror_assets/cover.jpg 1x, mirror_assets/cover@2x.jpg 2x\"><pre>npm run build</pre><input type=\"submit\" value=\"Subscribe\" placeholder=\"Email\"></body></html>"""
    target_html = """<!doctype html><html lang=\"zh-CN\"><head><title>译文</title><link rel=\"stylesheet\" href=\"mirror_assets/site.css\"><style>.box { color: black; background: url('mirror_assets/bg.jpg'); }</style><script>window.ready = true;</script></head><body><a href=\"/about\">关于</a><p>你好</p><img alt=\"封面\" src=\"mirror_assets/cover.jpg\" srcset=\"mirror_assets/cover.jpg 1x, mirror_assets/cover@2x.jpg 2x\"><pre>npm run build</pre><input type=\"submit\" value=\"订阅\" placeholder=\"邮箱\"></body></html>"""
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        assets = root / "mirror_assets"
        assets.mkdir()
        for name in ("site.css", "cover.jpg", "cover@2x.jpg", "bg.jpg"):
            (assets / name).write_bytes(b"asset")
        source = root / "index.html"
        target = root / "index.zh.html"
        source.write_text(source_html, encoding="utf-8")
        target.write_text(target_html, encoding="utf-8")
        assert not validate(source, target, "zh-CN")

        target.write_text(target_html.replace("mirror_assets/cover.jpg\"", "https://example.com/cover.jpg\"", 1), encoding="utf-8")
        assert any("protected attribute changed" in error or "resource references changed" in error for error in validate(source, target, "zh-CN"))

        target.write_text(target_html, encoding="utf-8")
        (assets / "cover.jpg").unlink()
        assert any("missing local resource" in error for error in validate(source, target, "zh-CN"))

        (assets / "cover.jpg").write_bytes(b"asset")
        target.write_text(target_html.replace("window.ready = true", "window.ready = false"), encoding="utf-8")
        assert any("protected code/script/style text changed" in error for error in validate(source, target, "zh-CN"))

        source.write_text(source_html.replace("mirror_assets/cover.jpg\"", "../other/cover.jpg\"", 1), encoding="utf-8")
        target.write_text(target_html.replace("mirror_assets/cover.jpg\"", "../other/cover.jpg\"", 1), encoding="utf-8")
        assert any("resource escapes asset root" in error for error in validate(source, target, "zh-CN"))

        source.write_text(source_html, encoding="utf-8")
        independent = root / "derived" / "index.zh.html"
        independent.parent.mkdir()
        rebased = rewrite_local_resources(target_html, root, independent.parent, root)
        independent.write_text(rebased, encoding="utf-8")
        assert "../mirror_assets/cover.jpg" in rebased
        assert "../mirror_assets/bg.jpg" in rebased
        assert not validate(source, independent, "zh-CN", asset_root=root)
        assert any("resource references resolve" in error for error in validate(source, independent, "zh-CN", asset_root=assets))
        independent.write_text(rebased.replace("../mirror_assets/cover.jpg", "../missing.jpg", 1), encoding="utf-8")
        assert any("missing local resource" in error for error in validate(source, independent, "zh-CN", asset_root=root))
        independent.write_text(rebased.replace("window.ready = true", "window.ready = false"), encoding="utf-8")
        assert any("protected code/script/style text changed" in error for error in validate(source, independent, "zh-CN", asset_root=root))
        independent.write_text(rebased.replace("color: black", "color: red"), encoding="utf-8")
        assert any("non-resource CSS changed" in error for error in validate(source, independent, "zh-CN", asset_root=root))
        independent.write_text(rebased.replace('href=\"/about\"', 'href=\"/other\"'), encoding="utf-8")
        assert any("protected attribute changed" in error for error in validate(source, independent, "zh-CN", asset_root=root))

        semantic_source = root / "semantic-source.html"
        semantic_target = root / "semantic-target.html"
        semantic_source.write_text(
            "<html lang=\"en\"><body><p>This is a complete English sentence with many ordinary words.</p><a>Politics</a></body></html>",
            encoding="utf-8",
        )
        semantic_target.write_text(
            "<html lang=\"zh-CN\"><body><p>这是一句完整的中文翻译，表达了原文的意思。</p><a>政治</a></body></html>",
            encoding="utf-8",
        )
        assert not semantic_lint(semantic_source, semantic_target)["warnings"]

        semantic_target.write_text(semantic_source.read_text(encoding="utf-8"), encoding="utf-8")
        warnings = semantic_lint(semantic_source, semantic_target)["warnings"]
        assert any(item["code"] == "long_english_unchanged" for item in warnings)

        semantic_target.write_text(
            "<html lang=\"zh-CN\"><body><p>这是一句完整的中文翻译，表达了原文的意思。</p><a>我认为在西方失业问题已经永久存在并且会持续影响社会结构与长期公共政策选择</a></body></html>",
            encoding="utf-8",
        )
        warnings = semantic_lint(semantic_source, semantic_target)["warnings"]
        assert any(item["code"] == "short_source_length_expansion" for item in warnings)

        report = root / "semantic-report.json"
        assert run_semantic_lint(semantic_source, semantic_target, report) == 0
        assert json.loads(report.read_text(encoding="utf-8"))["warning_count"]

    print("self-check ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate static HTML mirror preservation after agent translation.")
    parser.add_argument("source", nargs="?", help="Source index.html.")
    parser.add_argument("translated", nargs="?", help="Translated index.zh.html.")
    parser.add_argument("--target-lang", default="zh-CN", help="Required lang value on the translated <html> tag.")
    parser.add_argument("--semantic-lint", action="store_true", help="Emit read-only semantic warnings without changing validation success.")
    parser.add_argument("--semantic-report", help="Optional JSON report path for --semantic-lint.")
    parser.add_argument("--asset-root", help="Shared local asset root for an independent output directory.")
    parser.add_argument("--self-check", action="store_true", help="Run built-in validation checks.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    if not args.source or not args.translated:
        parser.error("source and translated are required unless --self-check is used")
    if args.semantic_report and not args.semantic_lint:
        parser.error("--semantic-report requires --semantic-lint")
    if args.semantic_lint:
        return run_semantic_lint(Path(args.source), Path(args.translated), Path(args.semantic_report) if args.semantic_report else None)
    return run_check(Path(args.source), Path(args.translated), args.target_lang, Path(args.asset_root) if args.asset_root else None)


if __name__ == "__main__":
    raise SystemExit(main())
