# 领英 / X 内容类型与制作规则

先识别用户发布的内容，再决定画面形式与模板。此处是内容场景分类，不是新增的模板、独立渲染器或命令行参数。保留原六套静态模板，并新增极简双 Logo 合作模板，用户提供正式素材后可按下表制作。内容类型与 static / motion 呈现方式、发布平台分别选择；用户要求动图时在同一个 cover project 中启用动效。

## 内容分类与现有模板映射

| 内容类型 | agent 内部识别名 | 默认模板 | 可选形式 |
| --- | --- | --- | --- |
| Partnership / 合作公告 | `partnership` | `partnership-announcement-centered` | 沿用已有左对齐版；需要动效时 `/animate-cover` |
| Events / 活动 | `event` | 预告用 `article-cover-landscape` | 回顾用 `seminar-summary-portrait`；嘉宾金句用 `speaker-quote-portrait`；横版人物观点用 `opinion-card-landscape` |
| Security Roundup / 安全周报与阶段汇总 | `security-roundup` | `article-cover-landscape` | 精选要点用 `seminar-summary-portrait`；按栏目要求保留“周报 / 双周 / 月报”等周期 |
| Incident Analysis / 安全事件分析 | `incident-analysis` | `article-cover-landscape` | 原始图表 / 截图作可选主视觉；较短已确认结论可用概要形式 |
| Product Updates / 产品发布与功能更新 | `product-update` | `article-cover-landscape` | 真实 UI 主视觉；官网/落地页/邮件产品动画路由 `/product-motion` |
| Research & Insights / 研究与行业观点 | `research-insight` | `article-cover-landscape` | 署名观点用 `opinion-card-landscape`；活动中的嘉宾观点归入活动 |

上述内部识别名不是静图脚本支持的新 `layout`。制作配置使用已有 `layout` / `template_id`，不要将 `security-roundup` 或 `event` 当成渲染器参数。

每次为新项目选择视觉方案时，按内容类型读取 [共享参考库索引](../assets/reference-library/index.json)。默认采用已有模板；用户指定参考方案时，优先使用对应 `ready` 记录及其已验证的配置。`draft` 和 `reviewed-spec` 只用于参考或共建，不能宣称是可直接渲染的正式模板。一次性参考图不自动入库；用户希望供他人复用时，进入 [参考图共建流程](reference-analysis.md)。

## 每类内容的重点

### Partnership

用户要白底浅网格、边角柔光、仅两家公司 Logo 和 × 的极简样式时，读取 [极简双 Logo Partnership](partnership-minimal.md)，使用 `partnership-minimal` + `partnership-soft-grid` / light；不添加标题，不沿用第三方参考的公司 Logo。有文案的默认合作模板仍为 `partnership-centered`。

画面先传达“谁与谁合作”，再传达已确认的合作内容。使用双方正式 Logo、合作标题和必要说明；原文明确是宣布合作、联合活动或其他关系时按原文表达，不将所有双方信息自动升级为战略合作、客户案例或背书。新建默认居中版，已有项目保留原版。

需要动效时复用已确认母版、文案与配色，在同一项目接入实际运动源并选择现有配方。单蓝、单橙、蓝橙、黑白灰均可；不因动图换风格或新增合作事实。

### 活动

先识别活动阶段：

- **活动预告 / 参会 / 演讲信息**：横版封面，重点是主题、活动名、明确日期与时区，以及用户确认的角色。提供了主办 / 赞助 / 嘉宾身份才呈现，不由 Logo 猜测身份。
- **活动回顾**：概要模板，使用 1–4 条已确认的要点；材料更多时筛选有明确来源的精简要点，必要时拆图，不强塞进一张。
- **嘉宾金句**：人物与原句是主体；准确保留姓名、职位、机构和引语。取得允许使用的人物素材，依原生编辑能力抠图。

日期和时区优先采用活动明确标注的值；需要计算“今天 / 明天”或默认时间时使用香港时间。

