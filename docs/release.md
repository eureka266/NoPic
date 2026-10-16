# 发布维护

README 面向首次使用的人，保留实验项目定位。实际安装标识仍是 `blocksec-social-cover`，展示名为「有图 NoPic」；发布到 `eureka266/NoPic`，不要因技术名不同创建第二个仓库。

## 文档插图

- `assets/partnership-example.png` 是 [通用演示成图](../output/prototypes/cover-workbench/demo-assets/cover.png) 的展示副本，复用已有底图；两侧分别为本品牌与“合作方”文字占位，不展示实际客户名称或 Logo，也不计作完整客户案例。[演示配置](../output/prototypes/cover-workbench/demo-assets/content.json)
- `assets/workbench.jpg` 是本地工作台真实截图。`YOUR BRAND` 与“合作方”均为文字占位；原型的能力边界见 [工作台说明](../output/prototypes/cover-workbench/README.md)。
- README 中的其他图片是底图素材，已明确标注，不计作完整成品。

更新展示副本（从仓库根目录执行）：

```bash
cp output/prototypes/cover-workbench/demo-assets/cover.png docs/assets/partnership-example.png
```

刷新界面截图：先按 [工作台说明](../output/prototypes/cover-workbench/README.md) 启动本地服务，再在仓库根目录执行：

```bash
python3 -m venv .venv-docs
.venv-docs/bin/python -m pip install playwright
.venv-docs/bin/python -m playwright install chromium
SCREENSHOT_URL=http://127.0.0.1:59054/ .venv-docs/bin/python scripts/capture_screenshots.py
```

已有 Google Chrome 时，可跳过浏览器下载，在截图命令前加 `SCREENSHOT_BROWSER_CHANNEL=chrome`，使用独立的临时浏览器配置，不连接日常浏览器会话。

截图使用新浏览器会话读取运行中的工作台，不替你上传素材、修改项目或导出图片。这是文档资产生成，不是完整功能验收。截图前确认当前页面是可公开的演示项目，避免展示本地路径或私人内容。

## 安装与打包检查

```bash
npx skills add eureka266/NoPic --list
python3 -m unittest discover -s tests -p 'test_skill_team_update.py'
python3 scripts/skill_team_update.py package
```

真实安装检查请在新建临时目录中执行，使用项目级范围，避免覆盖日常已安装的技能：

```bash
npx skills add eureka266/NoPic --skill blocksec-social-cover --agent codex --yes --copy
npx skills list --agent codex
```

候选 ZIP 应包含 `requirements.txt`、本文、README 图片和工作台的分发文件；不应包含用户收件原件、工作台 `workspace/`、本地虚拟环境或旧截图。运行环境、图像生成工具、字体和 Carrot 不随源码自动安装。

## 仍需处理

- **许可证**：尚未选定源码许可证，不显示 MIT 徽章。`skill-publisher` 脚本即使使用 `--dry-run`，也会在缺少 LICENSE 时自动写入 MIT；不要在当前源码直接运行这个默认动作。
- **字体分发**：既有完整样例附带 Arial 字体副本，其字体声明限制使用范围；公开再分发许可尚未核对。展示样例的授权不等于字体文件的分发授权，应核对许可或以有明确再分发许可的字体制作新的示例项目，原文件保留。
- **品牌适配**：底层仍保留既有品牌默认配置；预览的泛指文案不代表技能已完成任意品牌的首次配置流程。
- **效果图库**：首页仅展示通用占位版式与工作台截图。新增真实成品案例前先取得示例素材授权并完成实际出图，不用占位演示、参考海报或背景填充成品数量。

GitHub 发布与团队工作区上传是独立动作。本地候选 ZIP 不代表已安装或已同步到团队。
