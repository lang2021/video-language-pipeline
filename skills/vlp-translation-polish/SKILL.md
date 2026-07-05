---
name: vlp-translation-polish
description: "Video Language Pipeline 的 agent-guided 语言转换与润色 skill。处理 Markdown、纯文本、transcript、SRT/VTT 字幕、字幕片段和用户直接粘贴的文本。"
---

# vlp-translation-polish

## 用途

`vlp-translation-polish` 处理已经是文字形态的内容。

适用输入：

- Markdown 文稿。
- 纯文本。
- transcript 转写稿。
- SRT / VTT 字幕。
- 字幕片段。
- 用户直接粘贴的文本。

不处理：

- 视频下载。
- 音频提取。
- Whisper / ASR 转写。
- 视频编码。
- 字幕烧录。

## 使用方式

本 skill 优先由 agent 根据文本内容、用户意图和下列规则执行翻译或润色。不要为了普通翻译任务创建自动化翻译 CLI。

脚本只作为辅助工具使用。当前可用脚本示例：

- `scripts/bilingual_ass.py`：把已经生成的双语 SRT 转成 ASS 文本资产。
- `scripts/validate_markdown_translation.py`：校验 Markdown 译文是否保留 URL 和基础结构。

## 默认翻译原则

- 忠实翻译。
- 完整翻译，不漏翻。
- 不私自压缩。
- 不擅自总结。
- 不随意改写结构。
- 保留原文段落、标题和顺序。
- 保留链接、数据、代码块、路径、命令和 API 名称。
- 保留关键英文术语。
- 关键英文术语首次出现时，可添加中文括号解释。
- 不改变作者立场。
- 不文学化重写，除非用户明确要求。

用户明确给出 style policy 时，在不破坏忠实性和格式的前提下应用。

## 术语与一致性

- 识别当前任务中的关键术语、人名、公司名、产品名和技术名词。
- 同一个概念在同一任务中尽量保持同一译法。
- 用户提供 glossary 时，用户 glossary 优先。
- 技术术语优先保留英文原词，例如 `API`、`GPU`、`AI`、`ASR`。
- 英文与中文混排时，中英文之间保留一个英文空格。
- 不常见术语首次出现时，可加简短中文解释。

术语记录是当前任务内状态，不是长期用户记忆。

## 格式保持

翻译内容，但不要破坏原始格式。

- Markdown：保留标题、列表、链接、图片占位、代码块、表格和 front matter。
- SRT：保留序号、时间轴和字幕块结构。
- VTT：保留 `WEBVTT` header、cue block 和时间轴。
- 纯文本：保留段落、空行和顺序。

代码块、命令、路径、环境变量、API 名称默认不翻译。

Markdown 翻译必须逐字保留所有 Markdown link URL、image URL、raw autolink、代码块、路径、命令和结构性内容。翻译 Markdown 文件后必须运行：

```bash
python3 scripts/validate_markdown_translation.py <source.md> <translated.md>
```

如果校验失败，先修复 URL 或结构问题，再交付。不要依赖肉眼检查长 URL。

## 长文本处理

长文、transcript 和字幕可以由 agent 分段处理。

- 保持语义完整。
- 不把一个完整意思切碎。
- 尽量按标题、段落、说话轮次、字幕块或自然语义边界处理。
- 保持原文顺序。
- 使用当前任务上下文维持术语和语义连续性。

这不要求实现自动 chunking 工具。

## 字幕规则

适用于 SRT、VTT、timestamped transcript 或字幕风格文本。

- 不随意提前 start time。
- 不合并相邻字幕条，除非用户明确要求。
- 可以把过长字幕拆短；拆分后的时间必须仍在原条目范围内。
- 拆分后编号必须连续。
- 不允许时间戳重叠。
- 每条字幕以单行为主，必要时两行，避免三行以上。
- 中文单行建议不超过 12 到 16 个中文字符；技术内容可略放宽。
- 在语义自然处断句，不拆开固定短语。
- 短条可以保留，短条通常比长条更好读。

## 输出

根据用户请求和输入格式输出对应内容。

常见输出：

- translated Markdown。
- bilingual Markdown。
- translated text。
- translated SRT / VTT。
- bilingual SRT / VTT。
- task-local glossary notes。

SRT 输出格式：

```text
1
00:00:00,000 --> 00:00:03,500
这是第一条字幕

2
00:00:03,500 --> 00:00:07,200
这是第二条字幕
```

双语 SRT 输出结构：

```text
1
00:00:19,239 --> 00:00:21,239
大家好吗
Hello everyone, how are you?
```

如需将已生成的双语 SRT 转成 ASS 文本资产，可运行 `scripts/bilingual_ass.py`。本 skill 不烧录视频。

## Manifest 与调试输出

manifest 适合 pipeline 交接，但不是每个临时粘贴文本任务的强制负担。

需要跨 skill 交接时，manifest 可记录：

- input type。
- input path 或 input summary。
- target language。
- output paths。
- status。
- errors。
- warnings。

debug / report / log 不作为默认用户体验。仅在测试、排查或用户明确要求时保留，例如 `run.log`、`polish_report.md`、`quality_report.md`。

## 禁止事项

- 不做 user profile layer。
- 不保存 long-term memory。
- 不默认实现自动翻译 CLI。
- 不默认实现自动 glossary extractor。
- 不默认实现全自动 quality reviewer。
- 不下载视频。
- 不提取音频。
- 不运行 Whisper / ASR。
- 不修改音视频文件。
- 不烧录字幕。
- 不依赖 `vlp-orchestrator` 才能独立工作。
