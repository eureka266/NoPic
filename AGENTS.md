# 工作空间约定

此目录维护 blocksec-social-cover。用户提供的背景原文件优先，普通配图请求复用已有底图；仅在用户明确要求新背景时生成，不因“选取合适背景”自行生成。更换背景或文案时遵守用户指定的修改范围。

当用户要求从零或根据参考图与素材新绘制底图时，必须调用原生 `image_gen` / `image_generation`，包括网格、渐变等几何背景；不得用 Python/Pillow、SVG、Canvas、CSS 或背景构建脚本替代。程序仅合成已有图层与素材及完成合成所需的等比缩放、位置、透明度与格式处理。工具不可用或无可用图片时说明新绘制尚未完成，保留现有项目，不自动以程序或预设兜底。

用户手动放入或通过聊天提供的新底图先收集到 inbox/backgrounds/，保留原文件。需要正式入库时将选定文件存入 assets/backgrounds/，同步更新 assets/backgrounds.json。区分可直接使用的原始底图与仅供风格参考的图片。

保留原有预设与原文件，不静默覆盖同名素材。仅在用户要求安装或同步时更新本地技能安装目录。

嘉宾金句与 seminar 概要使用 assets/backgrounds.json 的 portrait_presets 中固定 3:4 PNG；优先使用根据 inbox/backgrounds 原图适配的 portrait-data-glow、portrait-diagonal-light、portrait-gradient-spheres，旧版预设保留兼容。每次制作默认复用；只有使用者明确要求生成新底图时才调用 AI。选定底图后写入项目并保持，修改金句、人物或 Logo 不触发背景重生成。

官方 BlockSec 及旗下产品 Logo 使用副本保存到 assets/logos/，按 blocksec、metasleuth、metasuites、phalcon、phalcon-compliance 子目录与品牌-形态-颜色命名，保留原文件与各版本；新增素材登记 assets/logos/index.json。制作前先读索引，先匹配品牌，再按目标背景和 brand_defaults 选择完整 Logo 或用户指定的独立图标，使用 render_file。BlockSec 深底默认 blocksec-white，浅底默认 blocksec-dark，用户指定版本优先。以实际颜色为准，旧版名称含 white 的 SVG 可能是深色版本；各产品 Logo 保持原色，不以工作空间图标或普通字体冒充。Media Kit 辅助素材登记 assets/media-kit.json，含 Logo 或文字的横幅不能作无字底图。Phalcon Compliance 已有独立 SVG 与透明 PNG，浅底默认 phalcon-compliance-lockup-dark，查 brand_status；此前 phalcon-compliance-brand-banner 保留为参考横幅；reference_only 为 true 或 usable_as_standalone_logo 为 false 的条目不能作为 Logo 图层，通用 Phalcon 标识不自动替代本产品专属版本。

用户提供的非背景原始素材（Logo、人物照片、截图、文案、参考图）统一收集到 inbox/materials/，按香港日期和用途建立有意义的批次，保留原文件名与原内容。已手动放入的文件不移动、不覆盖；整理与制作使用副本。正式 Logo 使用副本存入 assets/logos/，原照片与透明抠图分开保存。README 完整模板示例必须使用用户允许用于示例的素材，不能用参考海报或无字底图替代。
