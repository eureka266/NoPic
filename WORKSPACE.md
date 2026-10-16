# BlockSec 社交配图 Skill 工作空间

此目录用于维护 `blocksec-social-cover`，初始内容来自 `/Users/eureka266/Downloads/blocksec-social-cover.zip`，保留压缩包内原文件。

## 放置用户原始素材

- 非背景原素材统一收件目录：`inbox/materials/`。可直接拖入，也可在对话里发送，由 agent 按香港日期和用途建立批次并登记。
- Logo、人物原照片、截图、确认文案和参考图保留原名与原内容；制作、抠图和转换使用项目副本，不覆盖原文件。
- 规则见 `inbox/materials/README.md`；六套静图模板、默认样式和完整效果图状态见根目录 `README.md`。
- 背景继续使用下面的既有收件目录；正式 Logo 的使用副本继续入 `assets/logos/`。

## 放置底图

- 新底图、参考图先放入 `inbox/backgrounds/`；可直接拖入，也可在聊天里发送给 Codex 整理。
- 已打包且可直接使用的底图在 `assets/backgrounds/`，当前 12 张 16:9 底图，另有 3 张当前推荐的 3:4 原图适配底图与 3 张保留的旧版底图。
- 底图索引为 `assets/backgrounds.json`；收到新素材后再确认用途并登记，不自动把参考图当成可发布底图。
- 优先复用用户指定的原始底图。仅用户明确要求生成新背景时才生成；修改标题或 Logo 时保留底图。

## 放置 BlockSec Logo

- 官方 Logo 上传目录：`assets/logos/`。可直接拖入 PNG/SVG，建议提供深底用白色版本和浅底用深色/彩色版本。
- 素材选择规则见 `assets/logos/README.md`；保留原文件，不覆盖已有版本。BlockSec、MetaSleuth、MetaSuites、Phalcon 的 PNG/SVG 使用副本按品牌保存在 `assets/logos/`，查找与默认选择用 `assets/logos/index.json`。Media Kit 横幅与社交图标在 `assets/media-kit.json`，来源收件批次为 `inbox/materials/2026-10-14-blocksec-media-kit/`。Phalcon Compliance 独立专属 SVG / 透明 PNG 保存在 `assets/logos/phalcon-compliance/`，索引 ID 为 `phalcon-compliance-lockup-dark`，适合浅色背景。
- 嘉宾金句参考截图保存在 `assets/references/osl-speaker-quote-reference.png`，仅参考结构，不用作底图。

## 嘉宾金句子指令

- `/speaker-quote` 或 `/嘉宾金句`：提供嘉宾原图、确认的金句、姓名与职位，输出透明人物 PNG 和 3:4 完整配图。
- `/seminar-summary` 或 `/seminar概要`：同底图制作无人物的活动要点概要。
- `/speaker-cutout`：仅人物自动去背景与透明 PNG 导出。
- 3:4 底图 A/B/C 预览：`assets/references/portrait-background-options-v2.png`；默认复用固定底图，仅明确要求才生成新底图。
- 执行规则：`references/speaker-quote.md`；配置示例：`assets/example-speaker-quote.json`；合成器：`scripts/render_speaker_quote.py`。

## 维护入口

- `SKILL.md`：工作流程与执行规则。
- `references/`：品牌、模板和背景规范。
- `assets/templates/index.json` 与六套模板文件：按用途和版式命名，保存位置、大小、字号范围和对齐默认值。
- `references/template-parameters.md`：模板中文名、元素名、项目保存规则和局部调整命令。
- `scripts/template_parameters.py`：解析模板副本、保留单图调整、验证参数与要点的稳定 ID。
- `scripts/render_cover.py`：读取常规 16:9 配置并合成图片。
- `scripts/render_speaker_quote.py`：检查透明人物素材并合成 3:4 嘉宾金句配图。

工作空间尚未安装到 `~/.codex/skills/`。后续先在这里更新和验证，再同步安装。

## 原图适配的 3:4 长图底图

- `portrait-data-glow`：来自 `inbox/backgrounds/#U8d44#U6e90 7 1.png`，蓝橙柔光与细点阵。
- `portrait-diagonal-light`：来自 `inbox/backgrounds/#U8d44#U6e90 1 8.jpg`，暗蓝斜切光影。
- `portrait-gradient-spheres`：来自 `inbox/backgrounds/exec-90481eac-175b-4110-954b-db1f3a033839.png`，蓝橙渐变圆形与角落点阵。

均为 1200×1600 PNG，保留原图比例并纵向重排，中央扩展连续深色文字区。来源与哈希存入 `assets/backgrounds.json`，原文件不修改。新金句默认蓝橙点阵，新概要默认斜切光影；旧项目的已保存底图保持不变。

## 双产物项目层

- `references/asset-model.md`：两类交付、四个系统职责、权威配置、迁移与多平台规则。
- `scripts/project_assets.py`：两个合成器共用的项目保存；完整封面同时输出独立底图。
- `scripts/cover_project.py`：background 纯底图入项目、motion 接入实际动画源、export / rebuild 通过 presentation 统一静态与动态。
- `assets/platform-presets.json`、`assets/schemas/cover-project.schema.json`、`assets/schemas/motion.schema.json`：平台规格、兼容旧 v1 的项目清单 v2 与可选动效配置。
- `scripts/render_motion.py`：已有图层周期合成或接收外部纯背景帧，叠加当前准确前景并由 FFmpeg 编码。

此轮只维护工作空间源码，不自动同步本地技能安装目录。
