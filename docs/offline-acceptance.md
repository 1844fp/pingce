# 第五阶段离线验收

用户于2026-11-05明确选择暂不调用模型，本轮不执行真实模型评测。

## 一键运行

启动start.ps1后：

```powershell
.venv/Scripts/python.exe scripts/run_offline.py --suite all --report reports/offline-acceptance.json
```

只连接本机HTTP平台，固定注册五种离线适配器，不选择HTTP外部目标，不自动人工批准。默认项目default，与工作台相同；可通过--project显式指定隔离项目。超时请求取消，不能撤回已发出动作。
退出码0表示全部门禁PASS；1表示执行完成但存在失败/待复核；2表示执行或连接错误。当前19项均保留人工判断，因此正确的批量验收退出码是1。

## 实际结果

五组19项均COMPLETED，确定性失败0；NEEDS_REVIEW分别8/4/2/2/3。报告保留每条冻结目标、源码与评分器哈希、真实模块输出、评分证据和轨迹。

新增知识范围：实际执行graph.build/Graph查询与trace_source，合成SQLite仅在项目work创建并清理，不打开生产知识库。导航关系保留unreviewed_navigation和navigation_not_fact_verified；定位到合成文档第7页；源变更后旧边过滤且追溯拒绝；零结果没有原文证据。MCP server文件仅哈希上下文，未启动该服务。不代表真实检索质量或论文语义支持已验证。

51项pytest通过（含解压响应限流和评分器哈希不可混比）；生产构建通过；browser_knowledge.py验证三例、报告下载、待复核门禁和移动端，无pageerror。图谱报告docs/knowledge-report.json，截图docs/knowledge-live.png。

## 仍未完成

完整真实文献与生成质量、所有知识权限路径和图谱语义关系均未核验；远程提供方取消、任意副作用幂等没有通用保证。PostgreSQL/对象存储/SSO/可信工具网关/跨租户生产部署未落地。它们需要确定目标环境与服务配置，不能把当前单用户离线版描述成生产系统。
