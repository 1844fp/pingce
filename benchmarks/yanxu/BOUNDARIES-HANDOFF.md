# 第4阶段边界用例
新增 boundaries-cases.v1.json，snapshot=yanxu-boundaries-v1；两例 input 仅operation。来源为 BOUNDARIES-CONTRACT.md、实际适配源码及真实返回；不检查自报checks。
topic_constraints：断言真实rejected列表、handoff_error、quality_status，覆盖方法/截止时间拒绝、不可用数据阻断、未知学科needs_scope。
runtime_cancel：真实handleAPI运行/取消，断言HTTP200、持久job cancelled、run interrupted、output_present=false、fetch_calls=1。提供方为门控合成响应，实际已发生一次调用；不代表外部动作撤销或真实模型能力。数据和状态仅内存。
两例均默认NEEDS_REVIEW。未改旧数据/scorer/业务源码。图谱无隔离确定夹具，仍待接。
首轮取消测试search not entered失败；服务适配器切到实际topic运行并增加固定合成认证标记后修复，最终暴露稳定顶层字段，不冻结随机ID/时间/events。
最终复验：读取最新BOUNDARIES-CONTRACT后执行 python -m unittest discover -s benchmarks/yanxu -p "test*.py" -v，7项全部通过（12.717秒）；新增2场景实际执行及各顶层字段错误注入，正确输出无FAIL并保留NEEDS_REVIEW。
