# 团队更新提醒、工作区分享与使用建议

本规则用于维护 skill 后询问是否将更新上传到 Blocksec 团队工作区。它不把普通配图输出当作 skill 更新，不自动上传、发布或修改共享权限。

面向普通同事的参考提交、审核、贡献状态与复用步骤见 [用户共建指南](contributors-guide.md)。

## 本地 Codex hook

源码工作区已配置 `.codex/hooks.json`，使用 Python 3 执行 `scripts/skill_team_update.py hook`：

1. `UserPromptSubmit` 记录本轮开始时的 skill 文件摘要。
2. `Stop` 比较说明、脚本、模板、参考库、共享素材和测试文件。
3. 只有源码内容变化时才生成本地候选 ZIP 和文件清单，再要求 agent 完成适用校验并询问：
   > 是否将此次维护更新上传到 Blocksec 团队空间？
4. 普通图片 / 视频项目、用户收件素材、临时状态与导出目录不参与维护检测。同一轮不重复提醒，Stop 延续也不会再次触发。
5. hook 输出是提醒，不是人类授权；不能把它自动创建的延续消息视为允许上传。已有明确的目标工作区发布授权时沿用授权，不重复询问。

项目配置内的脚本命令使用当前工作区的绝对路径。换电脑或移动源码后要改成实际脚本位置，不能直接复用别人的主目录。它不是通过 skill ZIP 自动安装的全局 hook。

Codex 需要对项目配置层和具体 hook 完成信任检查；未信任或管理员禁用时不会执行。CLI 可通过 `/hooks` 检查、审阅和信任；不通过脚本写入信任记录或绕过 review。配置存在、单元测试通过，不代表当前会话已加载 hook 或实际运行获准。

## 没有本地 Stop hook 的环境

云端 Work 不使用本包的本地 command hook。只有当前 skill 源码发生维护变化时，agent 在任务结束前按相同流程准备更新包、列出改动并询问是否更新工作区。一次性图片制作不提问。

如果当前执行环境不能运行打包脚本或访问完整源码，先交付实际改动和可移交文件，说明更新包尚未生成；不假称能自动上传。不把保存项目、共享对话或上传素材等同于发布工作区 skill。

## 生成可审阅更新包

从源码根目录运行：

```bash
python3 scripts/skill_team_update.py package
```

脚本实际生成 `exports/team-updates/<source-revision>/blocksec-social-cover.zip` 和 `manifest.json`。ZIP 包含顶层 `blocksec-social-cover/` 技能目录，保留技术标识。清单记录文件哈希、ZIP 大小和外部依赖。包含技能说明、运行依赖清单、脚本、资产、参考、测试、文档插图、收件使用说明，以及预览工作台的显式分发文件；不包含收件原件、普通输出项目、工作台 workspace、虚拟环境、凭证或本地 hook 状态。

这是候选源码包，仍需验证目标工作区的运行环境、字体、image_gen、Python 依赖、真实素材路径以及外部 Carrot / HyperFrames。工作区分享不会自动安装本地软件、复制用户知识库或赋予源系统权限。Carrot 依然是独立外部技能，不能把索引说成已完整打包。

用户明确允许发布后，确认真实工作区、目标 skill、创建还是更新现有版本、可用发布权限及实际上传入口。只用当前环境提供的真实工具 / UI 完成发布；没有入口时交付 ZIP 与当前平台操作指引。只有拿到成功结果才报告已更新。

## 多人维护的建议

ChatGPT 工作区 skill 的共享、生命周期控制，与本地源码、插件和连接器权限是独立的边界。Enterprise 账号不自动意味着工作区管理员或 skill 发布权限；以实际设置为准。

当前核对的官方资料未明确保证多人同时编辑同一个已发布 skill 的全部源码。采用可验证的团队流程：同事用 `/analyze-reference` 提交候选 → 在团队源码中审阅合并 → 维护者验证 → 确认更新工作区版本 → 同事使用发布版本。团队可以指定主维护者与备份发布者；角色是否可配置以当前工作区 UI 为准，不宣称已经存在某种协作者角色。

维护本包时优先使用可访问源码和素材的本地 Codex 或 Work。只做日常品牌配图、提供文案和参考、查看成品的同事可以优先使用 ChatGPT Work；当前版本依赖本地脚本、正式素材、字体和动画工具，因此团队 Work 版本仍需做首次实际出图验证。

## 官方来源与核对边界

2026-10-14（香港日期）核对；具体权限、客户端与工作区功能会变化：

- [Hooks](https://learn.chatgpt.com/docs/hooks)：本地配置、Stop 输入 / 输出、信任要求，以及云端编排对本地 command hook 的限制。
- [Skill controls](https://learn.chatgpt.com/docs/enterprise/skills)：工作区 skill、本地文件技能与插件的独立分发和管理边界。
- [Roles and workspace permissions](https://learn.chatgpt.com/docs/enterprise/roles-and-workspace-permissions)：账号访问、角色、运行时和连接器权限的边界。
- [Get started with ChatGPT Work](https://learn.chatgpt.com/docs/get-started-with-work)：Work 的文件任务与本地 / 云端执行选择。

这些官方说明不等于本包在 Blocksec 工作区已经安装、发布、获授权或完成端到端测试。
