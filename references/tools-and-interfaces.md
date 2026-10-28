# 工具、依赖与制作接口

通用脚本和scene方法保持不变。先按[平台能力契约](platform-contract.md)核对执行入口：下文doc-intake、host-unit、computer、SessionFile/stage_files是Hana实现，不是DSH/Codex默认工具。其他平台使用对应适配，缺能力只暂停依赖步骤。

## 路径与权限

本文 `$SKILL_DIR` 为当前安装包目录，`$WORK` 为任务工作目录，`$NODE_PROJECT` 为用户环境中明确已有pptxgenjs的Node项目。使用绝对路径调用随包脚本；shell工作目录用工具的workdir设置，不在命令前拼接cd。不把生成物写入安装包。

本技能不自动下载、安装、付费或上传。缺依赖时说明受影响环节；另有授权后下载/安装仍走Hana downloader。科研、个人和参考中的未发表内容只走获授权本地/隐私通道，禁止贡献模型和未经允许的云OCR。

## 1．读取参考与成品

优先复用已生成且仍适用的提取、原像和审阅记录。读取Office/PDF先加载office-documents、doc-intake并遵守其参数规则。

已核工具发现：`tool_search`查`doc_intake`，当前正式调用为：

```json
{"server":"doc-intake","tool":"doc_intake","arguments":{"source":["/absolute/reference.pptx"],"backend":"local"}}
```

敏感资料或明确要求本地时固定local；不要因失败自行切云。后端超时后先查已有产物与警告，再针对性重试。文字提取的公式可能乱码，没有独立图片不等于页面没图，继续看原像。

office-documents的本地读取接口：

```bash
python3 "$OFFICE_SKILL_DIR/scripts/read_document.py" "$INPUT" --format json --max-chars 12000
```

通过正式技能入口发现`OFFICE_SKILL_DIR`，不猜缓存位置。`office_read-document`当前不支持PPTX，不能替代其读取。

补充对象/几何清点，随包工具不改源文件：

```bash
python3 "$SKILL_DIR/scripts/inspect_deck.py" "$REFERENCE_PPTX" --pages 1-3 --out "$WORK/reference-inspection"
python3 "$SKILL_DIR/scripts/inspect_deck.py" "$REFERENCE_PDF" --pages 7,11,17-18,21 --preview --out "$WORK/reference-inspection"
```

实际页码按本次参考选择。PPTX分支只用标准库；PDF需pdfplumber，本地预览用它的PDFium。若缺包，继续对象/文字工作，不安装依赖。PDF原像保存为真彩色，统计色板所做的量化不可写回预览图。

`inspection.json`包括页序、对象名称/类型/组关系/坐标、样式声明、资源关系、备注。它不完整解析主题继承；旋转/翻转边界标记不确定；不是Office渲染器。

## 2．字体与环境

```bash
python3 "$SKILL_DIR/scripts/preflight.py" --node-project "$NODE_PROJECT"
python3 "$SKILL_DIR/scripts/check_fonts.py" --families "Microsoft YaHei" "Times New Roman" "Cambria Math" --out "$WORK/fonts.json"
```

preflight无安装和文件写入；返回标准库PPTX检查能力、可选PDF依赖、Node及明确Node项目的pptxgenjs解析结果。字体探针仅适用于macOS，登记不等于实际Office字重/显示。

历史成功生成后端为PptxGenJS 4.0.1。随包生成器通过当前workdir的`package.json`定位依赖，所以运行时必须明确设置workdir=`$NODE_PROJECT`。技能目录中没有隐含node_modules，不把某个旧科研项目的依赖路径写死为默认。

## 3．制作端：接续现有源，或用低层scene组件

有已确认的完整稿与构建源时，沿它做增量修改并保留几何、数据与关系。检查实际命令行入口，旧名字可能已改为局部修订。按当前任务参数定位，不原样复制含研究正文/私人路径/固定页数的脚本。

随包 `build_deck.mjs`、`apply_ooxml_styles.py`、`inspect_deck.py`、`check_fonts.py` 原样复用已形成的通用包。它们是低层工具，不会替Agent选择主图、生成完整机制或自动套原参考模板。

没有项目生成器时，在工作区编写本次scene和构建源。`assets/scene-contract.json`演示字段，不是推荐版式或测试任务；不得直接把它的示意页交成科研汇报。参考shell、字体、图层、连线及图文比例应按实际拆解写进任务源。既有参考shell比低层生成器的简化公共顶边/页脚优先；若后端固定shell与其冲突，在任务构建副本中参数化该shell，保留原后端，不借此另换视觉路线。

### 最小接口

```bash
# 以下命令会生成新PPT，仅在当前任务已授权制作时执行。
# exec_command.workdir = NODE_PROJECT
node "$SKILL_DIR/scripts/build_deck.mjs" "$WORK/scene.json" "$WORK/build/base.pptx" "$WORK/fonts.json"
python3 "$SKILL_DIR/scripts/apply_ooxml_styles.py" "$WORK/build/base.pptx" "$WORK/scene.json" "$WORK/build/styled.pptx"
python3 "$SKILL_DIR/scripts/inspect_deck.py" "$WORK/build/styled.pptx" --requirements "$WORK/build/base.pptx.requirements.json" --out "$WORK/audit/objects"
```

