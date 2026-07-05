---
name: vlp-speech-transcribe
description: "Video Language Pipeline 的语音转文字 skill。把本地视频或音频转换为 transcript、字幕文本或其他可继续处理的文字资产。"
---

# vlp-speech-transcribe

## 用途

`vlp-speech-transcribe` 负责把本地视频或音频转换为文字资产，供后续 `vlp-translation-polish` 处理。

适用请求：

- “转写这个本地视频”
- “把这个音频变成 transcript”
- “从这个视频生成带时间戳的文字”
- “把上一步下载的媒体转成可翻译文本”

## 输入

- 本地视频路径。
- 本地音频路径。
- 可选 media ingest manifest。
- 可选 source language hint。
- 可选转写质量或时间戳粒度偏好。

## 输出

- `<input-media-stem>.srt`，或 `--output <name>` 指定的 `<name>.srt`。
- `<input-media-stem>.txt`，或 `--output <name>` 指定的 `<name>.txt`。
- transcription metadata。
- `manifest.json`。
- `run.log`。

## 使用方式

从本 skill 目录运行：

```bash
python3 scripts/transcribe_srt.py "<local-audio-or-video>"
```

常用参数：

```bash
python3 scripts/transcribe_srt.py "<local-media>" --output-dir "/absolute/output/root"
python3 scripts/transcribe_srt.py "<local-media>" --output "talk"
python3 scripts/transcribe_srt.py "<local-media>" --engine auto
python3 scripts/transcribe_srt.py "<local-media>" --engine mlx
python3 scripts/transcribe_srt.py "<local-media>" --engine faster
python3 scripts/transcribe_srt.py "<local-media>" --language en
python3 scripts/transcribe_srt.py "<local-media>" --max-line-ms 6000 --pause-ms 500
python3 scripts/transcribe_srt.py "<media-ingest-manifest.json>"
python3 scripts/transcribe_srt.py --self-check
```

如果没有传入 `--output-dir`，输出写入 suite 本地的 `runs/` 目录。
如果没有传入 `--output`，SRT/TXT 文件名使用输入媒体文件的 filename stem；manifest 输入则使用 manifest 指向的媒体文件 stem。

## 工作规则

- 只处理本地媒体文件，不处理远程 URL。
- 本地视频先用 `ffmpeg` 提取 16k mono WAV，再转写。
- 本地音频直接进入 ASR。
- 默认 `--engine auto` 先尝试 `mlx-whisper`，再尝试 `faster-whisper`。
- 如果没有可执行 ASR 路径或必要依赖，写入 failed manifest/log，并说明缺失能力。
- 输出必须保留文件路径或 manifest，不把 transcript 只留在对话上下文。
- 生成带时间戳文本时，保留原始时间顺序，不臆造未识别内容。

## 禁止事项

- 不下载视频。
- 不处理远程 URL。
- 不翻译。
- 不润色。
- 不做双语排版。
- 不渲染或烧录字幕。
- 不依赖 `vlp-orchestrator` 才能独立工作。
