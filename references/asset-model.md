# 双产物与静态 / 动态共用项目

## 架构评估与职责

原架构已经分离底图、文字、Logo / 人物 / 截图，保存模板副本和单图覆盖；可修改 `content.json` 再渲染。缺口在于纯底图仍依附完整封面流程、无统一项目清单与底图元数据、多平台尚无配置与批量导出入口。本次在原合成器上增加共享持久化与项目命令，不替换已有模板和素材。

| 系统 | 实现 / 权威数据 | 职责 |
| --- | --- | --- |
| Background Layer | `assets/backgrounds.json`、`background/` | 原图复用、原生 image_gen 生成后的接收、来源 / 风格 / 安全区元数据；不在合成器生成纹理 |
| Typography Layer | `assets/templates/` → 项目 `content.json.template`、`layer_overrides` | 独立文案绑定、字号、换行、对齐与素材容纳框；共享模板更新不改变旧项目 |
| Platform Preset | `assets/platform-presets.json` → 项目 `layout/platform-layouts.json` | 尺寸、安全区参考、平台背景与显式版式覆盖；用户规格优先 |
| Composer / Export | 两个静态渲染器、`render_motion.py`、`project_assets.py`、`cover_project.py` | 同项目合成静态 / 动态图层、保存两类产物、按平台派生与重编译；motion 为可选时间配置 |

三层资产库各司其职：共享底图库与共享版式库放在 `assets/`，具体主题项目放在用户指定输出目录。派生不写回共享库。平台预设是内部设计尺寸，不声明为平台当前强制要求。

内容类型、呈现方式、发布平台分别选择：合作 / 活动 / 周报等是内容类型，static / motion 是同一种配图的呈现方式，X / LinkedIn 等是投放平台。动图复用同一文案、背景、Logo、素材和版式，不另建一套动画主题项目；只增加可选 motion 配置与实际动画源。产品演示视频仍路由独立 Carrot。

## 两种交付模式

- **Background-only**：只交付无字、无 Logo、无水印的 PNG / WebP、配置与按需平台版本；不为了凑齐完整项目而要求标题、人物或 Logo。项目保留将来叠字能力，但没有确认文案时不虚构封面。
- **Full-cover editable project**：交付完整 PNG / WebP，**同时**保留干净背景及参数、独立文案、模板、素材与字体副本、可运行项目。无文案双 Logo 海报也属于完整封面，不能当纯底图。

两种模式共用同一背景资产。任何项目都不能把唯一母版保存成已烧录文字的成图。“只改文案 / Logo / 人物”不得重生成底图；跨画幅先检查留白与构图，必要时适配版式或选已有平台底图，仍只有用户明确要求新绘制时才调用原生 image_gen。

两种资产模式均可选择静态或动态呈现。默认只出静图；用户要求 motion 时，完整封面额外交付 MP4 / GIF 和 poster，纯底图也可交付对应无字背景动画。`--mode both` 保持原意“完整封面及底图”，`--presentation both` 才表示静态与动态两种呈现。执行细节仅在需要动效时读取 [静态与动态工作流](static-to-motion.md)。

## 项目文件与修改来源

```text
theme-project/
├── project.json                         # 清单 v2；兼容读取 v1
├── content.json                         # 完整封面的文案、素材路径、模板副本与覆盖；兼容旧 v2
├── background/
│   ├── master-<sha256>.png               # 不可变纯底图，内容哈希命名
│   ├── background-config.json            # 当前底图的来源与参数
│   └── original/<原文件名>               # 纯底图入口保留原文件；完整封面原素材在 assets/
├── layout/platform-layouts.json          # 平台预设副本与各平台 variants
├── assets/                              # 独立 Logo、截图、人物、原照片与字体副本
│   └── foreground-<hash>.png             # 静图 / 动图共用的精确透明前景
├── motion/                              # 可选；配置、源素材及外部动画工程
│   ├── motion.json                       # 时间、运动层或背景帧、循环与格式
│   ├── assets/                           # 实际运动源的项目副本
│   ├── poster.png                        # 已渲染动图首帧
│   └── last-render.json                  # 实际参数与源哈希
├── runtime/                             # 重编译 / 导出的 Python 脚本与平台预设
├── output/background-only/{平台}.png|webp|mp4|gif
├── output/final-covers/{平台}.png|webp|mp4|gif
└── variants/{full-cover|background-only}/{平台}/  # 每个平台可独立迁移的项目
```

默认导出名称为 `default.png/webp`。完整项目兼容根目录 `cover.png`、`speaker-quote.png` 或 `seminar-summary.png`。纯底图项目没有 `content.json`、素材或完整成图时不创建空占位文件夹。清单 schema 在 `assets/schemas/cover-project.schema.json`。

`content.json` 是母项目文案 / 模板 / 图层的唯一编辑来源，平台导出每次读取它；`layout/platform-layouts.json.variants` 是平台专属版式的编辑来源。导出的子项目是当次快照，在子项目改文案只影响该平台。修改母项目后须重新执行 export 才会刷新其他平台成图。

清单 v2 增加 `foreground`、`motion` 和 `presentations`，motion 为空的项目仍正常出静图，不需要动画依赖。动效配置引用 `assets/schemas/motion.schema.json`；静态版式与文案没有另复制到 motion。已有动态版本只有在带 `--presentation motion|both` 的导出后才更新，不能把保留的旧视频当成新文案版本。

