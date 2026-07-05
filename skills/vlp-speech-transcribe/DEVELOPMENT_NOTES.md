# vlp-speech-transcribe Development Notes

## 当前实现状态

- 已建立生产 `SKILL.md`。
- 已新增最小转写脚本：`scripts/transcribe_srt.py`。
- 支持本地 audio/video 和 media ingest manifest。
- video 输入通过 `ffmpeg` 提取 16k mono WAV。
- ASR 路径为 `mlx-whisper` 优先、`faster-whisper` 兜底。
- 输出 SRT、TXT、`manifest.json` 和 `run.log`。

## 参考项目吸收点

- 从 `xiaohu-video-translate` 的流程中拆出独立 speech transcribe 层。
- 转写不应藏在 download skill 或 translation skill 内。
- 保留 `transcribe_srt.py` 的 word-level timestamps 分段思路。
- 保留句末标点、停顿、最大时长、重复段清理和时间重叠修正。
- 保留 `--language` 作为语种误判时的强制重转参数。

## 明确排除项

- 不下载远程 URL。
- 不翻译。
- 不润色。
- 不做双语排版。
- 不渲染或烧录字幕。
- 不自动安装依赖。
- 不实现 `whisper-cli` fallback。

## 迁移原因

语音转文字和文字翻译是不同层。把 ASR 独立出来，可以避免字幕翻译规则、下载逻辑和转写引擎互相耦合。

## 后续计划

- 用真实本地媒体测试 MLX/faster 输出。
- 视实际失败情况决定是否加入 `whisper-cli` 纯文本 fallback。
- 如后续需要 Markdown，由 `vlp-translation-polish` 或单独文稿层处理。
