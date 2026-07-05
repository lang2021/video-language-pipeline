# vlp-video-download scripts

这个目录保存 `vlp-video-download` 的 media ingest 实现。脚本只处理视频下载、音频下载、原始字幕下载、本地媒体登记和 metadata 读取，不处理转写、翻译、字幕润色或烧录。

## 文件分工

- `media_ingest.py`：CLI 入口，负责参数解析、`--self-check` 和 URL/local 分发。
- `common.py`：公共工具，负责配置读取、路径解析、时间戳、URL 判断和默认 `yt-dlp` format selector。
- `media_probe.py`：可选 `ffprobe` 摘要层，记录 duration、container、codec、width/height 和音视频流存在性。
- `run_record.py`：运行记录层，负责创建 run 目录、写入 `run.log` 和 `manifest.json`。
- `local_ingest.py`：本地文件登记层，只检查文件存在并记录路径，不复制大文件。
- `url_download.py`：URL 下载分发层，按 URL host 选择 site adapter。
- `youtube_download.py`：YouTube 下载直接入口，复用统一 run record 和 adapter 分发。
- `bilibili_download.py`：Bilibili 下载直接入口，复用统一 run record 和 adapter 分发。
- `douyin_download.py`：Douyin 下载直接入口，支持资源列表和视频下载。
- `douyin_login.py`：Douyin 登录态准备入口。
- `site_downloaders/generic.py`：通用 `yt-dlp` adapter，覆盖未单独适配的网站。
- `site_downloaders/youtube.py`：YouTube adapter，加入 YouTube 独立下载策略。
- `site_downloaders/bilibili.py`：Bilibili adapter，支持单视频和显式 playlist/合集/分P。
- `site_downloaders/douyin.py`：Douyin adapter，使用可见 Chrome 抓取 `aweme detail` 后下载视频；如果存在 `audio_url`，支持 audio mode。
- `site_downloaders/__init__.py`：site adapter registry。

## 基本用法

```bash
python3 media_ingest.py "<video-url-or-local-file>"
python3 media_ingest.py "<video-url>" --output-dir "/absolute/output/root"
python3 media_ingest.py "<video-url>" --cookies-browser "chrome:Default"
python3 media_ingest.py "<video-url>" --proxy "http://127.0.0.1:7890"
python3 media_ingest.py "<video-url>" --force-cookies
python3 media_ingest.py "<video-url>" --no-cookies-fallback
python3 media_ingest.py "<video-url>" --mode audio
python3 media_ingest.py "<video-url>" --mode subtitles --sub-langs "en,zh-Hans"
python3 media_ingest.py "<video-url>" --mode metadata
python3 youtube_download.py "<youtube-url>" --cookies-browser "chrome:Default"
python3 youtube_download.py "<youtube-playlist-url>" --playlist-items "1:5"
python3 bilibili_download.py "<bilibili-url>" --playlist-items "all"
python3 douyin_login.py
python3 douyin_download.py "<douyin-url>" --list
python3 douyin_download.py "<douyin-url>" --resolution "1080p"
python3 media_ingest.py --self-check
```

## 当前行为

- URL 输入使用 `yt-dlp`。
- YouTube URL 会进入 `site_downloaders/youtube.py`。
- Bilibili URL 会进入 `site_downloaders/bilibili.py`。
- Douyin URL 会进入 `site_downloaders/douyin.py`。
- 其他 URL 默认进入 `site_downloaders/generic.py`。
- 默认使用 H.264 优先的 MP4 format selector。
- URL 下载先无 cookies 尝试，失败后按配置尝试 browser cookies fallback。
- `--mode video` 下载视频，是默认模式；YouTube / Bilibili / generic `yt-dlp` adapter 会在视频成功后自动尝试下载平台原始字幕。
- `--mode audio` 使用 `yt-dlp -x --audio-format mp3` 下载音频，不做转写。
- `--mode subtitles` 使用 `yt-dlp --skip-download --write-subs --write-auto-subs` 下载原始字幕，不下载视频。
- `--sub-langs` 传给 `yt-dlp --sub-langs`，默认 `zh-Hans,zh-CN,en,ja`。
- `--mode metadata` 或 `--list` 只读取资源信息，不下载媒体文件。
- YouTube/Bilibili 只有显式传入 `--playlist-items` 时才下载 playlist/合集/分P。
- Douyin 需要先用 `douyin_login.py` 准备本地登录态；Douyin subtitles mode 暂不支持，video mode 后也不会自动尝试字幕。
- 本地文件输入只检查文件是否存在，并登记其绝对路径。
- 下载或本地登记成功后会尝试运行 `ffprobe`，将摘要写入 `manifest.json`；`ffprobe` 缺失或失败只写 warning。
- 每次运行创建独立 run 目录。
- 每次运行尽量写入 `manifest.json` 和 `run.log`。

## 当前边界

这些脚本必须保持 media ingest 范围。字幕相关逻辑只保存平台返回的原始字幕文件；不要在这里实现 transcription、translation、subtitle polish、双语字幕、字幕清洗、`ASS` / `SRT` generation 或 burn-in。
