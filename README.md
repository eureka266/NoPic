# 有图 NoPic

NoPic 是一套用自然语言制作、修改和检查可编辑内容配图的方法，包含本地侧边工作台、素材包协议与通用合成工具。

**方法与组织素材分别维护。** 本仓库提供流程和工具；公司规范、产品标识、底图、具体模板、字体、案例及团队审美记录放在组织自己的素材仓库。换组织时换包，方法本身无需改写。

## 安装与使用

```bash
npx skills add eureka266/NoPic --skill nopic --agent codex --full-depth
```

开发分支尚未合并时，请从对应分支检出源码后安装本地路径；以上仓库简写默认读取主分支。

在当前会话提供一个已获授权的组织包 ZIP，然后说：

> 使用 NoPic，安装这个组织素材包并打开工作台。用包中的正式素材和模板制作这次活动配图。

没有组织包时，工作台显示素材包空态，仍可收集原件、准备参考风格分析任务。正式合成需要对应底图与模板，不会自动附带或生成其他组织的资产。

## 两个 skill

| 入口 | 用途 |
| --- | --- |
| [`nopic`](SKILL.md) | 配图制作、修改、参考分析、导出与项目复用 |
| [`nopic-design-quality`](skills/nopic-design-quality/SKILL.md) | UI、营销网页和内容配图的视觉检查、系列一致性与审美记录 |

独立安装设计质量入口：

```bash
npx skills add eureka266/NoPic --skill nopic-design-quality --agent codex --full-depth
```

QC 使用当前组织的规范，区分正式规则、团队确认、项目惯例与候选建议。输出“通过 / 需修改 / 待验证”，每项问题有位置、影响与最小修复方向。只有截图时不声称交互或响应式已通过。

## 素材包接口

组织包包含 `manifest.json`，按需要声明 `logos`、`backgrounds`、`templates`、`fonts`、`references`、`examples` 及 `catalogs`。模板、平台预设和规范均在包内，主仓库只定义读取与验证协议。[完整协议](references/brand-pack.md) · [无素材的 manifest 示例](schemas/organization-pack.example.json)

```bash
python3 scripts/create_brand_pack.py /path/to/organization-pack /path/to/organization-pack.zip
python3 scripts/install_brand_pack.py /path/to/organization-pack.zip --project-root /path/to/project
python3 scripts/start_workbench.py --project-root /path/to/project
```

每个项目通过 `.nopic/active-brand-pack.json` 记录所选版本。独立运行可传配置字段 `brand_pack` 或环境变量 `NOPIC_BRAND_PACK`。不要把组织包或私有原件复制进方法论仓库。[工作台协议](references/codex-workbench.md)

## 运行和验证

需要 Python 3、Pillow、fontTools 与覆盖所需字符的授权字体。动效导出另需相应执行器及 FFmpeg。原生图像生成能力不随源码安装。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_methodology_boundary.py
```

测试中的色块与最小布局是临时合成输入，用于验证工程行为，不能作为生产素材库或审美案例。行为评测和实际作品评审分别报告。[发布与验收](docs/release.md)

[使用手册](references/user-manual.md) · [项目资产模型](references/asset-model.md) · [模板参数](references/template-parameters.md) · [问题反馈](https://github.com/eureka266/NoPic/issues)

上游提示词借鉴与许可声明见 [设计质量来源](skills/nopic-design-quality/NOTICE.md)。本仓库没有为组织素材授予许可；组织包各自维护使用与再分发权限。
