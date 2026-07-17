# vlp-translation-polish scripts

这个目录保存 `vlp-translation-polish` 的轻量脚本。

## html_translation_nodes.py

把已离线化的 `index.html` 提取为可编辑 JSON，再从原 source 确定性回填 `index.zh.html`：

```bash
python3 html_translation_nodes.py extract index.html --bundle translation.json --target-lang zh-CN
# 只填写 translation.json 中各 unit 的 target 字段
python3 html_translation_nodes.py merge index.html --bundle translation.json --semantic-report translation-lint.json
python3 html_translation_nodes.py merge index.html --bundle translation.json --output <derived>/index.zh.html --asset-root <mirror-root>
python3 html_translation_nodes.py --self-check
```

约定：

- 不翻译、不调用模型，也不抓取网页。
- source hash、unit ID、顺序、context 和 source 都不可修改。
- `merge` 拒绝空 target、source 漂移和默认覆盖，验证通过后才原子写入 `index.zh.html`。
- 未指定 `--output` 时保持同目录输出；独立 output 只重写本地资源的相对路径，共享 `--asset-root`，不复制资源。
- `merge` 先执行结构验证，再输出不阻断的语义 lint 摘要；`--semantic-report` 可保存 JSON warning 清单。
- JSON bundle 是临时翻译工作资产；大批次状态仍只写入 per-run manifest。

## validate_html_translation.py

校验静态网页镜像译文是否保留 HTML 结构、受保护属性和本地资源：

```bash
python3 validate_html_translation.py index.html index.zh.html
python3 validate_html_translation.py index.html index.zh.html --semantic-lint --semantic-report translation-lint.json
python3 validate_html_translation.py index.html <derived>/index.zh.html --asset-root <mirror-root>
python3 validate_html_translation.py --self-check
```

约定：

- 默认 source 与译文同目录；独立输出模式用 `--asset-root` 校验 source 和 target 是否解析到同一实际资源。
- 允许翻译可见文本与必要的可见 UI 属性；普通链接、脚本、代码和非资源 CSS 保持不变。
- 校验本地 `src`、`srcset`、`poster`、资源 `href`、`object[data]`、CSS `url(...)` 等资源存在且不越过 asset root。
- `--semantic-lint` 只读检查可见文本单元数量、长英文原样保留、短 source 异常膨胀和长 source 异常缩短；warning 不改变机械校验结果。
- 不翻译、不润色、不做网页抓取或浏览器渲染验收。

## render_translation_queue.py

从 schema v3 batch manifest 生成唯一的 Markdown 队列视图：

```bash
python3 render_translation_queue.py --manifest manifest.json --output queue.md
python3 render_translation_queue.py --self-check
```

- manifest 是状态真相；每个 item 记录 output、逐项状态、机械结构/资源校验、内容覆盖、语义 lint、表达复核、warnings 和更新时间。
- `queue.md` 是生成物，不应手工编辑，也不维护第二套 Ready / Done 条目。
- 不翻译、不抓取网页、不调用模型，也不修改 manifest。

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
