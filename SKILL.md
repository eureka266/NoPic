---
name: blocksec-social-cover
description: 在 Codex 侧边打开 NoPic 工作台，用自然语言和上传的参考图、Logo、人物照片、截图或文案制作可编辑社交封面；默认复用已有底图与版式，支持合作公告、活动、文章、嘉宾金句及 Blog、X、LinkedIn、微信和 OG 派生。当前模板源自 BlockSec 项目。
---

# 有图 NoPic

首次调用时，先在 Codex 右侧打开本地 NoPic 工作台，再在当前会话中协作完成内容判断、素材选择、排版和导出。用户不需要先选择技术模式、打开 localhost 或手动运行启动命令；工作台是交互面板，会话是决策与执行入口。每种图片类型使用对应模板的固定区域与相对大小，文字在区域内换行和适配字号；除非用户要求调整排版，不重新安排素材位置。常规封面默认以 1600×900 为设计画布，交付 PNG / WebP、干净底图和可重编译项目；嘉宾金句使用下方独立竖版流程。尺寸是模板设计选择，并非平台强制规格。


本包显示名称为「有图 NoPic」，技术标识和现有调用入口保留 `$blocksec-social-cover`。当前模板与默认素材仍源自 BlockSec 品牌项目；其他品牌需明确提供并替换正式素材。中文使用指南见 [README](README.md)。

## Codex 侧边工作台

当用户用自然语言请求制作、修改、预览或上传封面素材时，按 [Codex 工作台协议](references/codex-workbench.md) 执行：

1. 调用 `scripts/start_workbench.py` 检查并启动本地工作台；已有可用实例时复用，不重复启动。
2. 使用 Codex 的 `open_in_codex` 浏览器面板动作打开工作台 URL，默认放在右侧。不要把启动命令或 localhost 地址作为用户的第一步要求。
3. 如果当前宿主没有 `open_in_codex`，说明侧边面板不可用，直接返回工作台 URL并继续在会话中制作；不要宣称已打开侧边栏。
4. 用户在工作台上传素材或填写说明后，读取 `workspace/workbench-state.json` 与 `workspace/session-handoffs/latest.json`，把它们视为当前会话的输入。参考图保持 `reference_only` 语义，不能自动变成发布素材。
5. 预览、改字、换底图、选择模板和导出可以在工作台完成；视觉判断、事实核对、素材取舍、新背景生成和最终交付说明仍由当前会话负责。

工作台不能直接向 Codex 注入新消息。它通过共享本地项目状态和会话任务清单与当前对话同步；没有清单时，以聊天中用户明确提供的素材和要求为准。

## 核心产品原则：同一系统，两类产物

每个主题都保留纯底图资产与可编辑完整封面的能力，按用户当前需要交付：

- **Background-only**：无字、无 Logo / 水印的 PNG / WebP、底图元数据和按需平台版本。无需标题或 Logo，不虚构完整封面。
- **Full-cover editable project**：完整 PNG / WebP **加**纯底图；独立文案、Logo / 人物 / 截图、字体与版式配置，以及可再次运行的项目。无标题的双 Logo 图仍是完整封面，不能当纯底图。

唯一母版不能烧录文字。背景、文字排版、平台规格、合成导出是四个独立职责；复用现有底图库、版式库和主题项目，不因换文案重新生成背景。只有用户明确要求新背景时才调用原生 image_gen。

先识别交付模式，再匹配内容类型。用户要“无字 blog 底图 / 品牌背景库 / 后续人工叠字”时走纯底图流程；要“直接发图 / 改标题 / 多平台封面”时走完整项目流程。完整项目默认同时保存两类资产；只要底图时不要求补齐完整封面的内容。创建、再次编辑或跨平台导出时读取 [资产模型与项目协议](references/asset-model.md)，使用其中的实际命令。尺寸、安全区与裁切策略从项目平台配置读取，显式用户规格优先。

**配图有三个独立维度**：内容类型（合作 / 活动 / 周报等）、呈现方式（`static` / `motion`）、发布平台（X / LinkedIn 等）。静图和动图共用同一个 cover project，不把动图列为新的内容类型或另建一套项目模型；纯底图 / 完整封面两种资产模式也都可按需派生动态版本。

