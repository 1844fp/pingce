# 生命周期用例交接
来源 integrations/yanxu/LIFECYCLE-CONTRACT.md 和实际适配器源码。新增2例 references_empty/resume_success，真实 executeWorkflow 编排配合合成搜索/内存持久快照。顶层检查scenario、interrupted、first_error、resume_error、search_calls、model_calls、records_count、run_status、stage_status；不依赖目标自报checks，不锁定内部save次数。所有结果默认保留NEEDS_REVIEW。
零命中仍needs_review；恢复场景在已保存searchResult后注入持久化异常，再从内存快照恢复，搜索总次数为1。不能推断真实网络搜索质量、进程崩溃持久性或任意任务幂等性。无取消场景，取消仍待接。旧8例/4例/scorer保持冻结。
2026-11-05 实际运行 python -m unittest discover -s benchmarks/yanxu -p "test*.py" -v，6项全部通过。新增测试真实执行2场景并逐字段注入错误确认FAIL；正确输出零FAIL且保留NEEDS_REVIEW。初次默认沙箱写新文件PermissionError，经针对已授权目录的提升执行写入成功，未使用旧目录。