`background-config.json` 保存 `sha256`、`size`、`style`、`theme`、`colors`、`safe_area`、`source`、`generation`、`prompt`、`model`、`seed`。未知值用 `null` / 空数组，不伪造 seed、模型或提示词；原生工具未返回 seed 时，能重编译指的是用已保存背景合成，不能保证重新生成逐像素一致的 AI 背景。补充已知参数可通过输入 `background_metadata`，或首次纯底图命令的 `--metadata` JSON；输入 metadata 消费后只保存在背景配置中，避免重放到下一张背景。换底图时同步更新来源参数，不能沿用旧 seed / prompt；平台独立背景使用 variant 的 `background_metadata`，默认不继承母版生成参数。只改文案时底图哈希与既有元数据保持。

## 命令与能力边界

静态依赖 Python 3、Pillow、fontTools，动态编码另需 FFmpeg。可使用原两个渲染器的命令，成功后自动补齐双产物结构和透明前景。旧项目仅在下次成功渲染时升级，不批量改已有文件。`project.json` 版本与 `content.json.schema_version: 2` 分别演进。

### 仅底图、无需任何文案

先查看实际原图，确认它是可用无字底图；参考海报和 Media Kit 含字横幅不能通过此入口。`--confirm-clean` 记录执行者已核实素材的选择，不是图像自动识别器。聊天素材先按收件规则存入 inbox。

```bash
python SKILL_DIR/scripts/cover_project.py background --project NEW_PROJECT_DIR \
  --background CLEAN_BACKGROUND.png --confirm-clean
# 可加 --metadata BACKGROUND_METADATA.json；新项目目录须未被占用。
python SKILL_DIR/scripts/cover_project.py export --project PROJECT_DIR \
  --platform blog --platform x --mode background-only
```

需要新背景时先调用原生 image_gen 并验收实际图片，然后把返回文件交给这个入口；本命令仅接收既有图像，不生成背景。未来升级完整项目时，用匹配模板的内容 JSON 运行原渲染器，`--project` 指回该目录，`--background` 指向其清单中的 master 路径，保留同一背景与元数据。

### 完整封面与再次编辑

```bash
python SKILL_DIR/scripts/render_cover.py --content APPROVED_CONTENT.json --project PROJECT_DIR
python PROJECT_DIR/runtime/cover_project.py rebuild --project PROJECT_DIR --set 'title=新的确认标题'
python PROJECT_DIR/runtime/cover_project.py export --project PROJECT_DIR \
  --platform x --platform linkedin-horizontal
# 已接入真实动效源时，同一项目 / 平台同时导出静态和动态。
python PROJECT_DIR/runtime/cover_project.py export --project PROJECT_DIR \
  --platform x --platform linkedin-horizontal --presentation both --format mp4
# 可重复 --project 为多个主题批量导出；每个主题独立报告成功 / 失败。
```

竖版仍用 `render_speaker_quote.py` 创建。`rebuild` 自动选择原渲染器并保留草稿状态，支持原文字字段和 `--asset`；位置调整继续用对应渲染器的 `--layer`。项目可整体迁移，使用 `runtime/` 和项目内相对素材路径，仍需目标环境安装 Python 依赖。字体副本按原使用授权处理。

### 多平台版式与安全区

`platform-layouts.json` 含 `presets` 与 `variants`。内置 blog、x、linkedin-horizontal、linkedin-vertical、wechat-headline、wechat-square、og；尺寸与 `[x, y, width, height]` 归一化安全区参考从预设复制到项目。安全区是视觉审阅指导，渲染器检查画布边界和文字溢出，不能代替平台预览审阅。

同画幅完整封面可自动缩放独立图层与字号并重新排字。异画幅纯底图默认拒绝隐式裁切；明确允许中心裁切才使用 `--fit cover` 或 `background_fit: "cover"`。也可准备平台专属既有底图并在 variant 的 `background_file` 指定**项目内相对路径**，以 strict 导出。原母版不覆盖。

异画幅完整封面还需要该平台 `template` 的完整快照（结构与现有 `content.json.template` 相同，`canvas` 必须匹配目标尺寸），及按需 `layer_overrides`。由 agent 根据内容与安全区准备并视觉检查，不要求运营手写 JSON。不提供跨画幅自动重排的承诺，也不裁切或拉伸已叠字成图。

例如在 `variants.wechat-square` 保存：

```json
{
  "size": [1200, 1200],
  "safe_area": [0.06, 0.06, 0.88, 0.88],
  "background_file": "assets/approved-square-background.png",
  "background_fit": "strict"
}
```

上例可直接导出无字版本；完整封面需再放入实际适配好的 `template`。默认继承母项目文案与素材，不改共享模板。新栏目可绑定现有 `eyebrow` 槽位；需要新增独立文字种类或渲染规则时扩展对应模板和合成器，不宣称任意新图层类型已受支持。

同一主题的多个平台先在临时目录完成校验、渲染，全部成功后再发布该批结果；异画幅缺失模板、文字溢出或素材无效会保留之前的成功成品。再次导出同名平台会刷新该派生项目；需保留历史编辑时先另存平台 ID。background-only 派生与 full-cover 派生分目录，单独导出背景不覆盖已有完整项目。此流程不保证文件系统故障或多主题批次整体原子性。
