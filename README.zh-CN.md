<p align="center"><img src="assets/icon.svg" width="92" alt="Research PPT SOP 图标"></p>
<h1 align="center">Research PPT SOP · 科研汇报制作技能</h1>
<p align="center">沿参考组织论证，把证据与机制做成可编辑的完整汇报。</p>
<p align="center"><a href="README.md">English</a> · <a href="SKILL.md">技能入口</a> · <a href="references/migration.md">平台使用</a> · <a href="LICENSE">MIT 许可</a></p>

<img src="assets/banner.svg" width="100%" alt="参考、证据与可编辑汇报">

## 能完成什么

输入已有主稿、证据与参考PDF/PPTX，按一套可复用流程组织完整科研汇报。图形要解释计算，结论要对应证据；制作过程不进入面向听众的正文。

- **参考驱动：**学习整页构图、局部强调、框体层级、语义箭头和阅读路径，不只换蓝白配色。
- **证据分清：**已有待排、身份待核、尚缺研究分别处理，不为填图自动开实验。
- **机制讲透：**输入输出、内部计算与作用位置、训练推理、设计理由和直接对照。
- **完整成品：**封面、目录、正文、备查、备注与导航/页码引用联动，不停在提纲或单页。
- **面向听众：**清理制作话术，保留正式来源、必要条件、未验证范围与完整负结果。
- **分层验收：**文件结构、内容、设计预览与真实Office显示分别报告。

核心说明和模板为简体中文；六个通用检查/构建脚本不依赖中文环境。

## 使用流程

主稿与证据 → 参考拆解 → 论证与页计划 → 机制与图证 → 完整可编辑稿 → 成品表达与文件检查 → 交付及遗留。

1. 下载仓库，或在[Releases](https://github.com/Scared11a/research-ppt-sop/releases)取得`.skill`包。
2. 按当前平台支持的方式加载完整目录，不只复制SKILL.md。
3. 提供主稿、证据、参考与允许输出的位置，调用：

> 按research-ppt-sop制作完整可编辑汇报。保留参考的视觉语言，讲清机制，并审阅所有面向听众的文字。

[输入模板](assets/job-contract.json)、[图证台账](assets/evidence-ledger.csv)、[封面目录契约](assets/frontmatter-contract.json)和[成品审阅表](assets/audience-review.csv)已随包提供。查不到的关键事实保留缺口，不凭模板补造。

## 平台入口

| 平台 | 怎么使用 | 不能默认什么 |
|---|---|---|
| Hana | 通过正式技能安装入口导入`.skill`并确认，见[适配](references/platforms/hana.md) | 安装不等于实际加载或PPT效果验证。 |
| DeepSeek Harness / DSHana | 由有效profile的技能根发现，或由委派者明确提供规则，见[适配](references/platforms/dsh.md) | 默认委派preset没有shell和skill自动发现。 |
| Codex | 完整目录放到适用`.agents/skills/research-ppt-sop`，用`$research-ppt-sop`调用，见[适配](references/platforms/codex.md) | 不自带Hana工具、字体、Office渲染或桌面操控。 |

三者共用一个核心。适配只映射能力，不扩大权限；跨平台PPT制作尚未端到端验证。

## 环境与安全预检

- Python 3.10+；PPTX对象与关系检查只用标准库。
- PDF测量/原像预览按需使用pdfplumber及PDFium。
- scene制作需要Node.js和明确Node项目内的PptxGenJS；既有流程使用4.0.1。
- 字体、文档读取和渲染能力由当前环境提供；随包字体探针仅支持macOS。

不自动安装依赖，不捆绑字体、Office引擎、模型或node_modules。

```bash
SKILL_DIR="/absolute/path/to/research-ppt-sop"
NODE_PROJECT="/absolute/path/to/existing-node-project"
python3 "$SKILL_DIR/scripts/preflight.py" --node-project "$NODE_PROJECT"
python3 "$SKILL_DIR/scripts/audit_pptx.py" /absolute/path/to/existing.pptx
```

预检只证明找到所列依赖。生成新PPT的命令及权限条件见[工具接口](references/tools-and-interfaces.md)。

## 内容导航

- [SKILL.md](SKILL.md)：完整执行入口。
- [平台契约](references/platform-contract.md)：资源、工具、权限与交付映射。
- [封面目录](references/cover-and-navigation.md)：整页层级、实际章节、页码与导航。
- [机制图证](references/figures-and-evidence.md)：计算关系、编辑层和对照身份。
- [成品表达](references/audience-content.md)：正文、图内字、页脚、备注共同审阅。
- [验收与恢复](references/acceptance-and-recovery.md)：检查、异常处理与停止条件。
- [MANIFEST.md](MANIFEST.md)：文件和模板清单。

## 检查与边界

```bash
python3 -m unittest discover -s tests -v
node --check scripts/build_deck.mjs
```

这些检查不生成PPT。结构通过不代表科学、视觉或GUI编辑通过；同源设计预览也不是从最终PPTX导出的Office渲染。任意SVG恢复、原生Office公式、连接器吸附与所有平台效果均无保证，详见[验证范围](references/provenance-and-validation.md)。

公开包不含私人参考稿、会话日志、未发表研究或实验数据；示例不代表科研结果。

## 贡献与许可

欢迎带最小非敏感示例的问题报告和聚焦的PR，说明平台/版本、失败能力和实际检查范围。不要上传密钥、私人PPT、未发表论文或研究数据。

[MIT](LICENSE)。图标和横幅为原创；运行依赖保留各自许可。文档组织参考与第三方说明见[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
