# 本机版交付状态

按用户确认：本机运行、不接组织SSO、不调用模型。完整实施与验收已完成，72项测试通过。使用、报告归档、审计和整包恢复见 [本机版完成验收](docs/local-completion.md)。

# 衡尺：数据与多智能体评测中台

最新进度、证据和未完成范围统一见 [当前状态](docs/current-status.md)。页面已有五组共19项评测范围，包含图谱来源边界。当前72项测试通过，真实模型生成和生产化仍未完成。

本地可运行的第一阶段全栈 MVP：React + TypeScript、FastAPI、SQLite 持久化队列、独立 Python Worker。

当前优先服务 **AI 写作助手**，暂缓数据中台接入。写作离线模块评测、人工复核、门禁、报告和失败回归已接通；操作和证据见 [写作验收](docs/writing-acceptance.md)。现有经营数据示例仍为历史 fixture。完整模型生成和网站全旅程尚未验收。

## 当前交付

- JSON 导入与不可变数据集版本，固定快照标识。
- 可控 fixture 与 HTTP 被测服务版本注册。
- 幂等创建实验，参数冲突检测，调用次数预算。
- 独立 Worker、执行状态、取消、超时和中断恢复。
- 精确匹配和禁止动作两个确定性评分器；证据、目标产物和轨迹保存。
- 逐样本结果、相同数据集的基线对比、保守门禁。
- 中文响应式管理界面、自动生成的 API 文档。

**这不是生产部署版本。** 当前没有 SSO，X-Project 是归属筛选，不是认证或租户安全边界。服务默认只监听 127.0.0.1。

## 本机启动

本次会话已安装依赖并构建前端。在本目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

打开 http://127.0.0.1:8765 。按 Ctrl+C 停止 API 和 Worker。
不要针对同一个数据库同时启动多份 run.py / Worker。

## 新环境安装

需要 Python 3.11+ 和 Node.js 20.19+。

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
Set-Location apps/web
npm.cmd ci
npm.cmd run build
Set-Location ../..
.venv/Scripts/python.exe run.py
```

数据库首次启动自动建表，默认 evaluation.db。可设置 EVAL_DB 指定路径。
测试：`.venv/Scripts/python.exe -m pytest -q`。
本会话也可以使用 `../../work/venv/Scripts/python.exe`。

## 五分钟验收

推荐在默认“写作验收”页点击“准备写作评测”→“运行真实模块基线”→查看8条待复核结果→“注入回归并验证”→查看7条失败→导出报告或转回归集。需本机已有 E:/AI/codex/writing-site 及 Node；适配器仅允许固定的 audit/repair 模块。源文件变化将拒绝旧目标，应重新准备版本。

以下为历史通用平台 fixture 验收：

1. 数据集版本：发布预填的三个样本；标识为可控测试数据。
2. 被测服务：注册 fixture / correct，版本 v1。
3. 实验工作台：选择数据集和目标，创建基线实验，应 3/3 通过。
4. 被测服务：注册 fixture / regression，版本 v2。
5. 使用**相同数据集版本**创建候选实验，应 2/3 通过。
6. 版本对比：选择两个实验，edge 样本从 PASS 变为 FAIL，下降约 33.3 个百分点。
7. 展开运行详情查看实际值、参考值、动作检查和目标响应。

fixture 读取参考答案来测试平台链路，不用于评价真实 Agent；退化与超时也是显式模拟行为。

## 接入真实测试服务

在启动 API 和 Worker 前设置 `$env:EVAL_ALLOWED_HOSTS='127.0.0.1,test-agent.internal'`，仅允许可信测试服务；不要添加生产写服务或元数据服务。没有设置则不接受任何 HTTP 目标。

适配器发送：

```json
{"input":"业务问题","context":{"snapshot":"固定快照","case_id":"case-1"}}
```

目标返回：

```json
{"output":{"profit":30000,"unit":"CNY"},"actions":["read_data"],"trace":[{"name":"query","status":"OK"}],"usage":{"cost":0.01,"currency":"USD"}}
```

业务服务需要负责将 snapshot 映射到真实快照，以及测试身份、数据权限、凭证和工具隔离。平台不向被测目标发送参考答案。无自动 HTTP 重试，超时后服务端仍可能在执行。
当前 exact_match 是 JSON 值精确相等，不是 SQL 结果语义评测。
禁止动作依赖目标声明，尚未接入独立可信工具审计；不能据此证明没有越权。

## 后续生产化清单

见 docs/roadmap.md。真实数据中台未提供，因此暂未连接任何生产系统。模型评审、人工标注、OTel Collector、对象存储、CI/CD 集成和费用硬预算尚未实现。

## 永久保存位置与第二阶段
唯一项目根目录为 E:/Codex/评测中台；使用本目录 .venv 与 start.ps1。工作流4例及CLI门禁说明见 MIGRATION.md，子会话均应使用本根目录。


可选服务令牌、数据库迁移、容器与PostgreSQL准备的实际验证范围见 [运行准备](docs/runtime-preparation.md)。Docker/PostgreSQL尚未运行验收，当前仍为本地SQLite。
