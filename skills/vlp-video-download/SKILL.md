---
name: vlp-video-download
description: "Video Language Pipeline 的独立 media ingest skill。接收视频 URL 或本地媒体路径，完成下载或登记，并生成 manifest/log。"
---

# vlp-video-download

## 用途

`vlp-video-download` 负责把远程视频 URL 或本地媒体文件变成后续 pipeline 可交接的 media ingest 结果。

适用请求：

- “下载这个视频：`https://...`”
- “只下载这个链接的音频”
- “只下载这个视频的字幕”
- “把这个链接的视频保存到本地”
- “登记这个本地视频文件”
- “检查这个本地媒体文件并生成 manifest”

## 输入

- 视频 URL。
- 本地视频或音频文件路径。
- 可选 `mode`：`video`、`audio`、`subtitles`、`metadata`，默认 `video`。
- 可选 `sub_langs`，用于原始字幕下载。
- 可选 `output_dir`。
- 可选 `cookies_browser`。
- 可选 `proxy`。
- 可选 `format` / output template。
- 可选 `playlist_items`，用于 YouTube / Bilibili。
- 可选 `list` 模式，用于列出可下载资源。
- 可选 Douyin `resolution`。

## 输出

- 下载得到的视频、音频、原始字幕路径，或登记的本地媒体路径。
- `manifest.json`。
- `run.log`。
- 下载命令 attempts。
- selected site adapter。
- playlist/list/Douyin 相关 metadata。
- 可用时写入 `media_probe` 摘要。
- video mode 成功时会自动尝试下载平台原始字幕；字幕失败或不存在只写 warning，不让视频下载失败。
- audio mode 成功时写入音频文件路径、文件大小和可用的 `media_probe`。
- subtitles mode 成功时写入原始字幕文件列表和 `sub_langs`。

## 使用方式

从本 skill 目录运行：

```bash
python3 scripts/media_ingest.py "<video-url-or-local-file>"
```

常用命令：

```bash
python3 scripts/media_ingest.py "<video-url>" --output-dir "/absolute/output/root"
python3 scripts/media_ingest.py "<video-url>" --cookies-browser "chrome:Default"
python3 scripts/media_ingest.py "<video-url>" --proxy "http://127.0.0.1:7890"
python3 scripts/media_ingest.py "<video-url>" --format "best[ext=mp4]/best"
python3 scripts/media_ingest.py "<video-url>" --mode audio
python3 scripts/media_ingest.py "<video-url>" --mode subtitles --sub-langs "en,zh-Hans"
python3 scripts/media_ingest.py "<video-url>" --mode metadata
python3 scripts/media_ingest.py "<youtube-or-bilibili-url>" --playlist-items "1:5"
python3 scripts/media_ingest.py "<youtube-or-bilibili-url>" --list
python3 scripts/douyin_login.py
python3 scripts/douyin_download.py "<douyin-url>" --list
python3 scripts/douyin_download.py "<douyin-url>" --resolution "1080p"
python3 scripts/media_ingest.py --self-check
```

如果没有传入 `--output-dir`，输出写入 suite 本地的 `runs/` 目录。

## 下载路由

- YouTube URL 使用 YouTube adapter。
- Bilibili URL 使用 Bilibili adapter。
- Douyin URL 使用 Douyin adapter。
- 其它 URL 使用 generic `yt-dlp` adapter。
- 本地文件不进入 URL adapter，只登记绝对路径。
- `video` mode 下载视频文件；YouTube / Bilibili / generic `yt-dlp` adapter 在视频成功后自动尝试下载平台原始字幕。
- `audio` mode 只下载音频文件，不做 ASR。
- `subtitles` mode 只下载平台提供的原始字幕，不翻译、不清洗、不双语排版。
- `metadata` mode 只做资源信息读取，不下载媒体。
- Douyin 暂不支持 subtitles mode，也不在 video mode 后自动尝试字幕；如果 aweme detail 中没有 `audio_url`，audio mode 会失败并写入 manifest/log。

## 失败处理

- 缺少 `yt-dlp` 时，不自动安装；返回可执行提示并写入 manifest/log。
- 缺少 `ffprobe` 或 probe 失败时，只写 warning，不把已成功的下载/登记改成失败。
- `subtitles` mode 没有字幕文件时，不伪造字幕；记录失败。
- `video` mode 的自动字幕尝试失败或没有字幕文件时，只记录 warning、attempts 和 `run.log`，不影响已下载视频。
- 命令被执行过时，保留原始输出到 `run.log`。
- 用户可根据 `manifest.json` 和 `run.log` 继续排查。

## 禁止事项

- 不做 transcription。
- 不做翻译或润色。
- 不清洗、改写、翻译或双语排版字幕。
- 不生成渲染用 `ASS` / `SRT`；字幕相关下载只保存平台返回的原始字幕文件。
- 不烧录字幕。
- 不把平台特殊逻辑混进 generic adapter；新增网站支持必须进入独立 adapter。
- 不依赖 `vlp-orchestrator` 才能运行。
