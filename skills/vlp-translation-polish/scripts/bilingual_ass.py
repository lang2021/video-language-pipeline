#!/usr/bin/env python3
"""双语 SRT -> 双语 ASS。

输入 SRT 每条字幕应为两行文本：目标语言在上，原文在下。
本脚本只生成 ASS 字幕资产，不做翻译、不烧录视频。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TIME_RE = re.compile(
    r"^(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})"
)

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 512
PlayResY: 288
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{cn_size},&H00FFFFFF,&H000000FF,&H64000000,&H00000000,1,0,0,0,100,100,0,0,1,1.2,0,2,20,20,{marginv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

SIZE_TABLE = {360: (22, 13), 720: (22, 13), 1080: (20, 12), 2160: (20, 12)}
SCRIPT_FONT = {
    "hangul": "Apple SD Gothic Neo",
    "arabic": "Geeza Pro",
    "kana": "Hiragino Sans",
}


def parse_srt(text: str) -> list[tuple[str, str, list[str]]]:
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n").strip())
    items: list[tuple[str, str, list[str]]] = []
    for index, block in enumerate(blocks, start=1):
        lines = [line.strip("\ufeff ") for line in block.split("\n") if line.strip()]
        if len(lines) < 3:
            raise ValueError(f"第 {index} 个 SRT block 不完整")
        time_line_index = 1 if lines[0].isdigit() else 0
        match = TIME_RE.search(lines[time_line_index])
        if not match:
            raise ValueError(f"第 {index} 个 SRT block 缺少合法时间戳")
        content = lines[time_line_index + 1 :]
        if not content:
            raise ValueError(f"第 {index} 个 SRT block 缺少字幕文本")
        items.append((match.group(1), match.group(2), content))
    validate_items(items)
    return items


def srt_time_to_ms(value: str) -> int:
    value = value.replace(".", ",")
    hms, ms = value.split(",")
    hour, minute, second = [int(part) for part in hms.split(":")]
    return ((hour * 60 + minute) * 60 + second) * 1000 + int(ms)


def srt_time_to_ass(value: str) -> str:
    value = value.replace(".", ",")
    hms, ms = value.split(",")
    hour, minute, second = hms.split(":")
    centisecond = int(ms) // 10
    return f"{int(hour)}:{minute}:{second}.{centisecond:02d}"


def validate_items(items: list[tuple[str, str, list[str]]]) -> None:
    if not items:
        raise ValueError("未解析到任何字幕条")
    previous_end = -1
    for index, (start, end, _lines) in enumerate(items, start=1):
        start_ms = srt_time_to_ms(start)
        end_ms = srt_time_to_ms(end)
        if end_ms <= start_ms:
            raise ValueError(f"第 {index} 条字幕 end time 不晚于 start time")
        if start_ms < previous_end:
            raise ValueError(f"第 {index} 条字幕与上一条时间重叠")
        previous_end = end_ms


def ass_escape(text: str) -> str:
    # ponytail: avoid ASS override injection; preserve exact braces later if users need math/code字幕.
    return text.replace("\\", "＼").replace("{", "（").replace("}", "）")


def build_ass(
    items: list[tuple[str, str, list[str]]],
    cn_size: int,
    en_size: int,
    font: str = "PingFang SC",
    marginv: int = 16,
) -> str:
    output = [ASS_HEADER.format(font=font, cn_size=cn_size, marginv=marginv)]
    for start, end, lines in items:
        if len(lines) >= 2:
            cn = ass_escape(lines[0].strip())
            original = ass_escape(" ".join(line.strip() for line in lines[1:]))
            text = f"{cn}\\N{{\\fs{en_size}}}{original}"
        else:
            text = ass_escape(lines[0].strip())
        output.append(f"Dialogue: 0,{srt_time_to_ass(start)},{srt_time_to_ass(end)},Default,,0,0,0,,{text}")
    return "\n".join(output) + "\n"


def pick_sizes(height: int | None, cn_override: int | None = None, ratio: float = 1.7) -> tuple[int, int]:
    if cn_override:
        return cn_override, max(8, round(cn_override / ratio))
    key = min(SIZE_TABLE, key=lambda value: abs(value - (height or 720)))
    return SIZE_TABLE[key]


def detect_script(text: str) -> str:
    scripts = {"hangul": False, "arabic": False, "kana": False, "cjk": False}
    for char in text:
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            scripts["hangul"] = True
        elif 0x0600 <= code <= 0x06FF or 0x0750 <= code <= 0x077F:
            scripts["arabic"] = True
        elif 0x3040 <= code <= 0x30FF:
            scripts["kana"] = True
        elif 0x4E00 <= code <= 0x9FFF:
            scripts["cjk"] = True
    for script in ("hangul", "arabic", "kana", "cjk"):
        if scripts[script]:
            return script
    return "latin"


def pick_font_for_items(items: list[tuple[str, str, list[str]]], default: str = "PingFang SC") -> str:
    text = "".join("".join(lines) for _start, _end, lines in items)
    return SCRIPT_FONT.get(detect_script(text), default)


def self_check() -> int:
    sample = """1
00:00:00,000 --> 00:00:01,500
大家好
Hello {everyone}

2
00:00:01,500 --> 00:00:03,000
这是 API
This is an API
"""
    items = parse_srt(sample)
    ass = build_ass(items, 22, 13)
    assert "Dialogue: 0,0:00:00.00,0:00:01.50" in ass
    assert "Hello （everyone）" in ass
    try:
        parse_srt("1\n00:00:01,000 --> 00:00:00,500\n坏时间\nbad\n")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid time was accepted")
    print("self-check ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="双语 SRT -> 双语 ASS（目标语言大 / 原文小）")
    parser.add_argument("srt", nargs="?", help="双语 SRT 路径（目标语言在上、原文在下）")
    parser.add_argument("--output", "-o", help="输出 ASS 路径（默认同名 .ass）")
    parser.add_argument("--cn-size", type=int, default=None, help="目标语言字号（指定则覆盖默认表）")
    parser.add_argument("--en-size", type=int, default=None, help="原文字号（默认按目标语言 / 1.7）")
    parser.add_argument("--height", type=int, default=None, help="视频高度像素，用于选默认字号档")
    parser.add_argument("--font", default=None, help="字体名（默认按文字脚本自动选）")
    parser.add_argument("--marginv", type=int, default=16, help="底部边距（默认 16）")
    parser.add_argument("--self-check", action="store_true", help="运行本地自检")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    if not args.srt:
        parser.error("除非使用 --self-check，否则必须提供 srt")

    srt_path = Path(args.srt)
    if not srt_path.exists():
        print(f"错误：文件不存在 {srt_path}", file=sys.stderr)
        return 1

    try:
        items = parse_srt(srt_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    cn_size, en_size = pick_sizes(args.height, args.cn_size)
    if args.en_size:
        en_size = args.en_size
    font = args.font or pick_font_for_items(items)

    output_path = Path(args.output) if args.output else srt_path.with_suffix(".ass")
    output_path.write_text(build_ass(items, cn_size, en_size, font=font, marginv=args.marginv), encoding="utf-8")
    print(f"完成：{len(items)} 条 -> {output_path}（目标语言 {cn_size} / 原文 {en_size} / 字体 {font}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
