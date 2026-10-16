# Codex 工作台协议

这份协议定义 `$blocksec-social-cover` 在 Codex 中的交互入口。它参考“会话负责意图与判断、侧边工作台负责可视化操作”的协作模式。工作台只处理本地文件和预览，不替代当前会话的事实判断、品牌选择或图像生成决策。

## 入口顺序

用户自然语言触发本 skill 后：

1. 解析当前请求的内容类型、交付模式和平台；不要求用户先学习命令。
2. 调用 `scripts/start_workbench.py`。脚本会复用同一工作区中已经运行的实例，否则启动 `output/prototypes/cover-workbench/server.py`，输出 `url`、`port` 和 `pid`。
3. 调用 Codex 的 `open_in_codex`，目标为脚本返回的 `url`，`placement` 使用 `right`。这是 Codex 桌面宿主提供的面板动作；技能不能自行模拟这个动作。
4. 打开面板后，在会话中用一句话说明已经打开工作台，并告诉用户可以拖入参考图、Logo、人物照片、截图或字体。不要重复要求用户在终端启动服务。

如果启动脚本失败，保留错误信息，给出可执行的本地启动命令并继续处理会话中已经提供的素材。如果 `open_in_codex` 不在当前工具列表，给出本地 URL，说明当前宿主无法自动打开侧边面板；不能把“URL 已返回”说成“侧边栏已打开”。

## 共享状态

工作台的运行状态位于：

- `output/prototypes/cover-workbench/workspace/workbench-state.json`：当前模式、底图、模板、文案、预览和上传索引。
- `output/prototypes/cover-workbench/workspace/inbox/`：用户上传的原文件，按香港日期、用途和内容哈希归档。
- `output/prototypes/cover-workbench/workspace/session-handoffs/latest.json`：最近一次会话任务的机器可读清单。
- `output/prototypes/cover-workbench/workspace/session-handoffs/latest.md`：最近一次会话任务的人类可读清单。

当用户说“我已经上传了”“按工作台里的图继续”“用刚才的参考图”等话时，先读 `workbench-state.json`；如果存在 `session-handoffs/latest.json`，再读它。以 `uploads[].relative_path` 读取实际文件，以 `uploads[].reference_only` 判断是否只能作为参考。读取不到状态时，回到当前会话中的附件和文字要求，不猜测工作台内容。

## 面板与会话的边界

工作台负责：

- 选择已有底图和模板；
- 更新标题、副标题和导出格式；
- 上传并归档素材；
- 生成静态预览和本地候选工程包；
- 保存背景生成或动效需求，但不伪装成已经生成。

当前会话负责：

- 判断用户意图和内容类型；
- 核对日期、人物、合作关系、产品和数据；
- 按 `assets/logos/index.json` 选择正式 Logo；
- 决定参考图哪些特征可借鉴；
- 用户明确要求新背景时调用原生 `image_gen`；
- 说明交付文件、限制和仍需用户确认的事实。

工作台不能直接向当前 Codex 会话注入一条新消息。它通过共享文件同步；如果用户在工作台点击“准备当前会话任务”，会更新 `latest.json` / `latest.md`，并复制一段可粘贴提示词。用户把提示词贴回当前对话后，继续读取上述清单。

## 关闭与复用

不要在每次自然语言修改时重启服务或重新打开面板。只要本地 URL 可用，就复用当前面板和工作区。只有端口失效、用户明确要求重置工作区，或工作台状态损坏时，才重新启动或请求用户处理。
