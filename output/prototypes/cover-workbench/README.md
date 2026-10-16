# 有图 NoPic 内容工作台：侧面板交互原型

此目录是本地交互原型，调用仓库中的静态合成脚本。日常使用技能不需要先启动它。

## 打开

启动后打开 <http://127.0.0.1:59054/>；在 Codex 内置浏览器中可放入右侧面板。这里只提供本机服务，没有公开在线演示站点。

先下载仓库，然后启动（已下载可跳过前两行）：

```sh
git clone https://github.com/eureka266/NoPic.git
cd NoPic/output/prototypes/cover-workbench
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python server.py 59054
```

`preview.html` 是包含图片、样式和脚本的单文件外观预览，可直接打开；真实上传、静态合成、保存、导出和会话任务桥接需要上述本地服务。通过 skill 自然语言调用时，Codex 会尝试自动启动服务并在右侧面板打开 `http://127.0.0.1:59054/`。`index.html`、`style.css`、`app.js` 是可继续修改的源文件。

界面使用“本公司 / 本品牌 / 合作方”等通用说明。配图中的 `YOUR BRAND` 和“合作方”均为文字占位，正式使用时需替换为双方授权的 Logo，不代表真实合作关系。原始品牌素材在素材库中保留。

修改源文件后执行 `.venv/bin/python build_preview.py`，同步更新单文件预览与内嵌演示素材。构建复用已有底图，只合成双方文字占位，不生成背景。`workspace/` 中的上传、运行历史与本地虚拟环境不纳入 Git。

## 开源参考核对

| 项目 | 许可与已核对能力 | 本项目的使用判断 |
| --- | --- | --- |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | Apache-2.0；本地 CLI、Studio 浏览器编辑与预览、播放器；Studio 依赖多个内部包、代码编辑器和面板系统 | 最接近期望的宿主体验。借鉴本地服务、共享工程和预览更新；直接迁入整套视频编辑器会扩大当前范围 |
| [miniPaint](https://github.com/viliusle/miniPaint) | MIT；上传、拖放、图层、图片格式导出；官方有 iframe 嵌入示例 | 可以参考素材导入与导出；大量画笔、滤镜和照片处理工具超出当前流程，本地项目归档仍需额外集成 |
| [Fabric.js](https://github.com/fabricjs/fabric.js) | MIT；文字编辑、对象变换、分组、序列化 | 是未来拖动和缩放控件的候选底层库，本身不是开箱即用的操作页面 |

判断依据是官方文档、许可与包依赖核查，没有构建或完整实测这些开源项目。本原型没有复制它们的代码，也没有添加这些运行依赖。

核对入口：

- [HyperFrames Studio 依赖](https://github.com/heygen-com/hyperframes/blob/main/packages/studio/package.json)
- [HyperFrames Studio Server 依赖](https://github.com/heygen-com/hyperframes/blob/main/packages/studio-server/package.json)
- [miniPaint 官方说明与嵌入方法](https://github.com/viliusle/miniPaint/blob/master/README.md)
- [Fabric.js 能力](https://www.fabricjs.com/)

## 可以实际操作

- 三个流程入口与窄侧面板响应布局；已经检查 560px 宽度。
- 已有的三张浅色底图切换；所有底图来自项目原素材，没有程序新绘制背景。
- 两套合作模板：极简双 Logo、居中标题；中文文案可更新。
- PNG / WebP 真实静态导出，预览使用现有 `render_cover.py` / `cover_project.py` 的成图。
- 按品牌、总体参考、底图参考、可用底图、既有静图和其他素材分类上传，保留原名和字节；同名不同内容通过哈希子目录分开存放。
- `workspace/` 下保存原件、索引、可编辑项目、版本和导出结果。
- 定稿生成本地候选 ZIP 和文件清单；可选择仅保留本地，当前版本记录不再提醒。
- 查看实际工作路径与可选知识库目录。
- “准备当前会话任务”会生成 `workspace/session-handoffs/latest.json` 与 `latest.md`，供当前 Codex 会话读取。

## 明确尚未接入

- 自动向当前 Codex 会话注入消息、原生 image_gen、人物抠图、自动 hook 安装、Git 提交或推送。工作台已支持文件桥接：点击“准备当前会话任务”会在 `workspace/session-handoffs/` 生成 JSON / Markdown 清单并复制可粘贴提示词。
- 任意素材替换到模板槽位；当前品牌槽位固定使用本品牌与合作方的文字占位。
- 自由拖动、缩放、撤销、多项目切换、工作路径选择与完整多平台版式。
- 动画制作与编码。动效入口显示缺少独立纹理层，只可将需求保存至 `workspace/requests/`，不会假装已生成视频。
- 知识库素材检索：当前只检测预设的本公司知识库素材目录是否存在，不遍历或写入该仓库。示例路径需按本公司实际配置调整。

## 保存边界

本地服务只监听 127.0.0.1，限制同源 JSON 写入和工作路径内文件读取；单文件最大 20 MB。原型运行时只导出指定文件和当前项目，不将用户主目录公开为静态目录。上传只负责归档；参考素材不会自动成为发布素材或共享品牌库条目。

`verification.json` 记录隔离临时工作区的实际验证结果，未将验证上传混入演示工作区。原型没有自动安装 hook；页面的定稿交互仅演示未来 hook 所提醒的可选入库流程。