### 安全周报与阶段汇总

画面需要栏目标题、明确日期范围、已确认摘要；作为正文链接的推广封面可以只保留一条摘要，不要求将整篇报告塞入图中。精选事件概要复用现有概要模板。标题与周期沿用用户输入；不能把双周报告改称周报，或把周报改成月报。

数值、损失金额、项目数量、事件清单和结论都必须来自本次已确认稿件 / 证据。不能从日期范围估算事件数，也不从版式参考中抄用数字。没有数据时先完成标题与背景，不补造统计。安全周报目前是内容到现有模板的映射，不具备自动采集事件、自动算总损失、绘制统计看板或专用时间线的实现。

### 安全事件分析

只聚焦本次已确认的单个事件 / 漏洞：事件名、结论、研究标题及可用截图 / 图表。没有确认的攻击原因、责任归属、受影响项目或损失金额不能成为大字标题；引用报告时保留“估计”“疑似”等限定。截图按比例放入，复杂报告的内容分析不属于仅制作配图的自动授权。

### 产品发布与功能更新

画面围绕产品 / 功能名称和一个核心已确认价值。真实 UI 截图保留原生颜色、标签和状态，不凭传播目标画一个不存在的按钮、告警或性能结果。

领英 / X 的静态产品公告使用本包封面。需要产品动画时先识别投放位置；官网、落地页和邮件可用 Carrot，社交视频不因“产品”两个字就自动进入 Carrot 的范围。

### 研究与行业观点

文章推广使用标题、精简摘要和可选原始主视觉。署名观点用真实人物与已确认引语；活动嘉宾观点沿活动流程处理。用户要求润色或提炼时才改写，不把改写文案当作未经确认的原句署名。

## 普通用户的流程

1. 接收内容用途、已有文案 / 稿件、发布场景和素材；根据内容自动判断类型与阶段，无需用户挑选模板 ID 或制作模式。
2. 读取对应模板和本次项目，复用正式 Logo、字体与固定底图，准确合成文字与素材。
3. 检查文案完整、日期与数字准确、Logo / 人物保真、对齐和可读性，交付成品 PNG 与可复用项目；需要动画时再按对应动效流程执行。
4. 接受中文修改意见，只改变指定文案、素材、背景或排版参数，保留原始素材与共享模板。

人物抠图、背景生成、模板参数、动效提示词与执行引擎属于内部制作能力。只提炼提示词属于用户明确请求的进阶分析 / 技能维护，不作为普通用户示例或出图前必选项。

## 分类依据

2026-10-14（香港日期）整理。参考用户明确提出的 Partnership、活动与安全周报，以及可公开读取的 BlockSec 官方社交内容和文章。以下样本用于识别内容场景，不代表完整账号盘点，也不作为新配图文案、合作名单或数据来源；帖子与发布频率会变化，具体稿件以本次用户材料为准。

- Partnership 官方帖样本：<https://www.linkedin.com/posts/blocksec_introducing-blocksec-partnership-program-activity-7223594755379273728-FfoA>
- 活动官方帖样本：<https://www.linkedin.com/posts/blocksec_join-blocksecs-ceo-andy-at-telegram-space-activity-7120383241289502720-2pld>
- Weekly Security Roundup 官方帖样本：<https://www.linkedin.com/posts/blocksec_weeklysecurityroundup-smartcontractsecurity-activity-7091988749514244096-POEO>
- 双周安全汇总官方 X 帖样本：<https://x.com/BlockSecTeam/status/1962813451064066226>
- 产品功能更新官方帖样本：<https://www.linkedin.com/posts/blocksec_phalconcompliance-compliance-activity-7358356752165425152-08yO>
- 事件分析与研究官方文章样本：<https://blocksec.com/blog/breaking-down-the-common-attack-patterns-of-honey-pot-scams>

六类是本包为制作而整理的分类；官方样本没有专用模板、栏目固定频率或自动数据功能的含义。