动效是 `project.json.motion` 指向的可选配置，复用母项目的背景、文案、Logo、人物、截图和版式，仅增加运动层、时间与循环规则。默认只出静图；用户要求动图或两种版本时，读取 [静态与动态配图工作流](references/static-to-motion.md)，通过统一 `export` / `rebuild --presentation static|motion|both` 执行。只改文案时重编译准确前景，不重生成底图或背景动画。静态导出不会刷新已有视频，需明确导出动态版本。

共享底图库在 `assets/backgrounds.json`，版式库在 `assets/templates/`，平台设计预设在 `assets/platform-presets.json`；主题项目由 `project.json` 指向现有兼容 `content.json`、`background/`、`layout/`、`assets/` 与 `runtime/`。两个现有渲染器会自动保存共享双产物结构与独立透明前景；可选 motion 配置和动画源素材保存在同一项目 `motion/` 中。纯底图独立使用 `scripts/cover_project.py background`；平台批量导出与重编译使用 `export` / `rebuild`。不要只交一张成图而丢弃项目。

异画幅完整封面需要明确的目标版式；只对同画幅缩放图层。底图的跨画幅裁切需显式指定，不能自动裁切整张成图；先复用合适底图或适配已有素材，生成授权规则保持不变。未知 seed / 模型 / prompt 保留空值，不声称能复现工具未提供的生成参数。

用户提供参考图用于一次性出图时，在普通制作流程中按需拆解，不要求额外调用子指令。`/analyze-reference` 是可选的参考贡献与共建入口：读取 [参考图拆解与共建](references/reference-analysis.md)，默认形成可审阅的贡献候选，将类型映射、字体 / 版式参数、底图提示词和规格登记到 [参考库索引](assets/reference-library/index.json)。经过适用验证的可复用方案入库；用户明确“只分析”时只交付当前项目分析，不修改共享库。首次引导完成后，可从新建类型分支进入共建，也可直接调用本指令。

先按领英 / X 内容类型判断需求：Partnership 合作公告、活动、安全周报与阶段汇总、安全事件分析、产品更新、研究与观点。读取 [内容类型与制作规则](references/content-types.md) 和匹配类型的已验证参考库记录后映射到已有模板；金句、概要、抠图与动图是各内容类型下的制作形式或辅助能力，不作为首层内容分类。用户只需提供内容用途和已确认素材，无需先选择技术模板。配图的循环动效使用兼容入口 `/animate-cover`；官网、落地页、邮件中的产品功能/价值动图使用 `/product-motion`，按 [Carrot 索引](references/product-motion.md) 读取已安装的 `carrot`。产品动图不套用合作动图的默认值。

用户询问如何共同维护、提交贡献、审核或复用团队方案时，读取 [用户共建指南](references/contributors-guide.md)，用帖子用途、视觉效果和普通中文反馈指导，不要求用户手动修改配置。

## 首次调用引导

用户在当前对话中首次调用本 skill 的任意子指令时，先读取 [首次调用提问脚本](references/first-invocation.md)，介绍现有内容类型与静图 / 动图能力，再完成一次类型选择。Codex 中优先使用当前工具列表实际提供、且当前模式允许调用的 `request_user_input`（名称空间以宿主为准）；ChatGPT 仅使用当前会话真实提供的结构化问答工具。没有可用工具或其调用条件不满足时，用一个普通中文问句收集类型，不能调用不存在的 `AskUserQuestions`，不能为此擅自切换模式。

能力介绍包含 Partnership 合作公告、活动预告 / 回顾 / 嘉宾金句、安全周报 / 阶段汇总、安全事件分析、产品更新、研究与观点，以及人物透明 PNG、单蓝 / 单橙 / 蓝橙 / 黑白灰风格、配图静态与动态版本、Carrot 产品营销动图、参考图拆解与图层合成参数。结构化工具的选项保留“都不是，新建配图类型”；普通对话回退用自由回答承接此需求。即使首次消息已指定类型，也先介绍能力，再以该类型完成一次简短确认。

