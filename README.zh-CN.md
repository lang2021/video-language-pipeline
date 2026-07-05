# Video Language Pipeline

语言：[English](README.md) | 简体中文

Video Language Pipeline 是一个 agent-first 的多技能视频语言处理套件。

它不是单一 CLI 产品。主要接口是给 Codex 或其他 agent 读取和执行的 `SKILL.md` 文件。脚本只用于确定性强的环节，例如媒体导入、转写和字幕格式辅助。

## 能做什么

- 下载或登记视频/音频资产。
- 从本地媒体生成 SRT/TXT 转写稿。
- 翻译和润色文字资产、transcript、SRT/VTT 字幕、Markdown 和粘贴文本。
- 生成翻译字幕或双语字幕文本资产。
- 通过 manifest、log 和明确文件路径保留交接证据。

当前套件停在文本资产层，不做字幕渲染或烧录。

## 技能组成

| Skill | 职责 |
|---|---|
| `vlp-orchestrator` | 编排完整流程，在各 child skill 之间做交接。 |
| `vlp-video-download` | 下载 URL、登记本地媒体，并写入 manifest / log。 |
| `vlp-speech-transcribe` | 把本地音视频转换成 SRT/TXT 转写资产。 |
| `vlp-translation-polish` | 由 agent 执行翻译、字幕发布级润色、术语统一和格式保持。 |

可调用 skill 位于：

```text
skills/<skill-name>/SKILL.md
```

项目根目录故意没有 `SKILL.md`。

## 默认流程

完整的视频到双语字幕任务从 `vlp-orchestrator` 开始：

```text
vlp-video-download
  -> vlp-speech-transcribe
  -> vlp-translation-polish
  -> translated or bilingual SRT/VTT
```

“下载双语字幕”或“生成双语 SRT”这类请求会被理解为完整 pipeline 产物请求，不会默认走平台原始字幕下载。

如果视频没有平台字幕，并且 ASR 结果没有有效语音内容，总控应安全停止，不伪造字幕。

## 命令辅助工具

在对应 skill 目录下运行命令。

媒体导入：

```bash
python3 scripts/media_ingest.py "<video-url-or-local-file>"
python3 scripts/media_ingest.py "<video-url>" --mode audio
python3 scripts/media_ingest.py "<video-url>" --mode subtitles --sub-langs "en,zh-Hans"
python3 scripts/media_ingest.py --self-check
```

语音转写：

```bash
python3 scripts/transcribe_srt.py "<local-audio-or-video>"
python3 scripts/transcribe_srt.py "<media-ingest-manifest.json>"
python3 scripts/transcribe_srt.py --self-check
```

翻译辅助：

```bash
python3 scripts/validate_markdown_translation.py <source.md> <translated.md>
python3 scripts/bilingual_ass.py <bilingual.srt>
```

## 依赖

- Python 3。
- `yt-dlp`，用于 URL 下载。
- `ffmpeg` 和 `ffprobe`，用于媒体探测和音频提取。
- `mlx-whisper` 或 `faster-whisper`，用于本地 ASR 转写。

脚本不会自动安装外部工具。

## 边界

- `vlp-video-download` 不转写、不翻译、不润色、不渲染、不烧录字幕。
- `vlp-speech-transcribe` 不下载远程 URL，也不翻译文本。
- `vlp-translation-polish` 是 agent-guided，不提供完整自动翻译 runner。
- `vlp-orchestrator` 只编排 child skills，不复制它们的内部逻辑。

生成的 runs、日志、本地 agent 记录和开发过程文档不会进入公开发布。
