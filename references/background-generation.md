# 背景生成规范

只生成背景，不生成文字、图表、人物或 Logo。背景风格与布局独立，新图必须满足当前文本框留白。

从零或根据参考图与素材新绘制底图，必须调用原生 `image_gen` / `image_generation`，包括下方所有几何风格。程序仅合成已有图层与素材，不绘制新背景；工具不可用时不得用程序或预设替代。完整边界见 [主技能的生成新背景规则](../SKILL.md#生成新背景)。

## 深色主题提示词

先根据内容选择配色方向，再把该方向写入提示词；不把四种方向全部堆入同一张图：

- 单蓝：蓝色及其同色明暗层次，可配中性色，不强加橙色。
- 单橙：橙色可以成为主色，同色明暗与中性色组织层级，不强加蓝色。
- 黑白灰：呼应 BlockSec 黑色 Logo，以纯黑 / 近黑、灰阶与留白组织画面，允许完全没有彩色点缀。
- 蓝橙组合：明确主色与次色，按内容分配面积；不是默认渐变，也不固定成左下蓝光 / 右上橙光。

Create a textless 16:9 background for BlockSec using the selected color direction: {chosen direction and tonal range}. Build a clear visual hierarchy with deliberate negative space, controlled tonal contrast and restrained visual elements. A solid field or subtle same-hue variation is sufficient; add gradients, glow, geometry or texture only when they support the concept. Keep the selected typography and logo safe areas visually quiet; for the standard left-aligned hero layout, keep the left 58% and upper-left logo area clear. Position visual weight according to the actual layout rather than a fixed corner-lighting formula. Do not add a second brand color to a single-color or neutral direction. No lettering, numbers, logos, watermark, unrelated purple accents, neon green or dense circuitry. Output only the background.

## 浅色主题提示词

Create a textless 16:9 background for BlockSec using the selected light-theme color direction: {white/gray neutrals, light blue, light orange, or a deliberate blue-orange combination}. Use negative space, balanced composition and controlled tonal variation to support clear dark typography. A plain light field is valid; gradients, glow and decorative geometry are optional. Keep the actual typography and logo safe areas quiet; for the standard left-aligned hero layout, preserve the left 58% and upper-left logo area. Do not introduce both blue and orange unless the combined direction was selected. No lettering, numbers, logos, watermark, unrelated purple accents, neon green or dense circuitry. Output only the background. Design the light version on its own terms rather than inverting a dark image.

## 风格补充

下列带指定颜色的描述用于匹配已有底图版本，不构成所有新底图的配色要求。明确保留原风格时沿用；用户要求新的单蓝、单橙或黑白灰方向时，保留需要的构图 / 材质特征，替换配色描述。不要为了改规范而重生成或覆盖现有底图。

- hex-outline：Thin rounded hexagon outlines near the right and lower-right edges, subtle blue-gray lines with a small orange accent, flat restrained lighting.
- hex-glow：Soft blue light at the lower-left corner and orange light at the upper-right corner, nearly black central band, a subtle recessed hexagonal form on the right. Keep glows away from text and logo areas.
- soft-satin：Use the dedicated satin prompts below instead of adding hexagonal geometry. Generate a new image; never attempt to reproduce the raster texture with the geometric build script.
- radial-grid-symmetric：Distribute extremely faint concentric arcs and radial lines evenly around the center, with balanced density on both left/right and top/bottom. Suppress the spoke intersection in the center so no dense hub lies beneath the centered title. Keep centered logo, headline, subtitle and footer regions quiet. No directional corner spotlight, bright central halo or one-sided decoration. Use near-black/blue-gray in dark mode, off-white/pale blue-gray in light mode. Orange can come from separately composited labels. Use native image_gen to generate or redraw this geometric background; do not use the procedural build script as a substitute.

浅色版本按选定配色重新安排明暗：线条可以是中性灰或同色浅阶，光晕只在构图确有需要时使用，不默认补齐淡蓝淡橙。深浅版本保留所需布局和安全区，分别检查实际对比度。

partnership 改留白要求为：Keep the top logo area and the full central band from 25% to 72% height visually quiet and uniform in the theme's base color; move decoration to corners and edges。
quote 保持左侧安静，右侧将独立叠加人物，不生成一个人物。

检查生成图片没有字样、Logo、亮斑进入文本框。非精确像素可由合成脚本等比适配 1600×900；比例偏差超过 2% 时重生成，不静默裁切。背景影响可读性时优先修正背景。

公共库保存图片、风格 ID、尺寸、留白描述和版本。不要只保存 prompt；同一 prompt 不能保证重复生成同一底图。

## 低对比度绸缎提示词

当前打包版本由内置图像生成工具生成并调整。编辑现有绸缎底图时使用以下提示词；新生成时将 Keep the same 改为 Create，明确无字、无 Logo、16:9 和浅色/深色主题。实际尺寸与比例须检查，不假设模型精确遵从数值。

深色：Keep the same 16:9 dark satin composition, but make the ENTIRE image much lower contrast and nearly flat matte ink navy. Base around #0C121C, fold shadows/highlights around #0E1520 and #111A26 only. Treat cloth as a faint embossed suggestion, barely visible on first glance. Eliminate the bright orange right-edge light and all luminous blue ribbons; orange brand accents will be added later as separate typography. Reduce every fold highlight by a large amount, flatten sharp creases, remove deep dark troughs. Leave the entire left 65%, center horizontal band and footer area almost uniform. Keep only two broad shallow soft curves faintly visible on the far-right edge. No dramatic studio light, gloss, specular shine, saturated gradients, noise, added text, logos, objects or watermark. It is a quiet background, not a fabric hero illustration.

浅色：Keep the same 16:9 light satin composition, but reduce the ENTIRE image contrast much further. Base around #F6F8FB, faint fold shading only around #EFF3F7 and #F2F5F8. White-on-white matte silk impression, almost flat on first glance. Remove the noticeable blue right-edge shadows, pale orange corner gradient and bright white ribbon highlights; brand accents will be added as typography later. Leave the entire left 65%, central band and bottom-left footer area nearly uniform off-white. Keep only two extremely faint broad shallow soft curves near the far-right edge. No shiny satin gloss, sharp highlights, deep folds, dark creases, saturated colors, noise, added text, logos, objects or watermark. It is a quiet low-contrast background, not a textile hero image.
