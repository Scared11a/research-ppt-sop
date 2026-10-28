# 平台加载与更新

## 包结构

完整目录包含SKILL.md、references、assets、scripts，以及公开说明/许可和图标。不要只复制入口文件。核心顺序和六个脚本方法保持一致，平台适配不改制作路线。

## 已有任务接续

- 不强制搬迁工程，沿既有工作目录、事实源与完整稿入口。
- 用job-contract指向platform-contract、frontmatter-contract及audience-review工作副本；未知项保留null，不把模板当确认。
- page-plan按列名追加章节、导航和审阅字段，不重写证据数据。
- 收到纠正应修实际成品并回读；更新技能本身不代表旧PPT已经修复。

## Hana

通过当前平台支持的技能导入/仓库安装入口加载包，完成应用确认，再核正式安装目录、启用和内容回读。更新先保留工作源/旧版本，走正式管理入口，不直接写托管底层目录。不能把安装成功写成已热刷新或端到端通过。

## DeepSeek Harness / DSHana

先读[DSH适配](platforms/dsh.md)。独立DSH要核有效profile的skill provider与扫描根。DSHana默认委派preset缺少shell/自动skill发现，需委派者提供必要规则并承担构建，不自动切preset补权。

## Codex

先读[Codex适配](platforms/codex.md)。经目标与权限确认后，将完整目录放到适用`.agents/skills/research-ppt-sop`，查重后用`$research-ppt-sop`显式调用并核发现情况。当前包不代为修改Codex配置或安装任何依赖。

## 更新与验证

保留旧源和变更记录，按当前平台的正式方式替换；同名技能不一定自动合并。运行包检查、检查引用与输入契约，再针对变动验证实际能力。不要为了更新技能自动制作PPT、运行付费模型或安装软件。

跨平台输入和脚本组织相同，但权限、附件、字体和渲染不同。报告已核入口、缺口与未测范围，不说“复制即可跑通”。
