# 通用能力契约与平台选择

核心顺序、图证要求、脚本和验收不随平台改变。平台适配只决定如何取得输入、执行已授权脚本、查看成品和交付，不能扩大文件、网络、模型、实验或软件安装权限。

## 执行入口

1. 明确host为Hana、DSH或Codex，及实际工作目录/读写根/服务归属。
2. 填工作副本`assets/platform-contract.json`；每项能力标为`verified`、`declared_not_run`、`missing`或`not_required`，记录实际工具/命令和证据。
3. 按需读取[Hana适配](platforms/hana.md)、[DSH适配](platforms/dsh.md)或[Codex适配](platforms/codex.md)。DSH经Hana委派时两者都读。
4. 脚本命令保持相同。缺能力只暂停依赖它的步骤，继续不受影响的主稿组织、来源核对和设计；不把不同工具的同名参数视为等价。

## 能力与替代接口

| 能力 | 所需输入与返回 | Hana | DSH | Codex |
|---|---|---|---|---|
| 资源定位 | 文件身份→授权可读真实位置；保留来源/版本 | ResourceIO、SessionFile、materialize | 显式cwd内路径、获准共享资源；不认识Hana fileId | 本机/工作区真实路径、用户明确附件；不认识Hana fileId |
| 读写/检索 | 局部文本、精确编辑、新版本源 | read/edit/write/find/grep | 实际preset的fs工具；PTC走SDK绑定 | 当前会话实际文件/命令工具及审批；工具名动态核对 |
| 文档内容与原像 | PPTX/PDF正文、对象/备注、代表页图像 | 已有doc-intake/Office入口及随包拆解器 | 已启用office技能/工具或允许的本地脚本；缺则回报委派者 | 获准本地解析器/随包脚本、已配文档技能；不默认有Hana App |
| 命令执行 | 指定cwd、显式依赖、退出码和真实输出 | exec_command | 默认dshana/dshana-ptc无shell；由委派者执行或另有明确授权的适当preset | 当前沙箱允许的命令入口；CLI参数控制并不等于已审批 |
| Node/Python/字体 | preflight结果、显式Node项目、字体角色与实际可用性 | 随包preflight和mac字体探针 | 有shell时同命令，否则交给委派者 | 同命令；非mac字体探针另配，不能用成功退出替代字体证据 |
| 设计预览 | 源图/HTML到真实预览图/PDF | 已有host-unit HTML→PDF | 已启用工具或委派者生成 | 已有且获授权的本地/插件渲染器；缺则标未测 |
| 实际Office与交互 | 从最终PPTX渲染/修改，记录应用与动作 | 授权computer/专业引擎 | 无通用保证；通过获授权外部执行者 | 不默认内置Office渲染或桌面操控 |
| 文件交付 | 完整PPTX、源/预览、实际可取入口 | stage_files | present或返回路径给委派者，由其stage | 本机可取绝对路径/会话支持的工件附件；不伪造SessionFile链接 |

## 统一预检

`preflight.py`只发现Python/可选PDF依赖、Node及指定项目的pptxgenjs；不会启动DSH/Codex会话、验证模型身份、检查登录或修改配置。

```bash
python3 "$SKILL_DIR/scripts/preflight.py" --node-project "$NODE_PROJECT"
```

无shell时不假装执行。返回请求给有权限的执行者：命令、cwd、输入/输出、允许写入范围和停止条件。macOS `check_fonts.py`不适用于Windows/Linux；替代探针未核时明确缺口。文本声明的字体、系统登记、实际Office显示是不同证据。

## 权限与缺失处理

资源不在当前cwd、无法解析附件身份、缺依赖、缺渲染器或必须经审批时，停止对应动作。不要以重开会话、改preset、切平台、全权限参数、默认联网或复制敏感材料规避边界。平台适配文件只说明入口，不能取代用户批准和工具权限。

本次只核文档、源码、无推理CLI帮助与既有PPT；没有跨平台PPT实跑。安装了同名技能不等于模型实际加载，正式保存、发现/启用和端到端运行分开报告。
