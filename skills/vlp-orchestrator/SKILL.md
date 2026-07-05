---
name: vlp-orchestrator
description: "Video Language Pipeline suite 的总控 skill。负责识别用户意图、创建 run plan、路由 child skill、传递结构化 manifest，并汇总输出结果。"
---

# vlp-orchestrator

## 用途

`vlp-orchestrator` 是 Video Language Pipeline 的总控入口。用户提出完整或不明确的视频语言处理请求时，先使用本 skill 判断意图、拆分任务、选择 child skill，并汇总结果。

适用请求：

- “处理这个视频”
- “下载并准备这个视频”
- “把这个视频变成翻译字幕”
- “运行 video language pipeline”

## 路由规则

- URL 下载或本地媒体登记：交给 `vlp-video-download`。
- 本地视频或音频转写：交给 `vlp-speech-transcribe`，或在没有可执行转写路径时说明缺失能力。
- 已有文稿、transcript、字幕文本或 Markdown 翻译润色：交给 `vlp-translation-polish`。
- 用户说“下载双语字幕”、“生成双语 SRT”或“视频转双语字幕”时，按双语字幕产物理解，默认走完整流程，不要机械映射到 `vlp-video-download --mode subtitles`。
- 需要字幕渲染或烧录：说明该能力属于独立后续层，不在本 skill 内执行。
- 不支持的输入或平台：返回清晰的缺失能力说明，不临时把逻辑塞进 orchestrator。

## 默认完整流程

完整视频到翻译字幕任务默认按以下顺序编排：

```text
vlp-video-download
  -> vlp-speech-transcribe
  -> vlp-translation-polish
```

阶段职责：

1. `vlp-video-download`：下载 URL 或登记本地媒体，输出 media path、`manifest.json` 和 `run.log`。
2. `vlp-speech-transcribe`：把本地视频或音频转成 source SRT/TXT，输出 transcription manifest 和 `run.log`。
3. `vlp-translation-polish`：把 source SRT/TXT 翻译成目标语言字幕；字幕输出默认经过发布级 polish pass。

默认交付终点是字幕文本资产，例如 translated SRT/VTT 或 bilingual SRT/VTT。当前 suite 不做 render、burn-in 或视频编码。

双语字幕请求默认保留视频本体：

1. 先用 `vlp-video-download` 的默认 `video` mode 下载视频；video mode 会 best-effort 尝试下载平台原始字幕。
2. 如果平台原始字幕可用，可把它作为 source text asset 交给 `vlp-translation-polish`。
3. 如果平台原始字幕不可用，再用 `vlp-speech-transcribe` 从媒体生成 source SRT/TXT。
4. `vlp-video-download --mode subtitles` 只用于用户明确要求“只下载平台原始字幕”、“只要字幕文件”或“不下载视频”的情况。

## 最小分支

- 用户只要求下载、登记或 metadata：只使用 `vlp-video-download`。
- 用户提供本地视频或音频并要求转写：可以直接使用 `vlp-speech-transcribe`，不必先登记媒体。
- 用户已有 SRT、VTT、transcript、Markdown 或纯文本：直接使用 `vlp-translation-polish`。
- 用户明确要求使用平台原始字幕：可跳过 ASR，把 `vlp-video-download` 得到的原始字幕作为 text asset 交给 `vlp-translation-polish`。
- 用户明确要求“只下载平台原始字幕”、“只要字幕文件”或“不下载视频”：才使用 `vlp-video-download --mode subtitles`。
- 用户要求 burn-in、render 或视频编码：说明当前 suite 不执行，停在字幕文本资产。

## No-speech gate

完整视频到字幕任务必须先判断是否有可翻译的语言内容。宣传片、游戏画面、风景片、音乐或环境声为主的视频，可能没有有效旁白。

- 平台字幕不可用且素材疑似无旁白时，先提示“可能无法生成语言字幕”。
- 如果已跑 ASR，但结果只有 `Erm`、`Thank you`、重复填充词、极少文本或长时间空白，判定为 no-speech / low-speech。
- no-speech / low-speech 时停止 pipeline，不进入 `vlp-translation-polish`。
- 不伪造 transcript、translated subtitle 或 bilingual subtitle。
- ASR 长时间无有效输出或卡死时，应终止或建议终止，避免后台残留。

停止时汇总：

- 已生成的 media / audio 文件。
- 已生成的 `manifest.json` 和 `run.log`。
- 平台字幕不可用或 ASR 低语音密度的原因。
- 下一步建议：换有旁白或有字幕的视频，或提供人工文稿。

## 工作流程

1. 明确用户输入、目标输出和已有文件路径。
2. 判断需要哪些 child skills。
3. 生成简短 run plan。
4. 调用或指引对应 child skill。
5. 汇总输出路径、manifest/log 路径、失败原因和下一步。

run plan 至少说明：

- 输入类型：URL、本地媒体、已有字幕、已有文稿或粘贴文本。
- 目标输出：source transcript、translated subtitles、bilingual subtitles、Markdown/text translation 等。
- 将使用的 child skills。
- 每一步的交接文件：media path、source SRT/TXT、translated/bilingual SRT/VTT、manifest/log。
- 当前不支持的终点，例如 burn-in。

## 交接规则

- 跨 skill 交接使用结构化 manifest 或明确文件路径。
- 保留 child skill 的输出路径，不把关键结果只留在对话上下文。
- child skill 失败时，只汇总失败原因并指向 `manifest.json` / `run.log`。
- 每一步成功后，把下一步需要的实际文件路径交给对应 child skill。
- 最终回复列出 media、source SRT/TXT、translated/bilingual SRT/VTT、manifest/log 路径；不存在的产物不要伪造。

## 禁止事项

- 不实现下载逻辑。
- 不实现 ASR / transcription 逻辑。
- 不实现翻译或润色逻辑。
- 不生成或烧录字幕。
- 不复制 child skill 的内部步骤。
- 不让 child skill 依赖 orchestrator 才能独立工作。
