# 静态与动态配图：同一项目，按需呈现

静图与循环动图属于同一种配图资产。先确定内容类型，再选择 `static` / `motion` 呈现方式和目标平台；不因 X / LinkedIn 的投放场景另建动画项目体系。`/animate-cover` 是兼容对话入口，默认在现有 cover project 中附加动效，保留已确认背景、文案、Logo、版式和配色。

## 交付维度与范围

- `mode=background-only` / `full-cover`：决定是否含文案、Logo 等前景。既有 CLI `--mode both` 表示完整封面及其纯底图，不是“同时出静动图”。
- `presentation=static` / `motion` / `both`：决定导出静态、动态或两种呈现。默认 static，用户明确要动图才执行 motion。
- 平台：同一 `layout/platform-layouts.json` 管理尺寸、版式、安全区和 `motion_export`；不声称各平台支持完全相同的文件格式、时长或播放行为。具体投放要求优先用户提供的规格，核对当前平台要求时再查官方资料。

完整封面的动态导出同时保存无字背景动画与含前景的完整动画；纯底图模式只导出背景动画。两者均保留可重编译项目。制作默认 5 秒、30 fps、无声循环 MP4；用户可要 GIF，或静态 PNG / WebP 与 MP4 / GIF 同时导出。这些是内部制作默认值，不是平台强制规格。

## 工作流

1. 读取原 `project.json` 和 `content.json`，检查确认母版与实际独立图层。默认 `style=preserve`；只有用户要求换风格时读取 [可选风格调整](static-style.md)。单蓝、单橙、蓝橙、黑白灰方向都可用，不强制重新风格化。
2. 按现有结构选动效，列明固定层、运动层、方向、速度与周期。首个配方为 [partnership-grid-flow](motion-types/partnership-grid-flow.md)：前景固定，已有网格 / 线性纹理运动。名字沿用合作示例，是否适用由图层结构判断，不只由内容类型判断；无网格的照片、绸缎或纯色底不自动套用。
3. 复用已有素材准备实际动画源。程序只移动 / 合成已有纹理与遮罩，不画新网格、不从扁平海报猜图层。需要新绘制时仍必须有用户的明确要求并调用原生 image_gen；工具失败不以程序或预设兜底。无法分离时保留可编辑静图与缺失素材说明，提示词不算动态成品。
4. 用下面的 motion 命令把配置和源素材收进同一项目；统一 export / rebuild 负责重新合成当前文案前景、按平台编码。只改标题不会重新生成底图或背景动画源。
5. 检查 poster、首 / 中 / 末帧、连续两轮播放、文字与 Logo 稳定性、循环接缝及实际导出参数。只渲染 `0 ≤ t < duration`；额外的 t=duration 用于周期校验，不重复编码为末帧。

## 两种实际执行接入

### layer-loop：已有纹理层周期平移

内置 `render_motion.py` 只对已有 RGBA 纹理做周期位移、可选固定遮罩和透明前景合成，FFmpeg 编码 GIF / MP4。输入的固定底色、纹理和遮罩均为真实文件，尺寸对应 source_size。多个层可用相反位移和不同遮罩实现镜像运动；不生成纹理、透视面或场景。

纹理需有真实透明背景；offset 是一个完整周期内的像素位移，必须对应纹理重复周期。第零相位的图层合成需与项目已确认纯底图一致（允许 2 个 RGB 级别的重采样误差），否则拒绝导出，防止启用动画悄悄换背景或叠出双重网格。

输入 JSON 的相对路径从该 JSON 所在目录解析：

```json
{
  "schema_version": 1,
  "engine": "layer-loop",
  "type": "partnership-grid-flow",
  "style": "preserve",
  "source_size": [1600, 900],
  "base": "actual-static-base.png",
  "layers": [
    {"id": "background-grid", "file": "actual-transparent-grid.png", "offset": [80, 0]}
  ],
  "duration_seconds": 5,
  "fps": 30,
  "formats": ["mp4"]
}
```

路径和 offset 仅示意，必须替换为真实图层和验证过的周期。不能把完整海报填入 texture，不能把已烘焙纹理的底图与相同动态纹理叠加。

### background-frames：接收 HyperFrames 等执行器的背景动画

