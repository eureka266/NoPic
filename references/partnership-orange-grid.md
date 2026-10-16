# BlockSec 暖橙渐变 Partnership 风格

这是 `partnership-minimal` 的第二个视觉皮肤，保留同一套三层结构和 Logo 相对位置，只替换底图与生成指令。适合“只展示两家公司 Logo + ×”的 Partnership 图，也适合用户先用图像工具创作底图，再由渲染器叠加正式 Logo。

## 模板调用指令

```text
使用 $blocksec-social-cover 制作一张暖橙渐变风格的 BlockSec Partnership 合作图：使用 partnership-minimal 模板和 partnership-orange-grid 底图，只保留两家公司官方 Logo 与黑色 ×，Logo 沿中心水平线排列；白底浅网格，左下橙珊瑚渐变，右上琥珀橙渐变，最左侧只保留轻微 BlockSec 蓝色平衡。不要标题、日期、说明、绿色、紫色、霓虹效果或重新绘制 Logo。
```

## 默认资产

- 底图 ID：`partnership-orange-grid`。
- PNG：[assets/backgrounds/partnership-orange-grid-light.png](../assets/backgrounds/partnership-orange-grid-light.png)。
- 可编辑源：[assets/backgrounds/partnership-orange-grid-light.svg](../assets/backgrounds/partnership-orange-grid-light.svg)。
- 内容起点：[assets/example-partnership-orange-grid.json](../assets/example-partnership-orange-grid.json)。
- Logo 和 × 的位置沿用 [partnership-minimal.md](partnership-minimal.md)：左 Logo 中心 `(26.25%, 50%)`，右 Logo 中心 `(73.75%, 50%)`，× 中心 `(50%, 50%)`。

画面使用白底和极淡方格，中央横向区域保持安静。左下与右上使用橙色、琥珀色和暖白渐变，边缘保留一小段低饱和 BlockSec 蓝色作为冷色平衡。不要使用绿色、紫色、荧光色或高饱和渐变；不要把光晕放到 Logo 后面形成脏色块。

## 推荐生成方式

新绘制时必须调用原生 `image_gen` / `image_generation` 生成无字底图，不用 SVG 或 Pillow 新画网格与渐变；正式 Logo、× 和任何准确文字由模板渲染器作为已有素材图层叠加。这样能避免 AI 改写公司名称或 Logo 几何。生成后检查 1600×900 比例、中央 Logo 安全区和四周渐变强度，再通过 `--background` 或 `background_id` 使用。

### 底图提示词

```text
Create a finished 16:9 background only for a premium BlockSec partnership announcement, 1600x900 or larger. Use a nearly white warm-neutral canvas with an exceptionally faint thin square grid across the full frame. Keep a large quiet white horizontal logo-safe band through the middle, approximately x 9%-91% and y 28%-72%, with no focal object and no texture crossing the logo area.

Use BlockSec-inspired blue and orange color language, led by soft orange gradients: a gentle orange-coral glow enters from the lower-left edge, a pale amber and warm-orange wash sits in the upper-right corner, and a very restrained powder-blue accent appears only at the far left edge for cool balance. The transitions should be broad, matte, translucent and softly defocused, with organic curved boundaries similar to a modern editorial partnership graphic. Keep the center almost white.

Minimal institutional Web3 security brand, calm premium layout, clean white negative space, subtle grid, delicate edge color, no shadows, no perspective, no 3D objects, no saturated green, no purple, no neon, no dark background. Absolutely no words, no letters, no company names, no logos, no multiplication sign, no icons, no watermark, no mockup.
```

### 完整 Partnership 构图提示词

如果用户想让图像工具直接给出完整构图，可以使用下面提示词；正式发布时仍建议把 Logo 从官方素材重新叠加到同一底图上。

```text
Create a premium 16:9 BlockSec-style partnership announcement composition on a nearly white background with a very faint square grid. Place two provided official logo image references in one perfectly centered horizontal row: [BLOCKSEC_OFFICIAL_LOGO] on the left and [PARTNER_OFFICIAL_LOGO] on the right, separated by a clean thin black multiplication cross. Keep the logo row centered at y=50%, with the left logo center at x=26.25%, the cross at x=50%, and the right logo center at x=73.75%. Preserve the supplied logo artwork exactly, including spelling, proportions, colors, and transparent edges.

Use broad soft BlockSec orange gradients around the edges: orange-coral at the lower left, pale amber-orange at the upper right, and only a faint powder-blue accent at the far left. Keep the entire central logo band bright, white and low contrast behind the logos. Refined editorial Web3 security partnership announcement, spacious, understated, crisp dark logos, no extra copy.

Do not invent or redraw any logo. Do not add a title, subtitle, date, badge, icon or watermark. No green, no purple, no neon, no heavy glow behind the logos, no perspective distortion, no mockup.
```

## 渲染命令

```bash
python scripts/render_cover.py \
  --content assets/example-partnership-orange-grid.json \
  --project OUTPUT_DIR \
  --asset 'logo=/absolute/path/blocksec-official-dark.png' \
  --asset 'partner_logo=/absolute/path/partner-official.png'
```

用户自行生成底图后，可直接替换背景而不改变 Logo 位置：

```bash
python scripts/render_cover.py --project OUTPUT_DIR \
  --background /absolute/path/user-created-background.png
```

用户需要有标题、说明或活动信息时，切换到 `partnership-centered`，不要把文案塞进这个无文字模板。
