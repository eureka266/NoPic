# BlockSec Logo 素材与索引

正式 Logo 使用副本保存在此目录，原始收件批次在 `inbox/materials/2026-10-14-brand-logos/`；源目录中的用户原文件保持不变。新增素材也可直接发给 agent，由其保留原文件、登记收件信息并更新 [index.json](index.json)。不覆盖同名文件。

## 已收录素材

| 索引 ID | 原始文件 | 实际颜色 / 适用背景 | 合成用 PNG |
| --- | --- | --- | --- |
| `blocksec-white` | [blocksec-logo-white-4k.png](blocksec/blocksec-logo-white-4k.png) | 白色透明 / 深色背景 | 原 PNG，2124×408 |
| `blocksec-dark` | [blocksec-logo-dark.svg](blocksec/blocksec-logo-dark.svg) | 黑色 / 浅色背景 | [blocksec-logo-dark.png](blocksec/blocksec-logo-dark.png)，2124×410 |
| `blocksec-ink` | [blocksec-logo-white.svg](blocksec/blocksec-logo-white.svg) | 深墨色 `#101820` / 浅色背景 | [blocksec-logo-ink.png](blocksec/blocksec-logo-ink.png)，2124×408 |
| `blocksec-ink-4k-alias` | [同一深墨色 SVG](blocksec/blocksec-logo-white.svg) | 原 4k 文件为重复副本，已去重 | 同一深墨色 PNG |

原收件中两份文件名含 `white` 的 SVG 实际为深色且内容完全相同；可用库仅保留 `blocksec/blocksec-logo-white.svg`，索引别名仍可引用。不能因原文件名用于深底。`4k` 是保留的原文件名，不代表 PNG 宽度为 4096，也不代表两份 SVG 是不同版本。SVG 导出的 PNG 保持原始路径、颜色、比例和透明度，没有重绘或反色。

## Media Kit 产品素材

新增 24 组完整 Logo / 独立图标，每组保留 PNG 和 SVG，按品牌存放：

| 品牌 | 目录 | 可用颜色 |
| --- | --- | --- |
| BlockSec | [blocksec](blocksec) | 黑、浅蓝、白 |
| MetaSleuth | [metasleuth](metasleuth) | 棕金原色、黑、白 |
| MetaSuites | [metasuites](metasuites) | 绿原色、黑、白 |
| Phalcon | [phalcon](phalcon) | 蓝原色、黑、白 |

命名为 `{品牌}-{lockup 或 icon}-{black / white / blue / color}.{png 或 svg}`。例如 `metasleuth-lockup-white.png` 是白色完整 Logo，`phalcon-icon-color.png` 是蓝色独立图标；`color` 的实际色值在索引中记录。Phalcon 白色完整 Logo 的原 PNG 为 348×104，合成默认使用同组 SVG 导出的 `phalcon-lockup-white-render.png`（2097×634）。

原文件按原名与目录结构保留在 `inbox/materials/2026-10-14-blocksec-media-kit/`。完整预览、辅助素材和使用边界见 [Media Kit 素材说明](../../references/media-kit.md)。此前收录的 Logo 也统一放在 `blocksec/`，索引 ID 保留兼容，重复 SVG 别名共用同一文件。

## Phalcon Compliance 专属 Logo

正式独立标识已保存为 [phalcon-compliance-lockup-dark.svg](phalcon-compliance/phalcon-compliance-lockup-dark.svg)，原 SVG 画幅 156×28，颜色为深蓝灰 `#202939`。同源透明 [PNG 副本](phalcon-compliance/phalcon-compliance-lockup-dark.png) 为 1872×336，按 12 倍等比导出，原形状、文字、颜色与透明度保持不变。

索引 ID 为 `phalcon-compliance-lockup-dark`，是 Phalcon Compliance 浅色背景的默认正式 Logo；可直接用于 Logo 图层。原下载文件 `1786089906947-2.svg` 保存在 `inbox/materials/2026-10-14-phalcon-compliance-logo/`，来源链接与 SHA-256 已登记。当前仅此深色版本，不自行反色或用 Phalcon 通用 Logo 替代。

此前 [含背景与宣传语的横幅](phalcon-compliance/phalcon-compliance-brand-banner.png) 继续以 `phalcon-compliance-brand-banner` 保留为参考素材，不放入 Logo 槽位。

## 调用与新增素材

- 制作前先读 `index.json`。先匹配用户指定品牌，再按 `brand_defaults` 选完整 Logo 或图标；用户指定版本优先，其次沿用项目保存的版本。未指定产品品牌的新项目使用 BlockSec，默认深底用 `blocksec-white`、浅底用 `blocksec-dark`。
- 索引的文件路径相对于本目录。`file` 是该条目的原素材使用副本，配对 SVG 在 `vector_file`，`render_file` 是图片文件路径；仅非参考且可独立使用的 Logo 可由 agent 写入配置或传给 `--asset logo=...`，渲染器不自动查索引。
- 新增版本登记 ID、品牌、文件、配对 SVG、实际颜色、完整标识或图标类型、适用背景、尺寸、透明度、合成文件、收件来源与 SHA-256。重复素材保留原文件并用 `duplicate_of` 说明，不误当成新设计。
- 优先完整横版标识（图形 + BlockSec 字标），保持官方比例。SVG 用矢量导出工具转为透明 PNG；不让 AI 重画 Logo，不自动反色，也不使用 `assets/icon.svg` 或普通字体冒充。

品牌规范或官方色值可随新素材提供。目前蓝 `#248BCC`、橙 `#FF7A1A` 仍是草案；本次深墨色 Logo 的 `#101820` 仅登记为素材实际颜色，不自动扩展为整套品牌规范。
