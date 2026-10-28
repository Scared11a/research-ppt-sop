# Codex适配

## 已核入口

核对日期2026-10-28。本机只执行`codex --version`、`codex --help`和`codex exec --help`，版本`codex-cli 0.151.0`；未启动推理、PPT任务、登录检查或配置写入。

OpenAI官方Build skills文档确认：Codex使用带name/description的SKILL.md目录；项目从cwd到repo root扫描`.agents/skills`，用户级为`$HOME/.agents/skills`，另有admin/system来源；同名技能不会自动合并。CLI/IDE可用`/skills`或`$research-ppt-sop`显式引用。支持相对references/scripts/assets，不要求Hana的.skill扩展名。

官方来源：https://developers.openai.com/codex/skills/ （当前返回ChatGPT Learn的Build skills，重定向入口：https://learn.chatgpt.com/docs/build-skills）。文档与本机版本分别作为证据，不以文档代表本机加载已经成功。

## 迁移与使用

只有另有安装目标和授权时，把完整research-ppt-sop目录放入项目`.agents/skills`或允许的用户级技能根；先查重，不覆盖同名包，不把Hana托管目录直接当可写Codex目录。跨平台迁移不附带私有参考/素材、字体或node_modules。

本次没有安装到Codex，也未改其config。未来显式调用示例：

```text
$research-ppt-sop 使用指定主稿、证据和参考，按核心SOP执行；选择Codex适配，先核当前工具、cwd和依赖。
```

加载后以当前会话工具表和项目规则为准；不假定存在Hana的read/ResourceIO/materialize/SessionFile/stage_files/doc-intake/host-unit。资源使用用户提供且当前沙箱可读的真实路径。缺输入附件需从原平台正式导出或授权共享，不能从显示名猜缓存位置。

## cwd、命令与权限

本机CLI帮助确认`-C/--cd`指定工作根，`-s/--sandbox`有read-only/workspace-write等模式，`--add-dir`是额外可写根；这些参数表达配置，不替代授权。不得使用绕过审批/沙箱的参数或通过切平台规避限制。

本任务不调用带prompt的codex/exec。未来由当前会话获授权命令工具执行随包脚本即可；若用户另外要求从CLI启动任务，先核所用版本帮助和审批策略，不照抄旧版本flag。

Python与PDF能力、明确Node项目的pptxgenjs用同一个preflight检查。执行build_deck时cwd必须是实际Node依赖项目，不把技能目录当node_modules来源。字体探针check_fonts只支持macOS；其他OS需已有获准探针/目标应用证据，未核不能承诺字体复现。

## 读取、预览与交付

PPTX结构和备注可用随包inspect/audit脚本；文本提取需当前已配置文档工具或已批准本地解析器，缺失时报告。CLI `-i/--image`接受图片附件，不等于本地有Office渲染/OCR能力；图片查看工具名由当前工具表核对。

设计HTML→PDF与最终PPTX的Office渲染分开。Codex不因能执行命令就默认拥有PowerPoint/WPS、LibreOffice、桌面控制或Hana Chromium工具。没有获授权渲染器时保留可执行的源/成品并注明未测，只暂停需要实际渲染的判断，不安装软件填缺口。

本机文件交付给出真实绝对路径，平台如支持工件/附件则用其正式接口；`-o/--output-last-message`只保存最后回复，不自动打包或发送PPT。交回Hana时由Hana登记/交付，不伪造fileId或下载链接。

## 未测项

Codex端skill安装/发现/自动触发、模型运行身份、PPT端到端制作、GUI编辑与Office显示未测试。官方入口和CLI帮助已核，不等于跨平台流程已跑通。