选择新建类型后，复用已提供信息，引导描述帖子类型及用途、合作方 / 嘉宾 / 产品、平台与画幅 / 格式 / 时长要求，再建议提供参考图。按平台提供 X / LinkedIn 的素材下载指引，下载后回到当前窗口上传；具体问句、`request_user_input` JSON 和下载地址均在首次调用提问脚本中维护。

一次对话只完成一次引导；后续按当次请求路由，不反复展示能力菜单。维护本 skill 不触发这套制作引导。首次引导是内容类型选择，不构成对其他操作的授权。

## 维护完成后的团队更新提醒

只有本 skill 的说明、脚本、模板、参考库或共享素材发生维护变化时，执行 [团队更新规则](references/team-sharing.md)。先完成适用校验并用 `scripts/skill_team_update.py package` 准备可审阅候选包，说明实际改动、文件清单与待验证依赖，再询问“是否将此次维护更新上传到 Blocksec 团队空间？”。原生 hook 已完成相同提醒时不重复；用户已明确授权更新同一个工作区时按授权推进。普通配图输出或只读分析不触发团队更新。

本地 Codex 提供项目级 `UserPromptSubmit` / `Stop` hook；未加载、未信任或云端 Work 不支持本地 command hook 时，agent 用本段规则完成对话提醒。hook 是机器提示，不是上传授权。上传前确认真实工作区、目标 skill 与发布权限；没有实际发布能力时交付候选包和操作指引，不报告已上传。

## 接收用户素材

用户通过聊天、拖拽或路径提供的 Logo、人物原照片、截图、文案和参考图，先保留在 `inbox/materials/`，具体批次命名与登记见 [素材收件说明](inbox/materials/README.md)。背景原文件继续收集到 `inbox/backgrounds/`。原文件与制作副本分开，保留原名、不覆盖同名素材；人物抠图和转换在项目副本上执行。正式 Logo 的使用副本入 `assets/logos/`，并登记 [Logo 索引](assets/logos/index.json)；字段与选用说明见 [Logo 素材说明](assets/logos/README.md)。参考素材不能自动当成可发布素材。

制作前先读取 Logo 索引，先匹配用户指定的 BlockSec / MetaSleuth / MetaSuites / Phalcon / Phalcon Compliance 品牌，再按完整 Logo 或独立图标与背景明暗选择；各品牌推荐版本见 `brand_defaults`，素材缺失或仅参考的状态见 `brand_status`。未指定产品标识时使用 BlockSec 主品牌，深底默认 `blocksec-white`、浅底默认 `blocksec-dark`；用户指定版本和已有项目选择优先。仅 `reference_only: false` 且未标为 `usable_as_standalone_logo: false` 的 Logo 可用索引中的 `render_file` PNG 路径写入内容配置或传给 `--asset logo=...`，并在项目中保留使用副本。Phalcon Compliance 已收录独立专属 SVG 与透明 PNG，浅底默认使用 `phalcon-compliance-lockup-dark`；此前含背景和宣传语的横幅仅作参考或明确原样复用，不放入 Logo 槽位。未提供白色专属版本时不自行反色，也不自动用 Phalcon 通用 Logo 替代。索引供 agent 选择素材，渲染脚本不自动解析它。文件名不能替代实际颜色判断：旧版两份名称含 `white` 的 SVG 实为深墨色。产品 Logo、图标、含字横幅与社交渠道图标的命名和使用边界见 [Media Kit 素材说明](references/media-kit.md)，使用辅助素材时读取 [辅助素材索引](assets/media-kit.json)。

用户希望补齐 README 示例时，读取 [逐步示例制作指南](references/example-walkthrough.md) 和 [示例状态](assets/examples/index.json)，一次只收集当前这一张真正缺少的材料。先做 Partnership，再按用户选择推进活动、安全周报等；包内正式素材优先复用。复用固定底图与当前模板，不调整共享默认参数；允许用于示例且完成视觉检查后，在短 README 图库嵌入实际成品，保留独立项目与原始素材。完整模板说明在 [详细手册](references/user-manual.md)，不把首页重新扩成长手册。仅在确认素材允许用于示例时使用，不拿参考海报、无字底图或没有正式 Logo 的草稿代替完整效果图。

## 子指令

