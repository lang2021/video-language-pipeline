# vlp-speech-transcribe scripts

这个目录保存 `vlp-speech-transcribe` 的本地转写脚本。

## transcribe_srt.py

把本地 audio/video 或 media ingest manifest 转成 SRT/TXT：

```bash
python3 transcribe_srt.py "<local-audio-or-video>"
python3 transcribe_srt.py "<local-media>" --output-dir "/absolute/output/root"
python3 transcribe_srt.py "<local-media>" --output "talk"
python3 transcribe_srt.py "<local-media>" --engine auto
python3 transcribe_srt.py "<local-media>" --language en
python3 transcribe_srt.py "<media-ingest-manifest.json>"
python3 transcribe_srt.py --self-check
```

输出：

- `runs/<job_id>/<name>.srt`
- `runs/<job_id>/<name>.txt`
- `runs/<job_id>/manifest.json`
- `runs/<job_id>/run.log`

当前边界：

- 不下载。
- 不翻译。
- 不烧录字幕。
- 不自动安装依赖。
- 不实现 `whisper-cli` fallback。
