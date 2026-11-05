# 研序业务评测交接

## 当前交付边界（2026-11-05）
正式可执行数据为 `module-cases.v1.json` 的8个合成用例。它们通过 `integrations.yanxu.adapter.execute` 调用业务 `writing-evidence.mjs` 的真实 audit/repair 纯函数，无模型调用。来源为本地源码契约，预期按契约手工定义；不从目标输出生成预期。

`cases.v1.json` 与 `import.v1.json` 的14个用例是待实现业务契约，覆盖面更广，但 instruction 输入不能直接交给现有仅支持 audit/repair 的适配器。不得把它们作为已跑通的业务闭环导入发布。`module-import.v1.json` 是早期两例最小样本，最终验收使用8例文件。

评分入口 `benchmarks.yanxu.scorer.evaluate(case, execution)` 及协议见 CONTRACT.md。此次收尾没有修改评分器或任何数据集，冻结版本保持原样。

## 实际验证
2026-11-05 从本目录测试发现入口执行：

```powershell
python -m unittest discover -s benchmarks/yanxu -p "test*.py" -v
```

在评测项目根目录运行，4项 unittest 全部通过。包含14例评分器结构与错误变体检查，以及8例真实适配器 correct/regression 两模式执行。

正确模式8例无 FAIL，8例保留 NEEDS_REVIEW。显式回归注入模式7例 FAIL（5个非空问题列表审计例、2个 repair 例）；正常空 issues 例不误报。回归模式是测试故障注入，不是业务真实退化。audit 同时检查 status、issues 精确结构和 affectedLocations；repair 比较 paragraphs 只验证编辑范围和标记，不衡量写作质量。

## 集成状态与责任
父会话报告公共 Case 路由、Worker 评分、人工复核、门禁与回归集已接通，21项 pytest 通过，浏览器验收进行中。这是父会话报告，不是本会话独立复验；最终平台验收以父会话记录为准。本会话负责的数据与评分器证据仅为上述4项 unittest 及离线模块运行。

所有8例仍需人工复核来源支持、语义完整性与表达。PASS 为结构检查通过；FAIL 或 NEEDS_REVIEW 不应自动放行门禁。目标 actions 自报不能证明无外部副作用；独立可信审计仍需后续建设。

## 来源与协作
读取 E:/AI/codex/AGENTS.md、agent-team/CURRENT-STATUS.md、registry.json、skills/role-skill-routing.json，并采用本地 yanxu-agent-skill-router。业务自身 AGENTS.md/agent-team 不存在，使用上级权威入口。只读检查业务源码和已有测试，不把夹具文献当真实研究证据。详细边界见 COVERAGE.md。

未调用收费模型、读取密钥、上传论文、发布或重启网站；未修改业务源码、数据中台、公共 API 或前端。复用现有模块、目标协议和Python标准库，无新增依赖。
