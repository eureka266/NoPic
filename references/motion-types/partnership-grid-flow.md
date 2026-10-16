# partnership-grid-flow：合作网格循环

适用于 partnership / partnership-centered 合作海报，以及具有相似固定前景和网格背景的静图。默认复用已确认母版与配色；需要时把真实独立层或背景序列接入同一个 cover project，再执行本配方。核心是 **前景保持完整、背景纹理低强度持续流动**；从第一帧起就是完整可读的合作海报，无入场和退场。

## 参考中实际看见的运动

参考来源：用户提供的 `x-downloader.com_hecOcg.mp4`，1920×1080，约 5.06 秒，视频流 34 fps。抽帧见 [时间序列](../../assets/references/partnership-grid-flow-contact-sheet.jpg)，每 0.25 秒一帧。该图仅供运动分析，不是可直接使用的底图；执行本类型不依赖原视频在用户 Downloads 中的路径。

| 元素 | 参考观察 | 可复用规则 |
| --- | --- | --- |
| 顶部合作公告文字 | 全程固定 | 原图的所有标题、说明与标签固定，不限定放在顶部 |
| 左右机构 Logo | 全程固定，比例与位置稳定 | 复用正式 Logo，保持原色、锐度和对齐 |
| 中央「×」 | 位置、角度和形状固定 | 原图有分隔符则保持，无分隔符不新增 |
| 背景 | 深色底与左右对称的透视面轮廓固定；面内竖网格线持续向左右外侧平移 | 固定底色、遮罩边界和汇聚结构，只改变纹理相位 |
| 镜头与构图 | 固定机位，完整画面持续展示 | 不推拉、摇移或切镜，不让整张海报一起动 |

上述是抽帧可见现象；原文件的具体工程、遮罩方式、速度曲线与无缝循环质量无法由成片确定。下面的实现方式和参数是用于复现的建议，不宣称是原作者方案。没有观察到需要复刻的 Logo 旋转、中央「×」绘制、粒子爆发或标题逐字出现。

参考中的紫色、荧光绿、ELLIPTIC 和 GNOSIS PAY 仅属于参考。制作 BlockSec 动图时保留已确认母版，单蓝、单橙、蓝橙、黑白灰均可；只有用户要求换风格时才调整。沿用输入静图的正式合作方和全部文案，不将参考配色或机构复制过来。

## 共用静态母版

先检查现有静态母版，不因启用动态版本重做背景或配色。前景来自同一 content.json 的准确文字 / 正式 Logo / 人物素材，运动源保存到项目 motion/。只有用户明确要求换风格时，才按 [可选风格调整](../static-style.md) 执行；颜色选择与运动类型相互独立。

执行接入、schema 和真实命令见 [统一静态 / 动态工作流](../static-to-motion.md)。规则平移网格可用 layer-loop；复杂透视可由 HyperFrames 输出纯背景序列后接入 background-frames。程序不得为了动画新画纹理或网格，必须复用实际素材；无法取得独立层时报告限制。

## 运动配方

- **固定层**：原图底色/渐变、背景几何外轮廓、所有文字、双 Logo、分隔符、布局和镜头。前景不缩放、不浮动、不渐隐，第一帧完整展示。
- **运动层**：原背景中低对比的网格线或线性纹理。参考式左右透视面采用镜像运动：左面竖线向左、右面竖线向右，仿佛从中央向外流动；导向中央的斜线和面边界固定。新线从固定遮罩内自然补入，不能留下空白或在接缝突然出现。
- **适配原图**：已有圆弧/放射网格时保留原结构，可采用网格间距的周期相位流动；均匀矩形网格采用匹配原构图的平移。适配属于本类型的延伸，不是参考视频原样复刻。纯绸缎、照片或无纹理底图不默认适用；不为套用配方生成新背景或添加 X 形隧道。
- **节奏**：低强度、匀速、不抢文字。参考式规则网格可从每 5 秒移动 1 个重复单元开始；原参考的精确速度未测定，实际速度以源图网格密度、尺寸和可读性为准。纹理的线宽、对比度与原图一致，不自动增加光晕、呼吸、扫光或粒子。
- **循环**：位移为重复单元的整数倍，线性时间推进；两侧共用相位、方向相反。规则网格可用 `phase(t) = (cycles × t / duration) mod 1` 驱动一个重复间距的偏移。确保图案在周期边界等价；需要透视时先在网格局部平面做周期，再通过固定透视变换/遮罩映射。不能用终点突然回原位、整图交叉淡化或来回倒放掩盖循环接缝。
- **前景保护**：运动层置于准确的文字/Logo 前景之下。不要把包含 Logo 的扁平海报直接当运动纹理。静态背景中已有的网格应由同一套动态网格替代或分离，避免原网格与新增移动网格叠在一起产生重影。

## 可直接使用的中文提示词

