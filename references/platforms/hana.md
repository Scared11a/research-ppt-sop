# Hana适配

适用于Hana主会话与Hana负责执行/交付的协作。核心规则和命令见上级文档，不改流程。

## 入口与资料

- Skill通过正式extension_manager/skill资源入口读取与保存；已安装包不直接改底层文件。工作区副本更新、验证后走正式安装/更新确认。
- SessionFile是身份，不是可猜的缓存路径。需要shell路径时先materialize；新文件优先按返回fileId交付。
- 文本和源码走read/grep/find/edit/write；文档正文优先已有doc-intake/office-documents。先查已有提取/预览，敏感文件保持本地或获准隐私通道。
- Obsidian等受控资料遵守其独立入口与导出限制，可读不代表能复制到制作目录、DSH/Codex或外部服务。

## 执行和预览

Hana的exec_command负责已授权脚本，workdir设为明确Node项目或任务目录。随包六脚本保持原接口；实际依赖由preflight核对。

同源HTML→PDF当前已核`host-unit/office_html-to-pdf`；它不是PPTX实际渲染。真实Office显示按获准computer/专业引擎执行；`office_render_preview`只收DOCX的现状不能推作PPT能力。

## 委派与交付

委派DSH前把共享输入解析为允许访问的路径，并提供最小必要核心章节/适配说明；不假定其继承Hana会话或skill清单。按[DSH适配](dsh.md)核对preset，默认dshana系列没有shell/skill发现。

最终stage_files交付完整文件，记录设计预览来源和未测范围。安装回执`installed`、host/agent启用、正文可读，只证明相应状态，不证明热刷新或PPT端到端效果。

## 已核与空白

安装后用正式管理工具确认技能状态及当前Agent启用，再回读包内容。已有工作流的运行经验不能代替你的目标环境验证；工具名变化时先查正式帮助，不换底层通道。
