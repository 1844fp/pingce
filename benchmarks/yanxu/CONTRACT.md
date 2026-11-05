# yanxu-writing-v1
入口：`benchmarks.yanxu.scorer.evaluate(case, execution) -> list[dict]`，纯函数，无网络、密钥或模型依赖。
case 使用公共 Case 字段并新增 `evaluation: yanxu-writing-v1`、`checks: [{field, equals}]`。`input.needs_review` 控制是否附加写作人工复核项（默认 true）；来源和风险在 input.provenance / input.risk_tags。完整可导入文件 import.v1.json 含14例。
execution 使用平台目标协议 `{output: object, actions: string[], trace: [], usage: {}}`。output 为适配器提取的结构化事实，不要求生成文本相等。检查只比较声明的单字段不变量，类型严格；字段缺失 FAIL，空 checks NEEDS_REVIEW，actions 缺失 NEEDS_REVIEW。返回 metric/status/value/reason/evidence/version；人工复核 value=null。FAIL 和 NEEDS_REVIEW 都不能自动通过门禁。
适配器应从实际模块返回、前后章节差异、调用计数、引用差异和持久化任务状态提取 output；不能直接复制 expected。本模块不读取 expected 评分，只读 checks。actions 为目标声明，不能证明无外部副作用；独立工具审计尚待接入。
现有平台若未合并 evaluation/checks 支持，请勿按默认 exact 运行此文件；旧评分只能演示结构化字段一致性，不能验收写作质量。
实际模块执行建议：写作 auditRewrite 与原文保护检查；topic-contract/topic-quality 硬约束；integrity-tools 来源覆盖；graph-engine 未审核边界；runtime/workbench 取消恢复。此会话未改共享适配器，也未执行这些模块。适配器负责人应逐例建立映射；无法可靠提取时不要填猜测值，应保留缺失使评分失败/复核。
真实模块即跑数据：module-import.v1.json；python benchmarks/yanxu/verify_modules.py。主 import.v1.json 为14项业务契约设计，需要逐例适配，不可直接交给只支持 audit/repair 的适配器。两份数据必须区分导入。
最终建议导入 module-cases.v1.json（8例），verify_modules.py 已切换此文件。返回全部保留人工复核。
