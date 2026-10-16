# /speaker-quote：Web3 活动嘉宾金句

用于 Web3 活动、seminar、panel、webinar 的嘉宾金句 LinkedIn 配图；`/嘉宾金句` 与自然语言“做一张嘉宾金句图”使用同一流程。`/speaker-cutout` 或“只抠人物”只交付透明人物素材。它们是本 skill 的对话子指令，无需另装插件或注册终端命令。

## 输入与文案

- 嘉宾原始照片（原图优先）、姓名、职位与机构；可选活动名、日期、语言。
- 用户确认的金句；可分成主金句 `quote` 与展开段 `quote_body`。原文逐字保留，指定强调片段用 `highlights`。语言默认跟随用户提供的原文，要求英文/翻译时才翻译。
- 用户仅提供逐字稿/会议记录时，可挑出候选原句并标明出处，再采用用户选定的句子。用户明确授权“提炼/润色”时可生成建议，但改写不能作为未经确认的逐字引语署名发布。不从参考图复制人物身份、日期、金句或活动事实。
- 正式 BlockSec Logo 先读取 [Logo 索引](../assets/logos/index.json)，按背景选择并使用 `render_file`：深底默认 `blocksec-white`，浅底默认 `blocksec-dark`，用户指定版本优先；不能仅按文件名判断颜色。品牌色读取品牌规范。现有蓝 `#248BCC`、橙 `#FF7A1A` 是草案，官方色值/用户指定值优先。没有官方色值也可先按草案制作并说明，不必阻塞整个流程。
- 缺照片时不生成虚构嘉宾。缺 Logo 时可继续抠图和整理配置；需要预览可用 `--draft` 输出明确标记的草稿，正式出图需真实 Logo。

## 参考结构与构图

参考图存于 `assets/references/osl-speaker-quote-reference.png`，仅作为结构参考，不是可发布背景或嘉宾照片源。只参考截图中的海报区域，忽略社交平台界面、账号、日期、互动数字。

默认 **1200×1600（3:4）**，是模板设计选择，不宣称平台要求。深色近黑底；左上橙色大引号；上半部主金句；左下展开段、嘉宾姓名与职位；右下透明半身人物；右上官方 BlockSec Logo。背景复用用户原图的蓝橙柔光、细点阵、斜切光影或渐变圆形；橙色用于引号、关键词、姓名等局部强调。去掉 OSL 荧光绿色与 OSL 版式中的 Logo；人物衣服上的真实机构标识默认保留，不用 AI 将其冒改成 BlockSec。

默认复用 `assets/backgrounds.json` 的 `portrait_presets` 中固定 3:4 PNG，不调用图像生成工具。先展示 `assets/references/portrait-background-options-v2.png` 供选择；未指定时金句用 A，概要优先 B；选择一次后保留配置，后续修改不得重选或重做背景。

| 选项 | background_id | 文件 | 建议用途 |
| --- | --- | --- | --- |
| A | portrait-data-glow | assets/backgrounds/portrait-data-glow.png | 蓝橙点阵，人物金句 |
| B | portrait-diagonal-light | assets/backgrounds/portrait-diagonal-light.png | 斜切光影，seminar 概要 |
| C | portrait-gradient-spheres | assets/backgrounds/portrait-gradient-spheres.png | 渐变圆形，嘉宾金句/活动回顾 |

这三张底图直接复用 `inbox/backgrounds/` 中的原始光感与纹理素材，等比缩放后把上下装饰纵向重排，在中央扩展深色留白；不拉伸圆形、不新画替代几何图案，保留原图。来源与校验值记录在索引中，不标作 AI 生成图。旧版三张预设保留兼容已有项目，新建默认使用本表。使用 `background_fit: "contain"` 保持固定 3:4 画幅。用户另行授权裁取非 3:4 底图时才用 `cover`。其他比例需调整布局，不能拉伸成品。

## 人物自动抠图

1. 先查看用户原图。保存原图到本次项目，不覆盖用户源文件。多个人物时先明确目标嘉宾；已是合格透明 PNG 可直接复用。
2. 非透明照片使用当前会话的原生图像编辑能力，明确要求 **移除背景并输出真实透明 RGBA PNG**。编辑目标必须是嘉宾原图；本地原图先用图片查看工具载入对话。只改变背景，不改脸型、五官、肤色、发型、年龄、服饰、姿势或真实衣服标识，不补造手臂或身体。
3. 可用编辑提示词：

   > 从这张嘉宾原始照片中精细移除背景，输出具有真实 alpha 通道的透明 PNG。逐一保留人物原有五官、表情、发型与发丝、肤色、服装、手部、姿势和可见机构标识。不做美颜、重新绘制或身份替换，不生成缺失的身体部位。不要输出白底、纯色底或印在图片里的棋盘格。边缘无原背景残留、白边或蓝橙色溢出。

4. 将工具返回的实际文件复制进项目。用下方 `--cutout-only` 检查 PNG/alpha 并持久化。数值检查只能证明存在透明像素，必须在深浅两种底色上查看发丝、肩部、手部和身份是否保真。假棋盘格/背景残留不能算合格。失败时进行一次针对性修复，再检查；仍无法保持真实身份/透明度时交付已完成的配置与原因，不宣称抠图成功。无法获得可保存文件时也不能用路径占位符冒充成果。
5. Python 只检查透明度、缩放及合成；不承担 AI 抠图，不用颜色阈值擦除照片背景。不要自动转用第三方照片上传服务或需要另行配置的 API。原生编辑工具不可用时说明缺失能力，保留准备好的配置；可直接接入用户提供的透明 PNG。

