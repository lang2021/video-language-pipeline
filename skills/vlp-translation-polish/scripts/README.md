# vlp-translation-polish scripts

这个目录保存 `vlp-translation-polish` 的轻量脚本。

## validate_markdown_translation.py

校验 Markdown 译文是否保留 URL 和基础结构：

```bash
python3 validate_markdown_translation.py <source.md> <translated.md>
python3 validate_markdown_translation.py --self-check
```

检查内容：

- Markdown inline links / images 的 URL。
- raw autolinks：`<https://...>` / `<http://...>`。
- YAML front matter keys。
- heading level sequence。
- fenced code block count。

当前边界：

- 不翻译。
- 不润色。
- 不做完整 Markdown parser。
- 不支持 reference-style links；出现真实失败案例时再加。

## bilingual_ass.py

把已经生成的双语 SRT 转成双语 ASS：

```bash
python3 bilingual_ass.py <双语SRT> --output <双语ASS>
python3 bilingual_ass.py <双语SRT> --cn-size 24
python3 bilingual_ass.py <双语SRT> --height 1080
python3 bilingual_ass.py --self-check
```

输入约定：

- 每条字幕至少一行目标语言文本。
- 双语模式下，第一行是目标语言，第二行及之后合并为原文。
- 时间戳必须递增，不能重叠。

当前边界：

- 不翻译。
- 不润色。
- 不调用模型。
- 不烧录视频。
- 只生成 ASS 字幕资产，交给未来 render / burn-in 层使用。
