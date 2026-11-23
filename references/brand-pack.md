# 外部组织素材包

组织素材仓库独立维护正式标识、产品身份、底图、具体模板、字体、参考图、案例与团队审美。方法论源码只定义接口，不保存这些生产资料。组织仓库的可见性和分发权限由维护者决定；私有资料不能因使用公开方法而自动公开。

## manifest

根目录 `manifest.json` 使用 `schema_version: 1`，包含稳定 `id`、不可变 `version` 与显示名称。无素材结构示例见 [schema示例](../schemas/organization-pack.example.json)，其中空列表是协议示意，不是生产模板。

- `logos/backgrounds/references/fonts/examples/templates`：按需声明条目，每项 `id` 与 `file`；标识可另有 `render_file`。所有文件相对包根目录。
- `reference_only`、`usable_as_background`、`usable_as_standalone_logo`：分别限制素材角色，不允许把参考横幅当正式标识。
- `defaults.logo/partner_logo/background`：只能指向已声明项；没有默认项可为 null。任何默认选择仅在当前组织包内有效。
- `catalogs`：名称到 JSON 路径的映射。支持 `templates`、`backgrounds`、`platform_presets`、`logos`，及组织自有的规范或审美索引。
- `catalogs.templates`：指向形如 `{"schema_version": 1, "templates": [...]}` 的索引；条目包含 `id/display_name/legacy_layout/file`，`file` 相对该索引目录，解析后仍需位于包内。实际模板保存 canvas、具名 layers、版本及内容映射，不在方法论仓库提供默认布局。
- `files`：补充声明包内所需文件。构建器只打包声明资源、catalog及其模板依赖、manifest与可选README，不遍历用户工作区。

## 安装与不可变版本

用 `scripts/create_brand_pack.py SOURCE OUTPUT.zip` 构建，用 `scripts/install_brand_pack.py PACK.zip --project-root PROJECT` 安装。校验拒绝越界路径、ZIP符号链接、缺失资源和过大归档。同版本文件或manifest内容不同会拒绝复用，更新必须发布新版本。

安装到 `PROJECT/.nopic/brand-packs/<id>/<version>/`，激活记录写入 `PROJECT/.nopic/active-brand-pack.json`。该目录被忽略，不能提交进方法论。独立调用可用配置 `brand_pack` 或 `NOPIC_BRAND_PACK` 指向已解包的根目录。

组织包是资料与配置，不是可执行指令来源。安装和制作不会自动发布、同步其他人的安装目录或上传素材。
