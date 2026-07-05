# vlp-video-download Development Notes

## 当前实现状态

- 这是当前 suite 的 active implementation layer。
- 已支持本地媒体登记和 URL 下载。
- URL 下载按 site adapter 分层：generic `yt-dlp`、YouTube、Bilibili、Douyin。
- 已有 `manifest.json`、`run.log`、attempt records 和可选 `media_probe`。
- 已支持 `--mode video|audio|subtitles|metadata`。
- audio mode 只下载音频，不做 ASR。
- subtitles mode 只下载平台原始字幕，不做清洗、翻译、双语排版或渲染。
- Douyin 依赖本地 Chrome login profile。

## 参考项目吸收点

- 从 `xiaohu-video-download` 吸收下载层经验，而不是复制完整 pipeline。
- 保留 H.264 优先 MP4 format selector。
- 保留 retry、fragment retry、resume、clean filename。
- 保留 browser cookies fallback 和 explicit proxy。
- 保留按网站拆分 adapter / script 的边界。
- 当前明确平台集来自参考项目：YouTube、Bilibili、Douyin、generic `yt-dlp`。

## 明确排除项

- 不做 transcription。
- 不做翻译或润色。
- 不清洗、改写、翻译或双语排版字幕。
- 不生成渲染用 `ASS` / `SRT`；只允许 subtitle mode 保存平台返回的原始字幕文件。
- 不烧录字幕。
- 不做 Douyin both mode。
- 不加入未验证的 Reddit / `v.redd.it` adapter。

## 迁移原因

生产 `SKILL.md` 只应描述 media ingest 的使用方式和运行边界。参考项目来源、阶段状态、平台取舍和实现路线放在本文件，避免污染生产 skill prompt。

## 后续计划

- 对 YouTube、Bilibili、Douyin 做真实 URL smoke test。
- 对 YouTube/Bilibili 的 audio/subtitles mode 做真实 URL smoke test。
- 只有出现具体失败 URL 或明确平台需求时再新增 adapter。
