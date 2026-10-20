# 发布维护

主仓库仅发布 NoPic 方法论和通用代码，组织资料独立维护。发布前检查当前受版本控制的文件，不因历史目录名或旧安装名保留组织默认项。

## 验证

- 安装 `requirements.txt` 到隔离环境，运行 `python -m unittest discover -s tests -v`；合成测试输入只用于工程验证。
- 用 skill-creator 的 `quick_validate.py` 校验根目录与 `skills/nopic-design-quality`。
- 运行 `scripts/check_methodology_boundary.py`，使用与打包器相同的规则检查生产素材、具体模板、组织manifest、隐藏凭据和运行状态。JSON协议与明确标注的行为评测输入单独管理。
- 检查 Markdown 相对引用、JSON与Python语法；按QC skill的eval说明验证行为，不以格式通过冒充审美验证。
- 验证工作台无组织包的空态、上传任务，以及加载外部组织包后的模板选择、预览与导出。
- `npx skills add SOURCE --list --full-depth` 应发现 `nopic` 和 `nopic-design-quality`。临时项目真实安装，不覆盖日常安装。
- 构建方法论ZIP，确认不包含组织资产、收件原件、本地环境或凭据；发布组织包则在独立仓库进行并核对文件哈希与权限。

## Git发布范围

提交与推送只覆盖用户要求的仓库和变更。没有合并授权时保留PR供审阅；不强制推送、不自动重写公开历史。素材迁出当前树不代表已有Git历史也被清除，历史整理属于需要单独评估的操作。
