# vlp-translation-polish Development Notes

## 当前实现状态

- 已从 `xiaohu-subtitle-polish` 迁入核心文字翻译/润色规则。
- 已改造成更宽的 text asset skill，覆盖 transcript、subtitle text、Markdown 和 plain text。
- 已保留并硬化 `scripts/bilingual_ass.py`，用于 bilingual SRT -> ASS text-asset conversion。
- 已添加 `scripts/validate_markdown_translation.py`，用于 Markdown 翻译后的 URL / 基础结构校验。
- 当前保持 agent-first, tool-light，不实现默认 translation/polish CLI。
- 生产 `SKILL.md` 已重新校准为 agent 使用说明，而不是自动化 CLI pipeline 规格。

## 参考项目吸收点

- ASR 文本常见同音、近音、专有名词和缩写错误，翻译前需要修正。
- 字幕文本需要短句、少堆叠、可读。
- 专有名词、产品名、公司名和技术术语优先保留英文或通行名称。
- 英文与中文混排时保留空格。
- 字幕模式下，“可以拆，不可以合”通常更稳。
- 双语字幕需要目标语言主导、原文辅助。
- 双语 SRT 需要不同字号时，应转成 ASS 文本资产，而不是依赖 SRT inline style。

## 明确排除项

- Whisper `-ml 50` 重转写。
- ffmpeg `silencedetect`。
- 字幕烧录命令。
- drawtext / watermark。
- 下载 skill 的内部路径依赖。
- 把下载、转写、翻译、排版、烧录写在一个 skill 里。

## 迁移原因

原参考 skill 是 subtitle-focused，并混有转写、静音检测、烧录和 video-download 联动说明。当前 suite 已拆成四层，因此生产 `SKILL.md` 只保留文字资产翻译/润色的运行规则；迁移依据和取舍放在本文件。

## 后续计划

- 保持 agent-first skill instructions 为主。
- 仅在具体任务证明有价值时，增加小型 deterministic helpers。
- 可选 helper 候选：Markdown/SRT/VTT 格式检查、manifest 辅助生成、术语清单整理。
- Markdown 校验 helper 当前不支持 reference-style links；出现真实失败案例时再加。
- 不默认实现自动翻译 CLI、自动 glossary extractor、全自动 quality reviewer 或大型 parser layer。
