# 极简双 Logo Partnership

适用请求：参考白底网格 + 边角柔光 + 中央双 Logo 的合作公告，或“只放两家 Logo 和 ×”“不要标题”。使用 `partnership-minimal`；有大标题与说明的合作图仍使用 `partnership-centered`。本模板为独立新增版，不替换旧模板默认值。

## 固定资产

- 底图 ID：`partnership-soft-grid`，仅浅色主题；`assets/backgrounds/partnership-soft-grid-light.png`，1600×900。可编辑源为同名 `.svg`。白底、淡蓝左下柔光、淡橙右上柔光、浅网格。
- 视觉变体：`partnership-orange-grid`，仅浅色主题；使用 BlockSec 暖橙渐变、琥珀色右上柔光和少量蓝色边缘平衡。完整生成指令见 [BlockSec 暖橙渐变 Partnership](partnership-orange-grid.md)。
- 模板：`assets/templates/partnership-announcement-minimal.json`。
- 内容起点：`assets/example-partnership-minimal.json`。默认无标题、无标签、无说明；不从风格参考中继承公司、合作事实或文案。
- 连接符：`assets/marks/partnership-cross-ink.png`，另有 `white` / `orange` 两版；均提供透明 256×256 PNG 和独立 SVG。浅底默认 ink，不使用系统 emoji，避免字体和设备改变形状。
- 收件参考只用于风格，不提取其 Elliptic / Internet Computer Logo。正式 BlockSec 与合作方 Logo 由用户提供；保留原色、透明度与宽高比。浅底用官方深色或彩色版本。

底图只需入库一次。替换 Logo、修改相对位置或调整乘号均复用该 PNG。没有双方正式 Logo 时可交付底图、模板和参数，不把空图当完整合作公告；渲染器会提示缺少的 Logo。

## 位置与比例

原点在左上，像素为权威参数，所有元素垂直中心为 y=450。图片先去除透明边距，再等比例放入容纳框。可见 Logo 的宽高取决于原素材比例，不拉伸以填满框。

| 元素 | 图层 ID | x, y | 容纳框宽×高 | 相对画布中心 | 相对画布宽×高 |
| --- | --- | --- | --- | --- | --- |
| BlockSec（左） | blocksec-logo | 160, 360 | 520×180 | 26.25%, 50% | 32.5%, 20% |
| 合作方（右） | partner-logo | 920, 360 | 520×180 | 73.75%, 50% | 32.5%, 20% |
| × | partnership-separator | 772, 422 | 56×56 | 50%, 50% | 3.5%, 6.22% |

Logo 容纳框中心间距 760px（画布宽度 47.5%），各自与乘号框水平间隙 92px；两侧安全边距 160px。模板的 `relative_geometry` 记录这些派生参考值；实际渲染使用 `layers`，单图覆盖保存至 `layer_overrides`。该参考值不会随单图覆盖自动重算。

## 出图与单图修改

用实际绝对路径替换以下占位路径。两个 Logo 参数分别为 `logo` / `partner_logo`；乘号默认自动载入并复制到项目，不必另传。

```bash
python SKILL_DIR/scripts/render_cover.py \
  --content SKILL_DIR/assets/example-partnership-minimal.json \
  --project OUTPUT_DIR \
  --asset 'logo=/absolute/path/blocksec-official-dark.png' \
  --asset 'partner_logo=/absolute/path/partner-official.png'

# 右 Logo 向左移动 40px、缩小容纳框；保留当前底图与其他元素。
python SKILL_DIR/scripts/render_cover.py --project OUTPUT_DIR \
  --layer 'partner-logo.x=880' --layer 'partner-logo.width=480'

# 调整乘号大小时同时修改 x/y，保持中心点在 (800, 450)。
python SKILL_DIR/scripts/render_cover.py --project OUTPUT_DIR \
  --layer 'partnership-separator.x=776' --layer 'partnership-separator.y=426' \
  --layer 'partnership-separator.width=48' --layer 'partnership-separator.height=48'

# 替换乘号素材；恢复位置用 --reset-layer partnership-separator。
python SKILL_DIR/scripts/render_cover.py --project OUTPUT_DIR \
  --asset 'separator=/absolute/path/custom-cross.png'
```

渲染项目保存双方 Logo、乘号、底图与完整模板副本。后续只改 Logo 时保留各图层位置。该布局没有文本槽位，收到文案时明确切换到有标题的模板，不默默丢弃文案。只提供浅色底图，不使用 `--theme dark` 自动变出深色；需要另一主题时选择已有背景或明确提供新背景与适合该背景的 Logo / 乘号。

## 维护资产

现有打包底图为历史原生 SVG 网格与渐变资产，PNG 可直接复用。这个来源说明不构成程序绘制新底图的许可；用户要求从零或根据参考图与素材新绘制时，必须调用原生 `image_gen` / `image_generation`，工具不可用时不得以程序重建兜底。

`scripts/build_partnership_assets.py` 保留为历史资产实现，不在新底图制作链路中调用。程序仅用于已有底图、正式 Logo、独立 × 和文字图层的排版合成。保留既有 PNG、SVG 与预设，不自动同步安装目录。
