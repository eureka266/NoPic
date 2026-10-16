# 模板名称与可保存的排版参数

现已实现模板参数文件、项目内模板副本和单图位置覆盖；localhost 微调页面尚未实现。默认由 agent 使用这些文件出图，运营与 COO 无需编辑 JSON。

## 模板命名

模板统一使用“图片用途 + 版式”的英文 ID / 文件名，并提供中文显示名。旧 `layout` 字段保留，已有配置可继续使用；`template_id` 让人和工具明确识别具体模板。目录索引为 [assets/templates/index.json](../assets/templates/index.json)。

| 中文显示名 | 模板 ID / 文件名（加 .json） | 兼容的 layout |
| --- | --- | --- |
| 文章封面｜横版 | article-cover-landscape | hero |
| 合作公告｜左对齐横版 | partnership-announcement-left | partnership |
| 合作公告｜居中横版 | partnership-announcement-centered | partnership-centered |
| 合作公告｜极简双 Logo 横版 | partnership-announcement-minimal | partnership-minimal |
| 观点人物卡｜横版 | opinion-card-landscape | quote |
| 嘉宾金句｜竖版 | speaker-quote-portrait | speaker-quote |
| 活动概要｜竖版 | seminar-summary-portrait | seminar-summary |

不同主题或底图继续由 `theme`、`background_id` 和保存的背景素材决定，不为了更换底图而复制或更名排版模板。

完整封面与底图现在共用 [双产物项目协议](asset-model.md)：原 `content.json` 继续作为静图 / 动图共同的文案与模板来源，`project.json` 指向底图参数、平台配置、可选 motion 与可迁移 `runtime/`。动画不复制另一份文字和素材配置。

## 保存在哪里

- `assets/templates/` 保存七套共享模板默认参数。保留原版排版，改变单张配图不会改动这些文件。
- 每个已渲染项目的 `content.json` 保存 `template_id` 与完整 `template` 副本，包含中文名称、版本、画布、元素及默认参数。后续读取项目副本，避免共享模板更新后旧项目的布局发生变化。
- `content.json` 的 `layer_overrides` 保存用户对该图片单独调整的位置、大小、字号和对齐。更改文案或替换素材不会清除这些调整。
- 配置升级到 `schema_version: 2`；原来的文案、素材与 layout 字段保留。旧版配置在下次成功渲染时自动补齐模板副本；不会批量修改已有成品。

每个模板记录 `canvas.width/height` 和单位 `px`，以及元素的 `x`、`y`、`width`、`height`。文本另存 `font_size_max/min`（区域内适配范围）、`align`、绑定的文案字段、字体角色与颜色角色；图片存素材字段、水平/垂直对齐和等比例缩放规则。字号范围可设为同一值以固定字号，无法容纳全文时仍会报错，保留上一版成品。

位置与大小是原始设计画布上的整数像素，不是浏览器缩放后的尺寸。图片位置描述素材容纳框，实际可见人物在去掉透明边距后等比例放入框中；竖版嘉宾人物默认靠底。背景覆盖整张画布，由现有背景规则处理，暂不支持作为可移动元素覆盖。

## 元素命名

按业务含义命名，避免 `layer1`、`box2` 等编号。

| 元素 ID | 中文显示名 / 用途 |
| --- | --- |
| main-title | 主标题 / 概要标题 |
| supporting-text | 说明文案 |
| category-label | 分类标签 |
| footer-note | 页脚说明 |
| main-image | 主视觉 / 人物 / 截图（横版） |
| blocksec-logo | BlockSec Logo |
| partner-logo | 合作方 Logo |
| partnership-separator | 合作连接符 |
| event-details | 活动名称与日期 |
| quote-mark | 引号装饰 |
| main-quote | 金句主文案 |
| supporting-quote | 金句补充文案 |
| speaker-portrait | 嘉宾人物（竖版） |
| speaker-name | 嘉宾姓名 |
| speaker-attribution | 嘉宾职位与机构 |

活动概要要点在首次渲染时获得稳定 ID，例如 `takeaway-01`；对应 `takeaway-01-heading`、`takeaway-01-body`、`takeaway-01-accent` 三个元素，各有中文显示名。要点重新排序时仍绑定同一内容；新增要点使用新的 ID；删除要点时移除相应覆盖，避免位置调整误绑到另一条内容。用户可使用已有的语义 ID，例如 `risk-monitoring`，需保持唯一且使用小写字母、数字及连字符。

## 局部调整命令

两个渲染脚本都支持可重复的 `--layer ELEMENT_ID.PROPERTY=VALUE` 和 `--reset-layer ELEMENT_ID`。文案仍通过 `--set` 修改，素材仍通过 `--asset` 替换。

```bash
# 修改当前项目中嘉宾人物的位置；共享模板不变。
python SKILL_DIR/scripts/render_speaker_quote.py --project PROJECT_DIR --layer 'speaker-portrait.x=620'

# 随后只改金句，保留已保存的人物位置。
python SKILL_DIR/scripts/render_speaker_quote.py --project PROJECT_DIR --set 'quote=已确认的新金句'

# 恢复该人物到当前项目保存的模板默认位置和大小。
python SKILL_DIR/scripts/render_speaker_quote.py --project PROJECT_DIR --reset-layer speaker-portrait

# 横版项目移动主视觉，并指定标题对齐。
python SKILL_DIR/scripts/render_cover.py --project PROJECT_DIR --layer 'main-image.x=950' --layer 'main-title.align=center'
```

使用命令前根据项目是否有正式 Logo 保留原来的正式/草稿状态；缺少正式 Logo 的竖版草稿继续使用 `--draft`，不借此将草稿变成正式成品。

可调整的属性：文本支持 x/y/width/height、字号范围与 left/center/right 对齐；图片支持 x/y/width/height、水平 left/center/right 与垂直 top/center/bottom 对齐；装饰符支持位置与字号；强调线支持位置、宽度与线宽。未知元素、未知属性、非整数尺寸、越出画布和文本溢出均拒绝，不覆盖上一版配置与图片。

只改文案/素材时保留模板副本和覆盖。切换到另一种排版是显式操作，应选择匹配的新模板并重新映射覆盖，不沿用另一模板的元素参数。重设一个元素使用 `--reset-layer`，不要编辑共享文件来重设单张配图。

## 极简合作模板

`partnership-announcement-minimal` 的像素框、相对画布中心、两家公司间距、独立乘号素材及使用命令见 [极简双 Logo Partnership](partnership-minimal.md)。三层均为图片；乘号支持与 Logo 一样的 x/y/width/height 调整。原有合作模板仍使用字体乘号，排版保持不变。

## 验证

当前默认排版已与改造前渲染器逐像素核对：四种横版、居中合作图的单/双/无 Logo、两种人物宽高比，以及 1–4 条活动概要均一致。

回归检查覆盖：移动人物后改文案仍保持位置、恢复单元素、无模板库时使用项目副本、要点排序/增删的稳定绑定、旧配置升级、无效修改保留上一版文件。使用已有依赖 Python、Pillow、fontTools 运行：

```bash
python -m unittest discover -s SKILL_DIR/tests -v
```