生成器写`output.pptx.requirements.json`。style脚本显式写原生渐变/预设调整到新文件；不自动栅格化文字。脚本只拒绝同一路径输入输出，不替代项目版本管理，执行前检查输出不存在。

### scene字段

- 顶层：`title,width,height,theme,slides`。坐标英寸，字号pt，色值为无#的六位hex。
- theme：`headingFont,bodyFont,latinFont,mathFont,background,ink,accent,secondary,surface,muted,fontVerificationRequired`。
- slide：`title,titleRuns?,titleWidth?,source,notes,pageNumber?,objects,relations?`。
- 每对象必须有稳定、页内唯一`name`，另有`type,x,y,w,h`。不要用同名对象掩盖替换失败。
- `text`：`text`或`runs`、`fontSize,fontFace,color,bold,align,valign,margin`。run支持`text,fontFace,fontRole,color/colorRole,bold,italic,fontSize,subscript,superscript`。mathFont仍须单独核验，后端字体门禁只覆盖heading/body/latin。
- `node`：Office预设`shape`、`fill,stroke,lineWidth,gradient,shadow,adjustments,rotate,flipH,flipV`。
- `custom`：`points`为PptxGenJS的custGeom点列。点类型及坐标按所装版本API核对；历史曲线用单段三次贝塞尔与标准三角箭头尖，不承诺自动SVG转换。
- `arrow`：独立直线/箭头，支持有符号w/h和虚线。它不是附着节点的连接器。
- `image`：本地`path,sourceSize:[pixelWidth,pixelHeight],role`；默认等比contain。显式stretch会变形，科研图通常不用。wholeSlide/page_title/body_text图片被拒绝。
- `table`：`rows,colW,rowH,fontSize`；`chart`：`chartType,data,chartOptions,colors`，仅bar/line/pie/scatter。优先保留已有原生图表与工作簿，不无故重建。
- relations：`name,kind,from,to,label?,direction?`；kind有progression/support/decomposition/aggregation/training/inference。仅简单直线、汇线和分叉布局，复杂弯曲/宽/循环/展开线需显式设计，不能声称该字段自动复现全部箭头。

外绘源与原生标签的对应、坐标缩放及语法边界见[机制与图证规则](figures-and-evidence.md)。文字公式可以编辑文字，不等于原生OMML公式；要求后者时另核真实能力并实际编辑验证。

### 无字底层与原生标签的实际接入

设计阶段同时维护完整SVG源、只含图形的SVG和标签清单；用同一viewBox和上述变换把每条标签写成scene的`text/runs`对象，名称例如`figureA_label_01`。这一步由本次构建源显式生成，不假定随包有任意SVG解析器。

任务允许无字图片底层时，把无字SVG内联进独立HTML，CSS用`@page { size: 1600px 900px; margin: 0 }`并将html/body/SVG画布设为同样尺寸（宽高按源viewBox比例改）。用下述HTML→PDF正式工具导出，再用`inspect_deck.py graphics.pdf --pages 1 --preview --out ...`取得其报告中`reference_render`指向的PNG；这是图形底层栅格化，不是最终PPTX渲染。PNG以本地`image`对象等比放置，标签按相同变换覆盖，回读检查文字确实原生且无重影。科研实测图片不经过文字层伪重建。

若图形本身也要求原生可改，在本次scene/构建源里显式迁移受支持的node/arrow/custom图元；复杂SVG或图形语义未核时列出缺口。该情况下不得以无字PNG代替原生图形要求。

## 4．预览和真实Office渲染

同源设计预览可由本次构建源导出HTML/SVG。已核工具：

```json
{"server":"host-unit","tool":"office_html-to-pdf","arguments":{"htmlPath":"/absolute/design-preview.html","filename":"同源设计预览_非Office渲染.pdf","preferCSSPageSize":true,"printBackground":true}}
```

HTML需明确`@page`尺寸与分页，使用本地/内联已授权资源。工具只接收html或htmlPath其一，文件写入拒绝默认覆盖；返回SessionFile按正式身份交付。它打印设计HTML，不读取最终PPTX，不代表Office渲染。封装时核对了正式schema，本包不另捆浏览器或截图引擎。

封面/目录需按[独立页面职责](cover-and-navigation.md)编排。现有低层后端默认公共shell不能直接作为参考封面，不提供自动封面/目录映射算法；在本次项目源中显式组织并验证。

真实PPTX渲染按当前已授权Office/WPS/Keynote或专业转换工具执行，记录实际引擎及是否发生降级。`office-toolkit`的`office_render_preview`当前只收DOCX，不能当PPT渲染器。

GUI操作使用computer正式start/list_apps/状态与操作流程；不使用AppleScript、open -a或脚本绕过审批。能读界面、点击回执与目标真正改变分别核验。用户取消测试即停止该测试及相关GUI排障。

## 5．交付与受控资料

`stage_files`交付完整PPTX和必要源/预览，优先SessionFile ID；需要shell路径时先materialize，不猜缓存。受限资料/Obsidian读取使用当下获授权入口；库内原文或附件向制作目录导出需遵守库规则，不因可读就默认复制。

随包工具不调用外网。平台App、工具名称和能力可能变化；遇到缺失重新发现接口，报告差异，不能默默改用未授权服务。