- `/analyze-reference` 或“贡献参考图 / 共建配图类型”：读取 [参考图拆解与共建](references/reference-analysis.md)，提炼字体、字号、版式、底图提示词与合成参数，形成共享参考库的贡献候选。先完成具体规格和差异说明，再按已有授权或用户审核登记可复用方案；需要改模板或渲染器时必须真实实现并验证。用户明确“只分析”时保持项目级分析。普通出图不必经过此指令。
- `/product-motion` 或“制作产品营销动图”：读取 [产品营销动图 / Carrot 索引](references/product-motion.md)，再读取并使用已安装的 `$carrot`。本包提供入口和路由，Carrot 作为独立外部技能维护，不复制其脚本、素材或工作流。
- `/animate-cover` 或“把这张配图做成动图”：读取 [静态与动态配图工作流](references/static-to-motion.md)，在原 cover project 中启用 motion 并使用统一导出入口。默认保留已确认配色与构图，不先强制改成纯黑或蓝橙；只有用户要求换风格时读取 [母版与可选风格调整](references/static-style.md)。首个已有配方为 `partnership-grid-flow`，适用于可分层、可周期运动的网格背景，前景固定；不把它强加给无纹理 / 绸缎 / 照片。实际制作与验收按可用执行器完成，不把只有提示词称为成品。对话子指令兼容保留；命令行用 `cover_project.py` 的 motion / export / rebuild。

- `/speaker-quote`、`/嘉宾金句` 或“制作 Web3 活动/seminar 嘉宾金句领英配图”：读取 [嘉宾金句工作流](references/speaker-quote.md)，使用参考结构制作 1200×1600 竖版图，交付透明人物 PNG、完整配图和可复用配置。
- `/seminar-summary`、`/seminar概要`：按同一 [嘉宾金句工作流](references/speaker-quote.md) 制作无人物的 3:4 活动要点概要，使用固定底图和正式 Logo。
- `/speaker-cutout` 或“只抠嘉宾人物”：按同一工作流使用原生图像编辑能力自动去背景，仅交付透明 PNG。
- 3:4 使用固定底图 `portrait-data-glow`、`portrait-diagonal-light`、`portrait-gradient-spheres`，均根据 `inbox/backgrounds/` 原图适配，见 [选择预览](assets/references/portrait-background-options-v2.png)。普通出图始终复用；只有明确要求新底图时才使用 AI。
- 正式 BlockSec Logo 上传到 `assets/logos/`；选取适合背景的官方版本。该子指令优先于下方常规 16:9 布局选择，使用 `scripts/render_speaker_quote.py`，保留原有 `quote` 横版布局。

## 工作流程

1. 读取 [品牌与模板](references/brand-and-templates.md)。根据内容气质、素材与信息层级选择单蓝、单橙、蓝橙组合或呼应 BlockSec 黑色 Logo 的黑白灰方向，不要求每张底图同时出现蓝橙。具体色值和排版参数仍是草案，优先采用官方 Logo、字体、色值。
2. 确定标题、副标题、标签和可选图片。确切文案逐字保留，要求润色时才修改。缺少人物/合作方素材时不要虚构。
3. 白底浅网格、只放双方 Logo 和 ×、无标题的合作图，读取 [极简双 Logo Partnership](references/partnership-minimal.md)，选 partnership-minimal 与 partnership-soft-grid / light；如果用户要求更明显的 BlockSec 橙色渐变，改用 partnership-orange-grid / light，并读取 [暖橙渐变 Partnership 指令](references/partnership-orange-grid.md)；示例分别为 assets/example-partnership-minimal.json 与 assets/example-partnership-orange-grid.json。其余选择 hero（发布/文章）、partnership（原合作布局）、partnership-centered（居中合作）、quote（观点/人物）布局，独立选择底图和 dark/light 主题。新建合作封面默认 partnership-centered，推荐 radial-grid-symmetric；已有项目保留其布局，用户只换背景时不要改文字对齐。OSL 绸缎选 soft-satin；纹理均匀对称、标题与说明居中的合作图选 radial-grid-symmetric。其他风格为 hex-outline、hex-glow。首次未指定主题默认 dark；浅色/白底使用 light。
4. 生成内容 JSON，示例为 assets/example-content.json；居中合作图使用 assets/example-partnership-centered.json。运行 scripts/render_cover.py --content CONTENT.json --project OUTPUT_DIR。需要 Python 3、Pillow、fontTools；先检查环境。缺少依赖时安装或明确说明阻碍。中文必须选覆盖中文的字体，不能输出缺字方框。
5. 查看 PNG，检查换行、遮挡、比例、对比度。溢出时在许可字号范围内处理；无法容纳时让用户选择缩短文案或换布局，不静默截断。
6. 静态配图交付 PNG / WebP 与独立无字底图；用户要求动态时另导出 MP4 / GIF 与 poster。两者保留同一 project.json、content.json、background/、layout/、assets/、runtime/ 及 output/，动效另存可选 motion/。后续改文案读取原项目；多平台按资产模型执行 export，不能拿成图重新生成。仅有 PNG 无法可靠修改独立图层。

