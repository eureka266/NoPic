# Changelog

## 2026-10-16

- 新增 NoPic 品牌素材包协议，支持用带 `manifest.json` 的 ZIP 分发正式 Logo、无字底图、参考图、字体和示例项目。
- 新增 `scripts/install_brand_pack.py`，把品牌包安装到当前项目 `.nopic/brand-packs/` 并写入激活配置；同事无需指定 skill 安装路径。
- 新增 `scripts/create_brand_pack.py` 和品牌包 manifest 模板，支持从经过整理的素材目录生成可移植 ZIP。
- 工作台启动器现在自动发现激活品牌包，并将项目路径、品牌包路径传给本地服务。
- 工作台动态显示品牌包中的底图和默认 Logo，并在静态渲染时使用包内素材。
- 更新 skill、README、详细使用手册和 Codex 工作台协议，明确“自然语言调用 → 右侧面板 → 品牌包 → 当前会话”的使用流程。
- 保留品牌包版本、路径安全校验和 `reference_only` 语义；不覆盖同版本但内容不同的已安装包。
