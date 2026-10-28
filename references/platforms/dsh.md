# DSH / DeepSeek Harness适配

先区分独立DSH与Hana的DSHana托管App。两者不能共用未经核对的home、模型、工具或preset假设。

## 当前可核依据

核对日期2026-10-28。已安装DSHana manifest为`1.2.1+dsh-0.2.1-rc.2`，所带`@deepseek-ai/dsh`为`0.2.1-rc.2`；以下基于其正式dshana技能、参数/preset/setup说明及skill-filesystem源码，未启动任务验证。

## 独立DSH的技能入口

当前已装skill-filesystem实现可扫描项目根`.dsh/skills`、`.agents/skills`、配置的customSkillDirs，以及有效dshHome/agentsHome下的skills。目录包含SKILL.md与相对资源；有效项目根、home、provider是否启用由实际profile决定，不能写死为用户`~/.dsh`。

迁移时只在明确目标/权限后把完整包放到有效扫描根，检查技能列表/实际读取结果。若preset没有skill-filesystem/tool-skill，即使文件存在也不会自动提供技能；须由委派者显式提供本技能核心和所需适配章节。当前未安装本技能到独立DSH profile，也未验证其发现行为。

## Hana经DSHana委派

正式工具通过Hana catalog发现`dshana`，不是shell里运行一个猜测的命令。调用前读App自身SKILL和`references/parameters.md`，因为oneOf参数不会在简化工具摘要完整展开。

工单必须包含：
- 第一任务task和已存在绝对cwd；共享素材/源/输出与单一写入者；
- 本技能核心、与任务相关的封面/正文/验收规则，或确实可读的完整包路径；
- 实际工具能力、依赖、模型/数据使用边界、交付和停止条件。

文档接口示意（只有另获委派授权时才调用，本次不执行）：`open`需要task/cwd，`reply`用当前taskId续接并提供task；模型覆盖必须provider/model成对，reasoningEffort按host可用档位。记录请求配置和实际可观察身份，不能混称。

## preset决定执行能力

- `dshana` / `dshana-ptc`保留文件/检索、todo、present等，移除了shell、web、skill-filesystem/tool-skill及递归委派；不能凭它运行Node/Python构建、安装或自行读入skill。
- `dshana-ptc`通过生成SDK的工具绑定访问文件；raw node:fs不是绕过文件边界的通道。
- 确有shell需求时，应交给Hana委派者执行，或在另有明确授权且核过能力后选择合适preset。不能为完成本SOP自动切preset或提高权限。
- 新建前需要时查正式presets roster，不猜名称。get只读结果需要runtime已在线；没有任务时不为验能力启动会话。

## 依赖、路径和交付

App内携带DSH运行依赖，不代表任务Node项目含pptxgenjs，也不代表预设可执行shell。Python/PDF/字体和Node项目按能力契约单独预检；无shell就回报由委派者执行具体命令。

cwd内路径与Hana SessionFile不同；委派者先解析并确认共享权限。工作目录外写入按实际沙箱审批，不把sessionId跨会话凭据当成扩权办法。App托管DSH使用App私有数据目录，不手改用户`~/.dsh`或App底层配置。

present若可用可呈现文件，但Hana最终仍由主助手stage_files交付。独立DSH交付使用其当前工件能力；精确入口未核时返回真实路径和缺口，不声称已发送附件。

## 待核项

有效profile是否开启skill provider、实际preset工具列表、当前模型身份、独立DSH安装/加载入口、真实Office渲染与GUI编辑均未做运行验证。能力不足只暂停相应步骤，不触发安装、模型评测或PPT试做。