复杂透视或其他需外部执行器的运动，按可用 `hyperframes` 技能制作**无字、无 Logo 的背景序列帧**，把工程保存在同一项目 `motion/` 的有意义子目录中。通过以下配置接入统一前景合成和编码，不把 HyperFrames 工程另建成内容 / 文案的来源：

```json
{
  "schema_version": 1,
  "engine": "background-frames",
  "producer": "hyperframes",
  "type": "partnership-grid-flow",
  "source_size": [1600, 900],
  "duration_seconds": 1,
  "fps": 2,
  "frames": ["actual-frame-0.png", "actual-frame-1.png", "actual-frame-2.png"],
  "formats": ["mp4"]
}
```

提供 `duration × fps + 1` 张实际帧，最后一张为 t=duration 的校验帧，需与首帧一致；第一张需复现确认底图。每张都是纯背景，前景由当前 content.json 重编译后叠加，改文案不需重做背景动画。输入与保存路径规则同 layer-loop。配置 schema 为 `assets/schemas/motion.schema.json`；当前已有配方仍只有网格循环，序列帧接入不代表新增一整套已验证动效类型。

本包实际执行的是分层合成 / 序列帧接入和编码，不附带 HyperFrames 安装包或自动生成其工程。外部执行器缺失时保留已有项目，不能说它已渲染成功；Carrot 仍是 [独立产品演示能力](product-motion.md)，不用于普通配图的背景运动。

## 统一命令

```bash
# 现有静态 cover project；不要求重建或复制另一套主题。
python SKILL_DIR/scripts/cover_project.py motion --project PROJECT_DIR --config ACTUAL_MOTION.json

# 同一个平台项目内同时交付静图与动图；底图 / 完整封面模式沿用原项目。
python SKILL_DIR/scripts/cover_project.py export --project PROJECT_DIR \
  --platform x --platform linkedin-horizontal --presentation both --format mp4 --format gif

# 同时刷新静图和动图中的标题，共享背景与动画源。
python PROJECT_DIR/runtime/cover_project.py rebuild --project PROJECT_DIR \
  --set 'title=新的确认标题' --presentation both
```

`motion` 命令保存项目内配置与源素材副本，不生成新背景，不渲染视频；`rebuild` / `export` 才执行。保存后 motion.json 里的素材路径相对于 cover project 根目录。CLI 默认 static，传 GIF / MP4 格式需明确 presentation=motion / both。请求 motion 时也保留静态 poster 和 PNG / WebP 以便预览和复用。

平台 variant 可含 `motion_export: {"formats": ["mp4"], "duration_seconds": 5, "fps": 30}` 覆盖导出参数；命令行 --format 优先。序列帧源的数量必须仍匹配时长与帧率。异画幅的完整封面需已有明确模板；动画源也需对应画幅，在该 variant 用 `motion_file` 指向实际平台动效 JSON，其中素材路径相对于母项目根目录。只对同画幅源做等比例适配，不拉伸整张成图或遮罩。

新项目清单 v2 记录 `foreground`、`motion`、`presentations`。既有 v1 可读取，下次成功渲染补齐 v2，不批量改旧项目。`content.json` 仍为 v2 且是唯一文案 / 版式来源。位置与素材修改继续使用原有渲染器，然后执行带 presentation 的 rebuild / export。

## 保存与验收

- `motion/motion.json`、`motion/assets/`：配置和原始运动源副本；外部动画工程也保存在 motion/，不删除原工程。
- `assets/foreground-<hash>.png`：静图和动图共用的精确透明前景，随文案 / Logo 修改重新编译。
- `output/background-only/{平台}.png|webp|mp4|gif` 与 `output/final-covers/{平台}.png|webp|mp4|gif`：沿用原交付目录；完整动画子项目仍在 `variants/full-cover/{平台}/`，不另建“动图内容类型”。
- `motion/poster.png`、`motion/last-render.json`：当前已渲染动态版本的首帧与实际参数，记录背景 / 前景源哈希。静态修改不会刷新旧视频；比较源哈希或重新导出，不能把旧 MP4 当成已更新。

同一主题的所有平台先在临时目录验证并渲染，全部成功才刷新该批结果；带 motion 的 rebuild 也先暂存文案、静图与动态结果。失败时保留之前成功的成品与文案；不保证设备断电或文件系统故障的原子性。整体迁移项目后可用 runtime/ 再编辑，动态编码仍需目标机提供 FFmpeg；本轮维护不自动安装或上传。
