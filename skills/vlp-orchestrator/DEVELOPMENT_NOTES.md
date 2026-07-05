# vlp-orchestrator Development Notes

## 当前实现状态

- 总控 skill 已建立生产 `SKILL.md`。
- 目前只定义意图识别、run plan、路由和交接规则。
- 不执行完整 video language pipeline。

## 参考项目吸收点

- 参考 `xiaohu-video-translate` 的多技能分层思路。
- 保留一条龙入口体验，但不把下载、转写、翻译、烧录逻辑写进总控。

## 明确排除项

- 不实现下载逻辑。
- 不实现 ASR / transcription。
- 不实现翻译或润色。
- 不生成或烧录字幕。
- 不复制 child skill 内部步骤。

## 迁移原因

总控需要作为 suite 入口存在，但生产 `SKILL.md` 只能保存运行时路由规则。项目状态、阶段说明和参考来源放在本文件或根目录记录文档。

## 后续计划

- 在 child skills 具备可执行能力后，补充具体 manifest handoff 示例。
- 保持 child skills 独立可用。