## 模板参数与命名

七套具名模板默认参数保存在 `assets/templates/`，索引为 `assets/templates/index.json`，名称为“文章封面｜横版”“合作公告｜左对齐横版 / 居中横版 / 极简双 Logo 横版”“观点人物卡｜横版”“嘉宾金句｜竖版”和“活动概要｜竖版”。每次成功出图在项目 `content.json` 中保存完整模板副本及 `layer_overrides`，后续修改优先读取项目副本，保留该图片的位置与大小调整。

用户要求调整位置、大小、字号或对齐时，读取 [模板名称与参数](references/template-parameters.md)，使用 `--layer` 调整具名元素（例如 `speaker-portrait` / 嘉宾人物、`main-title` / 主标题），而不是修改共享模板或在脚本内改坐标。只改文案/素材时保留这些参数；明确要求恢复某个元素时使用 `--reset-layer`。旧配置下次渲染自动补齐模板副本，保持原排版。localhost 编辑器尚未实现。

## 局部修改

已有 --project 不传 --content 即读取已保存配置。

```bash
python SKILL_DIR/scripts/render_cover.py --project PROJECT_DIR --set 'title=替换后的完整标题'
python SKILL_DIR/scripts/render_cover.py --project PROJECT_DIR --asset 'image=/absolute/path/screenshot.png'
python SKILL_DIR/scripts/render_cover.py --project PROJECT_DIR --background /absolute/path/new-background.png
python SKILL_DIR/scripts/render_cover.py --project PROJECT_DIR --theme light
```

- “只改标题”：只改 title，允许框内重新换行/适配字号；保留其他文字、底图、素材和布局。
- “换人物/截图”：只改 image；“换 Logo”只改 logo 或 partner_logo。
- “换背景”：保留文字和素材，新底图必须适合当前布局留白。
- “换风格”：默认仅背景并说明；不要擅自换掉整个排版。
- “改为浅色/深色”：使用 --theme light/dark，保留文案、布局和图片，切换成对应预设底图及文字配色。自定义/生成的背景不会自动变色；切主题会回到同风格预设，需要保留自定义风格时先生成对应主题背景，再同时传 --background。
- 切浅色后检查 Logo 可读性；白色 Logo 应替换成用户提供的正式深色/彩色版本，不自动反色或重绘。
- 用上一张 PNG 作为视觉检查依据，不能重新生成整张位图来修改文字。

## 底图来源

读取 assets/backgrounds.json。常规 16:9 四种预设各有深浅两版，共八张底图；另有仅浅色的 partnership-soft-grid 与 partnership-orange-grid 极简合作底图；`portrait_presets` 有三张当前推荐的固定 3:4 底图，另保留三张旧版以兼容已有项目；浅色在各预设的 themes.light 下。public_url 尚未配置，不编造链接或称已发布。管理员将无字 PNG 放在公开 HTTPS 静态地址后填入对应主题链接。渲染器优先下载，失败则使用打包底图并提示。链接直接返回图片，无需登录。

显式 --background 支持本地 PNG/JPG 或 HTTPS 图片地址；失败时停止，不悄悄替换。仅预设允许本地回退。

## 生成新背景

