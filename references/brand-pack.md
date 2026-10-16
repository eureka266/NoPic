# NoPic 品牌素材包

品牌素材包是独立于 skill 源码的可移植 ZIP。它用于把公司正式 Logo、已确认的无字底图、参考图、字体和示例项目一次交给使用 skill 的同事。品牌包可以放在私有 GitHub Release、公司云盘或直接附在 Codex 对话中；不要把内部资产写进公共 skill 仓库。

## 同事的最短用法

把 `NoPic-<brand>-<version>.zip` 附在 Codex 当前对话中，然后说：

```text
使用 $blocksec-social-cover，安装我附上的 NoPic 品牌素材包并打开工作台。
```

skill 会把包安装到当前项目的 `.nopic/brand-packs/<id>/<version>/`，并写入 `.nopic/active-brand-pack.json`。之后直接说“使用当前品牌包制作一张 LinkedIn 封面”即可。用户无需指定 skill 的安装路径；当前项目由 Codex 工作区自动确定。

## 包目录

```text
blocksec-brand-pack/
├── manifest.json
├── logos/
├── backgrounds/
├── references/
├── fonts/
└── examples/
```

`logos/` 只能放可作为正式图层的 Logo；`backgrounds/` 只能放可直接使用的无字底图；`references/` 用于借鉴结构和视觉方向，不能自动作为发布素材；`fonts/` 需要附带授权或使用说明；`examples/` 只用于展示经过确认的版式。

最小 manifest：

```json
{
  "schema_version": 1,
  "id": "blocksec",
  "version": "2026.10.16",
  "display_name": "BlockSec Brand Pack",
  "defaults": {
    "logo": "blocksec-white",
    "partner_logo": null,
    "background": "partnership-soft-grid-light"
  },
  "logos": [
    {
      "id": "blocksec-white",
      "display_name": "BlockSec white lockup",
      "file": "logos/blocksec-white.svg",
      "render_file": "logos/blocksec-white.png",
      "reference_only": false,
      "usable_as_standalone_logo": true
    }
  ],
  "backgrounds": [
    {
      "id": "partnership-soft-grid-light",
      "display_name": "Partnership soft grid",
      "file": "backgrounds/partnership-soft-grid-light.png",
      "reference_only": false,
      "usable_as_background": true
    }
  ],
  "references": [],
  "fonts": [],
  "examples": []
}
```

## 维护者打包

先复制 [manifest 模板](../assets/brand-pack-template/manifest.json)，把文件放入对应目录并登记每个 `id`，再执行：

```bash
python3 scripts/create_brand_pack.py /path/to/blocksec-brand-pack-source /path/to/NoPic-BlockSec-brand-pack-2026-10.zip
```

脚本只把 manifest 声明的文件和可选 `README.md` 放进 ZIP，不会把 `workspace/`、缓存、虚拟环境或未登记的内部文件带进去。安装和校验使用：

```bash
python3 scripts/install_brand_pack.py /path/to/NoPic-BlockSec-brand-pack-2026-10.zip
```

安装成功后，工作台启动器会自动发现 `.nopic/active-brand-pack.json`，启动服务时传入品牌包；工作台会动态显示包里的底图和默认 Logo，并在渲染时使用对应文件。

## 素材规则

- 原始包保留版本号，不覆盖同一品牌包版本。
- 正式 Logo 要登记实际颜色、适用背景和是否可独立使用。
- 参考图必须标记 `reference_only: true`。
- 底图必须去除文字、Logo 和不属于底图的发布信息。
- 不把用户上传的 `workspace/` 或一次性项目输出混入品牌包。
