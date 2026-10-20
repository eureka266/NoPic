# 可编辑项目资产模型

成功交付保留 `project.json`、兼容 `content.json`、独立 `background/`、透明前景与原素材副本、`layout/`、`runtime/` 和输出文件。配置与模板快照用于重编译，不能把扁平PNG描述成可编辑分层项目。

生产模板、平台预设和素材由外部组织包提供。首次合成将所需模板与素材冻结进项目，保存运行脚本及所需平台预设；之后项目快照优先，组织包更新不改变旧项目。

`cover_project.py background`处理纯背景，`export`按项目或组织预设导出，`rebuild`重编译已有项目。跨画幅完整封面需要明确版式；不能只裁切整张成图。背景裁切必须有明确设置并保留原件。

未知模型、seed或生成参数保持未知。没有真实输出或执行器时，交付配置和缺口，不称为完成图片或视频。

通用协议定义：[项目manifest schema](../schemas/cover-project.schema.json) 与 [motion schema](../schemas/motion.schema.json)。它们描述文件接口，不包含组织模板或素材。