将占位项替换为实际输入；只有左右透视面时使用“左右镜像”这一句，其他网格采用上面的适配规则。

```text
将已确认的 partnership 配图母版派生为时长 {duration_seconds，默认5} 秒的无声循环动图，默认保留原配色与背景。保持原图 {width}×{height} 尺寸、画幅比例、构图关系、文案事实和 Logo 身份；不因启用动效重做背景、装饰或配色；换风格需用户明确要求。

从第一帧开始完整呈现原海报。所有标题、说明、标签、两侧官方 Logo 和已有的中央合作分隔符全程固定，保持原有文字内容、字形、位置、大小、间距、清晰度、Logo 颜色与比例。镜头固定。

只让原背景的低对比网格纹理缓慢、均匀、连续流动。若原图是左右对称透视网格，左侧网格竖线向左外侧移动，右侧向右外侧移动，速度一致、方向镜像；固定透视面边界、汇聚点、斜向导线和所有前景。纹理运动始终限制在原有背景区域内，不新增几何场景，不盖住文字或 Logo，不让原静态网格与动态网格重叠产生重影。若输入是其他网格结构，沿其原有几何方向运动，并保持原版式。

全片保持同一完整画面与低强度匀速节奏，无入场、退场和切镜。以可重复的纹理相位构建无缝循环，播放到尾部后能自然继续到开头；不要通过整张图淡出、回弹、倒放或突然复位制造循环。

输出 {format，默认MP4}，{fps，默认30} fps，无音轨。优先保证文字和 Logo 的准确与稳定，再保证背景运动细腻连贯。
```

## English image-to-video prompt

```text
Animate the approved partnership cover as a subtle {duration_seconds}-second seamless loop, preserving its existing color direction and background. Preserve the original resolution, aspect ratio, composition, exact copy, and logo identities; do not rebuild the background or decorative treatment unless the user explicitly requests a style change. Show the complete poster from the first frame.

Lock all text, official logos, and the existing partnership separator in place. Preserve their exact wording, letterforms, geometry, spacing, sharpness, colors, and proportions throughout. Use a locked camera.

Animate only the existing low-contrast background grid. For a mirrored perspective layout, move the left grid's vertical lines slowly outward to the left and the right grid's vertical lines outward to the right at equal, constant speed. Keep the perspective boundaries, vanishing point, diagonal guide lines, background fill, and foreground unchanged. Confine the moving texture to the original background surfaces. For another existing grid structure, follow its original geometry without redesigning the poster. Avoid doubling the original static grid with a second moving grid.

Maintain one fully readable composition, with no entrance, exit, cuts, or global zoom. Build a continuous periodic texture loop with matching phase at the loop boundary. Do not reset the image, reverse playback, or fade the entire poster to hide the seam. Export a silent {format} at {fps} fps.
```

**负向约束（按执行引擎并入提示词或负向提示字段）**：不重绘/拼错文字；不变形、旋转、缩放或替换 Logo；不移动合作分隔符；不改变配色；不生成新背景；不整图推拉；不增加握手、人物、3D 物体、粒子、闪烁、扫光、额外光晕或旁白；不突然跳帧、黑屏、渐隐或倒放。

## 给可控合成执行器的提示词

```text
按 partnership-grid-flow 配方制作动画，复用输入静图项目的准确素材与排版，不重新设计。

先标出固定底色/几何层、可重复网格纹理层与原始文字/Logo 前景层。保持所有前景和镜头恒定，只以线性时间驱动网格的周期相位；左右透视面共用同一相位并采用镜像方向，纹理限制在固定的原图遮罩中。其他网格沿源图几何适配。

根据网格的重复间距设置一个周期内的整数单元位移，避免边缘露空、网格重影、遮罩矩形痕迹与循环停顿。背景线条保持原强度，不额外增加动效。

导出前核对首帧构图、前景稳定性、运动中可读性、t=0 与 t=duration 的周期等价以及连续两轮播放。保存实际素材、遮罩、动画源文件和 motion.json。若输入只是扁平 PNG 且无法可靠分离背景，报告素材限制，不宣称已取得独立图层或高保真动画。
```

## 验收重点

- 一眼仍是用户确认的原合作海报；任意时刻都能读完文字和识别双方 Logo。
- 只有背景纹理在动；中央分隔符、Logo、标题以及透视面外轮廓没有漂移或闪动。
- 左右节奏平衡，中心无线条堆积；背景没有比原图更亮、更密，也没有静动态网格重影。
- 连续播放两轮无可见接缝；实际导出文件、时长、尺寸和音轨符合记录。参考本身的循环接缝不作为合格证明。
- AI 图生视频即使接收了以上提示词，也必须逐帧抽查文字/Logo；发现漂移时优先回贴准确前景或改用可控图层合成，不能仅凭提示词宣称保真。