用户要求“从零绘制 / 根据参考图和素材新绘制底图 / 重新生成底图 / 新增背景风格”时，必须调用当前会话的原生 `image_gen`（或宿主提供的同等原生 `image_generation` 工具）。已有参考图和素材作为图像生成或编辑的输入，先查看实际图片并遵守工具的输入要求。网格、圆弧、六边形、渐变和光晕等几何底图同样走此流程，不用 Python/Pillow、SVG、Canvas、CSS 或资产构建脚本绘制替代。

程序仅用于已有独立图层与素材的排版合成，包括准确文字、官方 Logo、人物透明 PNG、截图、已生成底图，以及合成所需的等比缩放、位置调整、透明度与格式转换。把已有原图的装饰图层重排并扩展纯色留白属于素材合成；根据参考图新画纹理、形状、光影或主体属于图像生成。

原生图像工具不可用、失败或没有返回可用图片时，明确说明新底图尚未完成并保留现有项目；不得改用程序绘制，也不得自动用预设代替本次新绘制请求。可交付提示词用于后续重试，但提示词不算生成成品。普通配图和“选取合适背景”仍复用已有底图。

读取 [背景生成规范](references/background-generation.md)，按当前 dark/light 主题生成无字、无 Logo 的 16:9 背景。查看结果并检查留白，再将路径传给 --background，以同一配置合成文字。换主题时同时传 --theme，保证文字配色匹配背景。禁止用 Python 修改用户照片或 AI 生成图的内容；脚本仅合成独立图层。

保存新背景到项目；用户未明确要求加入共享库时不发布、不覆盖公共预设。

## 质量约束

- Logo 原样使用，保留透明度和比例；各产品 Logo 保持原色，包括 MetaSuites 绿色、MetaSleuth 棕金色和 Phalcon 蓝色，不因 BlockSec 海报配色而染色。产品 Logo 原色不自动扩展为背景与装饰色。没有正式素材就省略，不用普通字体冒充官方 Logo。
- 新绘制背景/插画必须调用原生 `image_gen`；程序仅合成已有图层与准确文字，具体边界见上方“生成新背景”。
- 少量大字、充足留白；不混入 OSL 荧光绿色。
- 配色服务于内容气质、视觉重心与信息层级；单蓝、单橙、蓝橙组合，以及呼应 BlockSec 黑色 Logo 的纯黑 / 黑白灰方向均可独立成立。不要求同时使用蓝橙，也不默认添加渐变、光晕或装饰；可用纯色、同色明暗层次和留白建立完整画面。优先明确的主色、克制的色彩数量与稳定的明暗关系，避免为体现品牌而堆叠颜色。参考合作图的紫色不自动成为 BlockSec 品牌色；合作方 Logo 保留原色。
- 深浅主题均围绕所选配色独立设计，以文字可读性、Logo 辨识度和整体平衡为准。浅色可以是白 / 浅灰、淡蓝或淡橙，也可以采用黑白灰排版；标题、正文与小字强调按层级选择对比充分的颜色，不强制使用深蓝标题、灰蓝正文或橙色强调，不机械反转深色图。单色方向不为“补齐品牌色”添加另一种颜色。
- 纹理默认极低对比度，第一眼先看见文字，第二眼才察觉材质。偏侧绸缎保留右侧宽、浅、软的折线；左侧约 65%、中央横带、底部正文与 Logo 区近乎平坦。避免强反光、明暗断层、密集布纹。居中对称网格围绕画布中心均衡展开，中心抑制细线聚集，不能形成明亮或密集焦点。居中合作版 Logo 组合、标题、说明沿同一中心轴排列。
- “纹理再淡一些”：保留文案、布局和素材。独立的已有纹理图层可在合成时调低透明度；需要改变底图像素内容时调用原生 `image_gen` 编辑，绸缎和几何网格均适用。检查最小字号正文局部对比度，不改已确认文案来迁就底图。
- 不把参考中的名字、合作方、数字和承诺当新图事实。
- 常规封面保留原四种 16:9 布局、四种底图预设各深浅两版；另增 partnership-minimal 双 Logo 布局及仅浅色的 partnership-soft-grid / partnership-orange-grid 底图变体；嘉宾金句新增独立 3:4 模板，其他平台尺寸使用项目平台配置与专属模板派生，精细编辑按既有图层能力处理。
