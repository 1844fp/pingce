# 第5阶段知识边界
新增knowledge-cases.v1.json（snapshot yanxu-knowledge-v1）和独立test_knowledge_cases.py。来源：integrations/yanxu/KNOWLEDGE-CONTRACT.md、knowledge_adapter.py及实际执行。真实graph.build/Graph.graph_lookup/trace_source，输入仅固定operation，最小合成SQLite在项目work内创建并清理，不打开真实知识库或论文、不联网、不调用模型。
3例：navigation_trace检查1条边、unreviewed_navigation、navigation_not_fact_verified、合成doc_id/第7页/精确原文trace与普通检索fallback；stale_source检查零边、来源变化拒绝trace及source_unchanged=false（只变更合成源）；empty_lookup检查零边及空trace，不推断不存在真实文献。
全部使用实际顶层字段，不使用调试自报。trace原文相等仅验证定位与来源片段传递，不是写作质量或研究证据。均默认NEEDS_REVIEW，不把规则关系当事实/因果认证。source_unchanged检查合成源文件，不证明生产库安全。
未改旧数据/scorer或业务源码。同步图操作无强制取消；manifest前后比较不等于不可变运行时快照。父会话负责API/UI集成。
2026-11-05 实际执行 python -m unittest discover -s benchmarks/yanxu -p "test*.py" -v：8项全部通过（12.916秒）。新增3场景真实图操作均无FAIL且保留NEEDS_REVIEW；逐一篡改每个断言字段均检出FAIL，modelCalls均为0。