## 可复用配置与执行

读取 `assets/example-speaker-quote.json`，填写实际信息与素材路径。配置路径相对其 JSON 所在目录解析。`photo_original` 可选，用于项目保留原图；`portrait` 必须是抠图后的透明 PNG。`logo` 使用正式透明 PNG；SVG 先用现有矢量导出工具导出透明 PNG，保持官方形状、颜色与比例，不能用图像生成工具重画 Logo。

只交付抠图素材（该脚本检查并保存已完成的抠图，不调用图像模型）：

```bash
python SKILL_DIR/scripts/render_speaker_quote.py --cutout-only --portrait CUTOUT.png --project PROJECT_DIR
```

完整金句配图：

```bash
python SKILL_DIR/scripts/render_speaker_quote.py --content CONTENT.json --project PROJECT_DIR
```

修改已有项目（不重新抠图、不重做背景）：

```bash
python SKILL_DIR/scripts/render_speaker_quote.py --project PROJECT_DIR --set 'quote=用户确认的新金句'
python SKILL_DIR/scripts/render_speaker_quote.py --project PROJECT_DIR --asset 'portrait=/absolute/path/new-cutout.png'
python SKILL_DIR/scripts/render_speaker_quote.py --project PROJECT_DIR --asset 'logo=/absolute/path/blocksec-white.png'
```

`--set` 支持 quote、quote_body、speaker_name、speaker_role、organization、event、event_date、title、footer。只改金句后，若旧的 `highlights` 已不在新文案中，脚本自动移除失效强调片段；新增强调请修改 JSON。`palette` 可覆盖 background/text/muted/blue/orange；不改 Logo 颜色。字体规则与主 skill 相同（Python 3、Pillow、fontTools），支持中英文检查缺字。人物位置与引语区分离；文字过长时在许可字号内适配，仍溢出则报错并保留上一版文件，不截断、不擅自改写。

## 交付与验收

完整金句 / 概要项目同时保存无字底图 PNG / WebP、完整成图 PNG / WebP、底图元数据、平台配置及可迁移运行脚本，目录与多平台命令见 [双产物项目协议](asset-model.md)。只要无字背景时使用纯底图入口，不要求人物、金句或 Logo。以下既有 PNG 文件名继续兼容。

- `speaker-cutout.png`：独立 RGBA PNG，透明通道保留；不加蓝橙背景、文字、Logo。
- `speaker-quote.png`：1200×1600 完整配图；有正式 Logo 且没有草稿标记，才称为正式成品。
- `content.json` 和 `assets/`：复制实际人物、原图（如提供）、Logo、背景与字体，配置记录相对路径，可迁移。抠图单独模式另外保留 `cutout.json` 记录。

查看成品原尺寸与缩小预览，检查逐字文案、强调范围、嘉宾身份、姓名职位对应关系、发丝边缘、Logo 原色和比例、人物与文字无重叠。交付时展示成品并给两张 PNG 的实际路径；如仅抠图则只交付透明人物。用户未要求发帖时，只制作文件。

## /seminar-summary：同底图制作活动概要

`/seminar-summary`、`/seminar概要` 或“制作 3:4 seminar 要点概要”读取 `assets/example-seminar-summary.json`，设置 `layout: "seminar-summary"`，填写已确认的标题与 1–4 条 `sections`（每条 heading/body），使用同一个合成脚本。此模式没有人物位，不需要人物照片；不从主题猜测活动结论。机构名/嘉宾名/数字以用户的会议材料为依据。输出 `seminar-summary.png` 与可复用配置。默认 B；用户指定 A/C 时按其选择。正式出图同样使用上传的官方 Logo。

```bash
python SKILL_DIR/scripts/render_speaker_quote.py --content SUMMARY.json --project PROJECT_DIR
python SKILL_DIR/scripts/render_speaker_quote.py --project PROJECT_DIR --background-id portrait-gradient-spheres
```

切底图只改变背景；已保存项目优先读取 `background` 的实际文件。仅改 JSON 的 `background_id` 不会覆盖已保存背景，显式切换请用 `--background-id`。

## 底图稳定与新生成规则

普通出图、换金句、换人物、seminar 概要、批量出图都读取固定 PNG；不得为了“更适合这次活动”自动重生成、调色或重画。`scripts/adapt_inbox_portrait_backgrounds.py` 是当前原图适配的维护工具；`scripts/build_speaker_backgrounds.py` 仅保留旧版实现，不作为新底图绘制入口。两者不在正常制作链路中调用，也不能覆盖已有预设；用户要求新绘制时必须调用原生 `image_gen`。

只有使用者明确要求“从零绘制 / 根据参考图和素材新绘制底图 / 生成新底图 / 重新生成底图 / 新增背景风格”时，才读取 [3:4 新背景规范](speaker-background-generation.md)，必须调用原生 `image_gen` / `image_generation`，不得以程序绘制替代。用户只要求“换一张 / 选合适的底图”时从固定 A/B/C 中选。新底图使用新文件名，保留旧预设；需要正式入共享库时更新 `portrait_presets`，没有入库要求时保存到当前项目。未来生成成功须保存并核对实际图片，不能把提示词或无文件的工具返回当成生成成功。
