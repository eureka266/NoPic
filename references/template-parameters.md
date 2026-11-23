# 具名模板与项目覆盖

新项目从外部组织包 `catalogs.templates` 选择模板；已有项目优先读取 `content.json.template`。模板的版本、画幅、图层ID、类型、内容字段和几何参数需要明确，未知布局不自动落到内置模板。

每次成功保存完整模板快照与 `layer_overrides`。`--layer LAYER.PROPERTY=VALUE`修改项目中指定图层的允许属性；`--reset-layer LAYER`只恢复该图层。普通换文案或素材保留覆盖，不改组织共享模板。

校验画幅、坐标、边界、字号范围与未知图层；失败时保留上次成功输出。概要分段应使用稳定section_id，删除和重排不能把旧覆盖转移到新段落。

模板图层ID使用角色名称，例如brand-logo、partner-logo、main-title，不把公司名写进方法论代码。历史项目按其实际asset_field识别品牌层，不要求通过公司名迁移。
