# 第二阶段编排用例交接
2026-11-05 新增 workflow-cases.v1.json（4例公共Case格式），test_workflow_cases.py。未改冻结的8例、scorer或公共代码。

来源：integrations/yanxu/WORKFLOW-CONTRACT.md、workflow_adapter.mjs/.py，以及 E:/AI/codex/writing-site/src/workflow.mjs 的 executeWorkflow。真实编排执行，search为合成记录，model/legacy被拒绝，内存项目无外部副作用。input严格只含operation；scorer默认保留NEEDS_REVIEW，不向固定输入塞附加元数据。

4例实际输出顶层断言：
- references：completed、error_code=null、search_calls=1、model_calls=0。
- missing_material：rejected、workflow.requirements、search_calls=0、model_calls=0。
- resume_parameters_changed：rejected、workflow.parameters_changed、search_calls=1、model_calls=0。
- resume_input_changed：rejected、workflow.input_changed、search_calls=1、model_calls=0。

各例还检查scenario；不使用目标自报checks布尔值作为预期。人工复核全部保留。引用例为合成非空结果，仅证明编排状态，不能称零命中边界或引用真实性已验证；恢复拒绝例证明第二次搜索未发生，不证明完成任务正常恢复的幂等性或外部副作用可撤销。

运行 python -m unittest discover -s benchmarks/yanxu -p "test*.py" -v，5项测试全部通过（含4工作流场景真实执行、各顶层字段逐一错误注入）。最初运行因input附加元数据违反固定适配器契约失败，已将新数据input收窄为operation后通过，无修改适配器。

14个广义业务契约仍按 COVERAGE.md 标待接。缺资料拒绝/恢复参数变化仅取得本次窄场景证据；取消、成功恢复、真实检索零命中、选题硬约束与未核验图谱未由本次4例完成。父会话负责adapter枚举、UI与门禁集成，不把5项本地unittest写成网站E2E通过。
