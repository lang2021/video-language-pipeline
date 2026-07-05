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
- 需要字幕渲染或烧录：说明该能力属于独立后续层，不在本 skill 内执行。
- 不支持的输入或平台：返回清晰的缺失能力说明，不临时把逻辑塞进 orchestrator。

## 工作流程

1. 明确用户输入、目标输出和已有文件路径。
2. 判断需要哪些 child skills。
3. 生成简短 run plan。
4. 调用或指引对应 child skill。
5. 汇总输出路径、manifest/log 路径、失败原因和下一步。

## 交接规则

- 跨 skill 交接使用结构化 manifest 或明确文件路径。
- 保留 child skill 的输出路径，不把关键结果只留在对话上下文。
- child skill 失败时，只汇总失败原因并指向 `manifest.json` / `run.log`。

## 禁止事项

- 不实现下载逻辑。
- 不实现 ASR / transcription 逻辑。
- 不实现翻译或润色逻辑。
- 不生成或烧录字幕。
- 不复制 child skill 的内部步骤。
- 不让 child skill 依赖 orchestrator 才能独立工作。
